from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

import csv
import json
from pathlib import Path
from typing import Dict, Any, Iterable, Tuple

from ...models import Device


DEVICE_TYPE_ALIASES: Dict[str, str] = {
    # Check Point Firewall
    "checkpoint": "firewall",
    "check point": "firewall",
    "cp": "firewall",
    "check point firewall": "firewall",
    "checkpoint firewall": "firewall",
    # F5 BIG-IP
    "f5": "f5",
    "bigip": "f5",
    "big-ip": "f5",
    "f5 bigip": "f5",
    "f5 big-ip": "f5",
    "f5 load balancer": "f5",
    # Infoblox
    "infoblox": "infoblox",
    "nios": "infoblox",
    # Common network
    "switch": "switch",
    "router": "router",
    "other": "other",
}


def normalize_device_type(value: str) -> str:
    if not value:
        return "other"
    value_lower = value.strip().lower()
    # direct match against canonical choices
    canonical = {c[0] for c in Device.DEVICE_TYPE_CHOICES}
    if value_lower in canonical:
        return value_lower
    # alias map
    return DEVICE_TYPE_ALIASES.get(value_lower, "other")


def iter_csv(path: Path) -> Iterable[Dict[str, Any]]:
    with path.open(newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        for row in reader:
            yield {
                "ip_address": (row.get("ip") or row.get("ip_address") or "").strip(),
                "hostname": (row.get("hostname") or "").strip(),
                "device_type": (row.get("device_type") or row.get("type") or "").strip(),
                "status": (row.get("status") or "").strip() or "offline",
                "description": (row.get("description") or row.get("desc") or "").strip(),
            }


def iter_json(path: Path) -> Iterable[Dict[str, Any]]:
    with path.open(encoding="utf-8") as fh:
        data = json.load(fh)
    if isinstance(data, dict) and "devices" in data:
        items = data["devices"]
    else:
        items = data
    if not isinstance(items, list):
        raise CommandError("JSON must be a list of devices or object with 'devices' array")
    for row in items:
        yield {
            "ip_address": str(row.get("ip") or row.get("ip_address") or "").strip(),
            "hostname": str(row.get("hostname") or "").strip(),
            "device_type": str(row.get("device_type") or row.get("type") or "").strip(),
            "status": (str(row.get("status")) or "offline").strip(),
            "description": str(row.get("description") or row.get("desc") or "").strip(),
        }


class Command(BaseCommand):
    help = (
        "Import devices from CSV or JSON. "
        "Columns/keys: ip (or ip_address), hostname, device_type/type, status, description."
    )

    def add_arguments(self, parser):
        parser.add_argument("file", type=str, help="Path to CSV or JSON file")
        parser.add_argument(
            "--format",
            choices=["csv", "json"],
            default=None,
            help="File format (auto-detected by extension if omitted)",
        )
        parser.add_argument(
            "--update",
            action="store_true",
            help="Update existing devices (matched by IP address) instead of skipping",
        )

    def handle(self, *args, **options):
        file_path = Path(options["file"]).expanduser().resolve()
        if not file_path.exists():
            raise CommandError(f"File not found: {file_path}")

        fmt = options["format"]
        if fmt is None:
            suf = file_path.suffix.lower()
            if suf == ".csv":
                fmt = "csv"
            elif suf == ".json":
                fmt = "json"
            else:
                raise CommandError("Unable to detect format. Use --format csv|json")

        iterator = iter_csv(file_path) if fmt == "csv" else iter_json(file_path)

        created = 0
        updated = 0
        skipped = 0
        errors: list[Tuple[str, str]] = []

        with transaction.atomic():
            for idx, item in enumerate(iterator, start=1):
                ip = item.get("ip_address", "").strip()
                if not ip:
                    skipped += 1
                    errors.append((f"row {idx}", "Missing ip/ip_address"))
                    continue

                hostname = item.get("hostname", "").strip()
                device_type = normalize_device_type(item.get("device_type", ""))
                status = (item.get("status") or "offline").strip().lower()
                description = item.get("description", "").strip()

                obj = Device.objects.filter(ip_address=ip).first()
                if obj:
                    if options["update"]:
                        obj.hostname = hostname or obj.hostname
                        obj.device_type = device_type or obj.device_type
                        obj.status = status or obj.status
                        if description:
                            obj.description = description
                        obj.save()
                        updated += 1
                    else:
                        skipped += 1
                else:
                    Device.objects.create(
                        ip_address=ip,
                        hostname=hostname,
                        device_type=device_type,
                        status=status,
                        description=description,
                    )
                    created += 1

        self.stdout.write(self.style.SUCCESS(
            f"Import finished: created={created}, updated={updated}, skipped={skipped}"
        ))
        if errors:
            for where, msg in errors[:10]:
                self.stdout.write(self.style.WARNING(f"Skipped {where}: {msg}"))
            if len(errors) > 10:
                self.stdout.write(self.style.WARNING(f"... and {len(errors)-10} more"))


