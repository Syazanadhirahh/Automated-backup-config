from django.core.management.base import BaseCommand
from network_scanner.backup_service import backup_service
from django.utils import timezone


class Command(BaseCommand):
    help = 'Show backup status'

    def handle(self, *args, **options):
        status_list = backup_service.get_backup_status()
        
        if not status_list:
            self.stdout.write('No backup configurations found')
            return
        
        self.stdout.write('\nBackup Status:')
        self.stdout.write('=' * 80)
        
        for status in status_list:
            config = status['config']
            last_backup = status['last_backup']
            next_backup = status['next_backup']
            is_due = status['is_due']
            
            # Status indicator
            if not config.enabled:
                status_indicator = self.style.WARNING('DISABLED')
            elif is_due:
                status_indicator = self.style.ERROR('DUE')
            else:
                status_indicator = self.style.SUCCESS('OK')
            
            self.stdout.write(f'\n{config.name} - {status_indicator}')
            self.stdout.write(f'  Type: {config.backup_type} | Frequency: {config.frequency}')
            
            if last_backup:
                self.stdout.write(f'  Last backup: {last_backup.completed_at}')
                if last_backup.file_size:
                    size_mb = last_backup.file_size / (1024 * 1024)
                    self.stdout.write(f'  Size: {size_mb:.2f} MB')
            else:
                self.stdout.write('  Last backup: Never')
            
            if next_backup:
                self.stdout.write(f'  Next backup: {next_backup}')
            else:
                self.stdout.write('  Next backup: Not scheduled')
        
        self.stdout.write('\n' + '=' * 80)
