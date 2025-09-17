import os
import json
import zipfile
import shutil
from datetime import datetime, timedelta
from pathlib import Path
from django.conf import settings
from django.utils import timezone
from django.core.management import call_command
from django.db import transaction
from .models import BackupConfig, BackupHistory, BackupArchive, NetworkConfig, Device


class BackupService:
    """Service for handling automatic backups"""
    
    def __init__(self):
        self.base_backup_dir = Path(settings.BASE_DIR) / 'backups'
        self.base_backup_dir.mkdir(exist_ok=True)
    
    def run_scheduled_backups(self):
        """Run all due backups"""
        now = timezone.now()
        due_configs = BackupConfig.objects.filter(
            enabled=True,
            next_backup_at__lte=now
        )
        
        for config in due_configs:
            try:
                self.run_backup(config)
            except Exception as e:
                print(f"Error running backup for {config.name}: {e}")
    
    def run_backup(self, config):
        """Run a specific backup configuration"""
        backup_history = BackupHistory.objects.create(
            config=config,
            status='running'
        )
        
        try:
            # Create backup directory
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_dir = self.base_backup_dir / f"{config.name}_{timestamp}"
            backup_dir.mkdir(exist_ok=True)
            
            backup_data = {}
            
            # Backup database
            if config.include_database:
                db_backup_path = self._backup_database(backup_dir, config)
                backup_data['database'] = str(db_backup_path)
            
            # Backup network configurations
            if config.backup_type in ['config', 'full']:
                config_backup_path = self._backup_network_configs(backup_dir, config)
                backup_data['network_configs'] = str(config_backup_path)
            
            # Backup media files
            if config.include_media and config.backup_type in ['data', 'full']:
                media_backup_path = self._backup_media(backup_dir, config)
                backup_data['media'] = str(media_backup_path)
            
            # Backup logs
            if config.include_logs:
                logs_backup_path = self._backup_logs(backup_dir, config)
                backup_data['logs'] = str(logs_backup_path)
            
            # Create final backup archive
            archive_path = self._create_backup_archive(backup_dir, config, timestamp)
            
            # Update backup history
            file_size = archive_path.stat().st_size if archive_path.exists() else 0
            backup_history.mark_completed(
                file_path=str(archive_path),
                file_size=file_size,
                backup_data=backup_data
            )
            
            # Update config
            config.last_backup_at = timezone.now()
            config.schedule_next_backup()
            config.save()
            
            # Auto push if enabled
            if config.auto_push_enabled:
                self._auto_push_backup(archive_path, config)
            
            # Cleanup old backups
            self._cleanup_old_backups(config)
            
            return backup_history
            
        except Exception as e:
            backup_history.mark_failed(str(e))
            raise
    
    def _backup_database(self, backup_dir, config):
        """Backup database using Django's dumpdata command"""
        db_backup_path = backup_dir / 'database.json'
        
        with open(db_backup_path, 'w') as f:
            call_command('dumpdata', stdout=f, indent=2)
        
        return db_backup_path
    
    def _backup_network_configs(self, backup_dir, config):
        """Backup network device configurations"""
        configs_backup_path = backup_dir / 'network_configs.json'
        
        network_configs = []
        for device in Device.objects.all():
            device_configs = device.configs.filter(is_active=True)
            for net_config in device_configs:
                network_configs.append(net_config.to_dict())
        
        with open(configs_backup_path, 'w') as f:
            json.dump(network_configs, f, indent=2, default=str)
        
        return configs_backup_path
    
    def _backup_media(self, backup_dir, config):
        """Backup media files"""
        media_backup_path = backup_dir / 'media'
        media_backup_path.mkdir(exist_ok=True)
        
        media_dir = Path(settings.MEDIA_ROOT) if hasattr(settings, 'MEDIA_ROOT') else Path(settings.BASE_DIR) / 'media'
        if media_dir.exists():
            shutil.copytree(media_dir, media_backup_path, dirs_exist_ok=True)
        
        return media_backup_path
    
    def _backup_logs(self, backup_dir, config):
        """Backup log files"""
        logs_backup_path = backup_dir / 'logs'
        logs_backup_path.mkdir(exist_ok=True)
        
        # Look for common log locations
        log_dirs = [
            Path(settings.BASE_DIR) / 'logs',
            Path('/var/log') if os.name != 'nt' else Path('C:/logs'),
            Path(settings.BASE_DIR) / 'network_scanner' / 'logs'
        ]
        
        for log_dir in log_dirs:
            if log_dir.exists():
                for log_file in log_dir.glob('*.log'):
                    shutil.copy2(log_file, logs_backup_path)
        
        return logs_backup_path
    
    def _create_backup_archive(self, backup_dir, config, timestamp):
        """Create final backup archive"""
        archive_name = f"{config.name}_{timestamp}.zip"
        archive_path = self.base_backup_dir / archive_name
        
        with zipfile.ZipFile(archive_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(backup_dir):
                for file in files:
                    file_path = Path(root) / file
                    arcname = file_path.relative_to(backup_dir)
                    zipf.write(file_path, arcname)
        
        # Remove temporary directory
        shutil.rmtree(backup_dir)
        
        return archive_path
    
    def _cleanup_old_backups(self, config):
        """Clean up old backups based on retention policy"""
        # Get all backup history records for this config
        cutoff_date = timezone.now() - timezone.timedelta(days=config.retention_months * 30)
        
        # Find backups older than retention period
        old_backups = BackupHistory.objects.filter(
            config=config,
            status='completed',
            completed_at__lt=cutoff_date
        ).order_by('completed_at')
        
        if old_backups.exists() and config.archive_old_backups:
            # Archive old backups instead of deleting
            self._archive_old_backups(config, old_backups)
        else:
            # Delete old backups if archiving is disabled
            for backup in old_backups:
                if backup.file_path and Path(backup.file_path).exists():
                    Path(backup.file_path).unlink()
                backup.delete()
        
        # Also clean up based on max_backups count for recent backups
        recent_backups = BackupHistory.objects.filter(
            config=config,
            status='completed',
            completed_at__gte=cutoff_date
        ).order_by('-completed_at')
        
        if recent_backups.count() > config.max_backups:
            for backup in recent_backups[config.max_backups:]:
                if backup.file_path and Path(backup.file_path).exists():
                    Path(backup.file_path).unlink()
                backup.delete()
    
    def _archive_old_backups(self, config, old_backups):
        """Archive old backups into a single archive file"""
        if not old_backups.exists():
            return
        
        # Create archive directory
        archive_dir = Path(config.archive_path)
        archive_dir.mkdir(parents=True, exist_ok=True)
        
        # Create archive filename with date range
        start_date = old_backups.first().completed_at.strftime('%Y%m%d')
        end_date = old_backups.last().completed_at.strftime('%Y%m%d')
        archive_name = f"{config.name}_archive_{start_date}_to_{end_date}.zip"
        archive_path = archive_dir / archive_name
        
        # Create archive
        with zipfile.ZipFile(archive_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            total_size = 0
            backup_count = 0
            
            for backup in old_backups:
                if backup.file_path and Path(backup.file_path).exists():
                    backup_file = Path(backup.file_path)
                    # Add backup file to archive with timestamp in name
                    timestamp = backup.completed_at.strftime('%Y%m%d_%H%M%S')
                    archive_filename = f"{config.name}_{timestamp}.zip"
                    zipf.write(backup_file, archive_filename)
                    total_size += backup_file.stat().st_size
                    backup_count += 1
                    
                    # Remove original backup file
                    backup_file.unlink()
            
            # Add metadata file
            metadata = {
                'config_name': config.name,
                'archive_created': timezone.now().isoformat(),
                'backup_count': backup_count,
                'date_range_start': old_backups.first().completed_at.isoformat(),
                'date_range_end': old_backups.last().completed_at.isoformat(),
                'total_size': total_size,
                'backups': [
                    {
                        'id': backup.id,
                        'completed_at': backup.completed_at.isoformat(),
                        'file_size': backup.file_size,
                        'status': backup.status
                    }
                    for backup in old_backups
                ]
            }
            
            zipf.writestr('archive_metadata.json', json.dumps(metadata, indent=2))
        
        # Create BackupArchive record
        BackupArchive.objects.create(
            config=config,
            archive_name=archive_name,
            archive_path=str(archive_path),
            archive_size=archive_path.stat().st_size,
            backup_count=backup_count,
            date_range_start=old_backups.first().completed_at,
            date_range_end=old_backups.last().completed_at
        )
        
        # Delete old backup history records
        old_backups.delete()
        
        print(f"Archived {backup_count} backups for {config.name} to {archive_name}")
    
    def restore_from_archive(self, backup_archive, target_backup_id=None):
        """Restore a specific backup from an archive"""
        if not Path(backup_archive.archive_path).exists():
            raise ValueError("Archive file not found")
        
        with zipfile.ZipFile(backup_archive.archive_path, 'r') as zipf:
            # Read metadata
            metadata_str = zipf.read('archive_metadata.json').decode('utf-8')
            metadata = json.loads(metadata_str)
            
            if target_backup_id:
                # Find specific backup in metadata
                target_backup = None
                for backup_info in metadata['backups']:
                    if backup_info['id'] == target_backup_id:
                        target_backup = backup_info
                        break
                
                if not target_backup:
                    raise ValueError(f"Backup ID {target_backup_id} not found in archive")
                
                # Extract specific backup
                timestamp = target_backup['completed_at'][:19].replace(':', '').replace('-', '').replace('T', '_')
                archive_filename = f"{backup_archive.config.name}_{timestamp}.zip"
                
                if archive_filename in zipf.namelist():
                    # Extract to temporary location
                    temp_dir = self.base_backup_dir / f"restore_archive_{backup_archive.id}"
                    temp_dir.mkdir(exist_ok=True)
                    
                    zipf.extract(archive_filename, temp_dir)
                    backup_file = temp_dir / archive_filename
                    
                    # Restore from the extracted backup
                    self.restore_backup_file(backup_file)
                    
                    # Cleanup
                    shutil.rmtree(temp_dir)
                else:
                    raise ValueError(f"Backup file {archive_filename} not found in archive")
            else:
                # Restore all backups from archive
                temp_dir = self.base_backup_dir / f"restore_archive_{backup_archive.id}"
                temp_dir.mkdir(exist_ok=True)
                
                try:
                    # Extract all backup files
                    for filename in zipf.namelist():
                        if filename.endswith('.zip') and filename != 'archive_metadata.json':
                            zipf.extract(filename, temp_dir)
                    
                    # Restore each backup
                    for backup_file in temp_dir.glob('*.zip'):
                        self.restore_backup_file(backup_file)
                
                finally:
                    # Cleanup
                    shutil.rmtree(temp_dir)
    
    def restore_backup_file(self, backup_file):
        """Restore from a backup file"""
        temp_dir = self.base_backup_dir / f"restore_{backup_file.stem}"
        
        try:
            # Extract backup
            with zipfile.ZipFile(backup_file, 'r') as zipf:
                zipf.extractall(temp_dir)
            
            # Restore database
            db_file = temp_dir / 'database.json'
            if db_file.exists():
                call_command('loaddata', str(db_file))
            
            # Restore network configs
            configs_file = temp_dir / 'network_configs.json'
            if configs_file.exists():
                self._restore_network_configs(configs_file)
            
            # Restore media files
            media_dir = temp_dir / 'media'
            if media_dir.exists():
                target_media = Path(settings.MEDIA_ROOT) if hasattr(settings, 'MEDIA_ROOT') else Path(settings.BASE_DIR) / 'media'
                shutil.copytree(media_dir, target_media, dirs_exist_ok=True)
            
        finally:
            # Cleanup
            if temp_dir.exists():
                shutil.rmtree(temp_dir)
    
    def restore_backup(self, backup_history):
        """Restore from a backup"""
        if not backup_history.file_path or not Path(backup_history.file_path).exists():
            raise ValueError("Backup file not found")
        
        archive_path = Path(backup_history.file_path)
        temp_dir = self.base_backup_dir / f"restore_{backup_history.id}"
        
        try:
            # Extract backup
            with zipfile.ZipFile(archive_path, 'r') as zipf:
                zipf.extractall(temp_dir)
            
            # Restore database
            db_file = temp_dir / 'database.json'
            if db_file.exists():
                call_command('loaddata', str(db_file))
            
            # Restore network configs
            configs_file = temp_dir / 'network_configs.json'
            if configs_file.exists():
                self._restore_network_configs(configs_file)
            
            # Restore media
            media_dir = temp_dir / 'media'
            if media_dir.exists():
                target_media = Path(settings.MEDIA_ROOT) if hasattr(settings, 'MEDIA_ROOT') else Path(settings.BASE_DIR) / 'media'
                shutil.copytree(media_dir, target_media, dirs_exist_ok=True)
            
        finally:
            # Cleanup
            if temp_dir.exists():
                shutil.rmtree(temp_dir)
    
    def _restore_network_configs(self, configs_file):
        """Restore network configurations from backup"""
        with open(configs_file, 'r') as f:
            configs_data = json.load(f)
        
        for config_data in configs_data:
            device, created = Device.objects.get_or_create(
                ip_address=config_data['device_ip'],
                defaults={'hostname': config_data.get('device_hostname', '')}
            )
            
            NetworkConfig.objects.create(
                device=device,
                config_type=config_data['config_type'],
                config_data=config_data['config_data'],
                version=config_data.get('version', '1.0'),
                is_active=config_data.get('is_active', True)
            )
    
    def get_backup_status(self):
        """Get current backup status for all configurations"""
        configs = BackupConfig.objects.all()
        status = []
        
        for config in configs:
            last_backup = config.backups.filter(status='completed').first()
            next_backup = config.next_backup_at
            
            status.append({
                'config': config,
                'last_backup': last_backup,
                'next_backup': next_backup,
                'is_due': next_backup and next_backup <= timezone.now() if config.enabled else False
            })
        
        return status
    
    def _auto_push_backup(self, archive_path, config):
        """Auto push backup to remote location if enabled"""
        try:
            # This is a placeholder implementation
            # In a real implementation, you would push to:
            # - Cloud storage (AWS S3, Google Cloud Storage, etc.)
            # - FTP/SFTP server
            # - Network share
            # - Git repository
            # - etc.
            
            print(f"Auto pushing backup {archive_path} for config {config.name}")
            
            # Example implementation for demonstration:
            # You could add configuration fields for:
            # - Remote server details
            # - Authentication credentials
            # - Push destination path
            # - Push method (FTP, SCP, cloud API, etc.)
            
            # For now, just log that auto push would happen
            print(f"Backup {archive_path} would be pushed to remote location for {config.name}")
            
        except Exception as e:
            print(f"Error auto pushing backup for {config.name}: {e}")
            # Don't raise the exception to avoid breaking the backup process


# Global backup service instance
backup_service = BackupService()
