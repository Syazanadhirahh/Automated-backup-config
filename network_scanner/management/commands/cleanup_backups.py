from django.core.management.base import BaseCommand
from django.utils import timezone
from network_scanner.models import BackupConfig, BackupHistory, BackupArchive
from network_scanner.backup_service import backup_service


class Command(BaseCommand):
    help = 'Clean up old backups and archive them based on retention policy'

    def add_arguments(self, parser):
        parser.add_argument(
            '--config',
            type=str,
            help='Specific backup configuration name to clean up (optional)',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be done without actually doing it',
        )
        parser.add_argument(
            '--force-archive',
            action='store_true',
            help='Force archiving even if retention period has not been reached',
        )

    def handle(self, *args, **options):
        config_name = options.get('config')
        dry_run = options.get('dry_run', False)
        force_archive = options.get('force_archive', False)

        if config_name:
            try:
                config = BackupConfig.objects.get(name=config_name)
                configs = [config]
            except BackupConfig.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(f'Backup configuration "{config_name}" not found')
                )
                return
        else:
            configs = BackupConfig.objects.all()

        if not configs:
            self.stdout.write(
                self.style.WARNING('No backup configurations found')
            )
            return

        total_archived = 0
        total_deleted = 0

        for config in configs:
            self.stdout.write(f'\nProcessing backup configuration: {config.name}')
            
            if dry_run:
                self.stdout.write('  [DRY RUN] - No changes will be made')
            
            # Calculate cutoff date
            if force_archive:
                cutoff_date = timezone.now() - timezone.timedelta(days=1)  # Archive everything older than 1 day
            else:
                cutoff_date = timezone.now() - timezone.timedelta(days=config.retention_months * 30)
            
            self.stdout.write(f'  Retention period: {config.retention_months} months')
            self.stdout.write(f'  Cutoff date: {cutoff_date.strftime("%Y-%m-%d %H:%M:%S")}')
            
            # Find old backups
            old_backups = BackupHistory.objects.filter(
                config=config,
                status='completed',
                completed_at__lt=cutoff_date
            ).order_by('completed_at')
            
            old_count = old_backups.count()
            self.stdout.write(f'  Found {old_count} old backups to process')
            
            if old_count == 0:
                self.stdout.write('  No old backups to process')
                continue
            
            if config.archive_old_backups:
                self.stdout.write('  Archiving old backups...')
                
                if not dry_run:
                    try:
                        backup_service._archive_old_backups(config, old_backups)
                        total_archived += old_count
                        self.stdout.write(
                            self.style.SUCCESS(f'  ✓ Archived {old_count} backups')
                        )
                    except Exception as e:
                        self.stdout.write(
                            self.style.ERROR(f'  ✗ Error archiving backups: {e}')
                        )
                else:
                    self.stdout.write(f'  [DRY RUN] Would archive {old_count} backups')
            else:
                self.stdout.write('  Deleting old backups (archiving disabled)...')
                
                if not dry_run:
                    try:
                        for backup in old_backups:
                            if backup.file_path:
                                from pathlib import Path
                                backup_file = Path(backup.file_path)
                                if backup_file.exists():
                                    backup_file.unlink()
                            backup.delete()
                        
                        total_deleted += old_count
                        self.stdout.write(
                            self.style.SUCCESS(f'  ✓ Deleted {old_count} backups')
                        )
                    except Exception as e:
                        self.stdout.write(
                            self.style.ERROR(f'  ✗ Error deleting backups: {e}')
                        )
                else:
                    self.stdout.write(f'  [DRY RUN] Would delete {old_count} backups')
            
            # Also clean up recent backups based on max_backups count
            recent_backups = BackupHistory.objects.filter(
                config=config,
                status='completed',
                completed_at__gte=cutoff_date
            ).order_by('-completed_at')
            
            recent_count = recent_backups.count()
            if recent_count > config.max_backups:
                excess_count = recent_count - config.max_backups
                self.stdout.write(f'  Found {excess_count} excess recent backups to clean up')
                
                if not dry_run:
                    try:
                        for backup in recent_backups[config.max_backups:]:
                            if backup.file_path:
                                from pathlib import Path
                                backup_file = Path(backup.file_path)
                                if backup_file.exists():
                                    backup_file.unlink()
                            backup.delete()
                        
                        self.stdout.write(
                            self.style.SUCCESS(f'  ✓ Cleaned up {excess_count} excess recent backups')
                        )
                    except Exception as e:
                        self.stdout.write(
                            self.style.ERROR(f'  ✗ Error cleaning up excess backups: {e}')
                        )
                else:
                    self.stdout.write(f'  [DRY RUN] Would clean up {excess_count} excess recent backups')

        # Summary
        self.stdout.write('\n' + '='*50)
        self.stdout.write('CLEANUP SUMMARY')
        self.stdout.write('='*50)
        
        if dry_run:
            self.stdout.write('This was a DRY RUN - no changes were made')
        else:
            if total_archived > 0:
                self.stdout.write(
                    self.style.SUCCESS(f'✓ Archived {total_archived} backups')
                )
            if total_deleted > 0:
                self.stdout.write(
                    self.style.SUCCESS(f'✓ Deleted {total_deleted} backups')
                )
            
            if total_archived == 0 and total_deleted == 0:
                self.stdout.write('No backups were processed')
        
        # Show archive statistics
        total_archives = BackupArchive.objects.count()
        if total_archives > 0:
            self.stdout.write(f'\nTotal archives in system: {total_archives}')
            
            total_archive_size = sum(archive.archive_size for archive in BackupArchive.objects.all())
            size_mb = total_archive_size / (1024 * 1024)
            self.stdout.write(f'Total archive size: {size_mb:.1f} MB')
