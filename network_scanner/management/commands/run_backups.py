from django.core.management.base import BaseCommand
from network_scanner.backup_service import backup_service
from network_scanner.models import BackupConfig


class Command(BaseCommand):
    help = 'Run scheduled backups'

    def add_arguments(self, parser):
        parser.add_argument(
            '--config',
            type=str,
            help='Run backup for specific configuration name'
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force backup even if not due'
        )

    def handle(self, *args, **options):
        if options['config']:
            try:
                config = BackupConfig.objects.get(name=options['config'])
                if not config.enabled and not options['force']:
                    self.stdout.write(
                        self.style.WARNING(f'Configuration {config.name} is disabled')
                    )
                    return
                
                self.stdout.write(f'Running backup for {config.name}...')
                backup_history = backup_service.run_backup(config)
                self.stdout.write(
                    self.style.SUCCESS(f'Backup completed: {backup_history}')
                )
            except BackupConfig.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(f'Configuration {options["config"]} not found')
                )
        else:
            self.stdout.write('Running scheduled backups...')
            backup_service.run_scheduled_backups()
            self.stdout.write(
                self.style.SUCCESS('Scheduled backups completed')
            )
