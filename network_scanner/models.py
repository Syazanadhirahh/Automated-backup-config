from django.db import models
from django.utils import timezone
import json


class Device(models.Model):
    DEVICE_TYPE_CHOICES = [
        ('firewall', 'Checkpoint Firewall'),
        ('f5', 'F5 Load Balancer'),
        ('infoblox', 'Infoblox DNS/DHCP'),
        ('switch', 'Network Switch'),
        ('router', 'Router'),
        ('other', 'Other'),
    ]
    
    ip_address = models.GenericIPAddressField(protocol="both")
    hostname = models.CharField(max_length=255, blank=True)
    device_type = models.CharField(max_length=20, choices=DEVICE_TYPE_CHOICES, default='other')
    status = models.CharField(max_length=20, default="offline")
    last_scanned_at = models.DateTimeField(null=True, blank=True)
    description = models.TextField(blank=True, help_text="Device description or notes")

    class Meta:
        ordering = ['device_type', 'ip_address']

    def __str__(self) -> str:
        return f"{self.get_device_type_display()} - {self.ip_address}"
    
    @property
    def device_type_display(self):
        return self.get_device_type_display()




class BackupConfig(models.Model):
    """Configuration for automatic backups"""
    BACKUP_TYPES = [
        ('full', 'Full System Backup'),
        ('config', 'Configuration Only'),
        ('data', 'Data Only'),
    ]
    
    FREQUENCY_CHOICES = [
        ('hourly', 'Hourly'),
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
    ]
    
    name = models.CharField(max_length=100, unique=True)
    backup_type = models.CharField(max_length=10, choices=BACKUP_TYPES, default='config')
    frequency = models.CharField(max_length=10, choices=FREQUENCY_CHOICES, default='daily')
    enabled = models.BooleanField(default=True)
    auto_push_enabled = models.BooleanField(default=False, help_text="Enable automatic push of backups to remote location")
    max_backups = models.PositiveIntegerField(default=30, help_text="Maximum number of backups to keep")
    retention_months = models.PositiveIntegerField(default=6, help_text="Number of months to keep individual backups before archiving")
    archive_old_backups = models.BooleanField(default=True, help_text="Archive old backups instead of deleting them")
    backup_path = models.CharField(max_length=500, default='backups/')
    archive_path = models.CharField(max_length=500, default='backups/archives/', help_text="Path for archived backups")
    include_database = models.BooleanField(default=True)
    include_media = models.BooleanField(default=False)
    include_logs = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_backup_at = models.DateTimeField(null=True, blank=True)
    next_backup_at = models.DateTimeField(null=True, blank=True)
    
    def __str__(self):
        return f"{self.name} ({self.frequency})"
    
    def save(self, *args, **kwargs):
        if not self.next_backup_at and self.enabled:
            self.schedule_next_backup()
        super().save(*args, **kwargs)
    
    def schedule_next_backup(self):
        """Calculate next backup time based on frequency"""
        now = timezone.now()
        if self.frequency == 'hourly':
            self.next_backup_at = now + timezone.timedelta(hours=1)
        elif self.frequency == 'daily':
            self.next_backup_at = now + timezone.timedelta(days=1)
        elif self.frequency == 'weekly':
            self.next_backup_at = now + timezone.timedelta(weeks=1)
        elif self.frequency == 'monthly':
            self.next_backup_at = now + timezone.timedelta(days=30)


class BackupHistory(models.Model):
    """History of backup operations"""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('running', 'Running'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    ]
    
    config = models.ForeignKey(BackupConfig, on_delete=models.CASCADE, related_name='backups')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    file_path = models.CharField(max_length=500, blank=True)
    file_size = models.BigIntegerField(null=True, blank=True)
    error_message = models.TextField(blank=True)
    backup_data = models.JSONField(default=dict, blank=True)
    
    def __str__(self):
        return f"Backup {self.id} - {self.config.name} ({self.status})"
    
    @property
    def duration(self):
        if self.completed_at and self.started_at:
            return self.completed_at - self.started_at
        return None
    
    def mark_completed(self, file_path=None, file_size=None, backup_data=None):
        self.status = 'completed'
        self.completed_at = timezone.now()
        if file_path:
            self.file_path = file_path
        if file_size:
            self.file_size = file_size
        if backup_data:
            self.backup_data = backup_data
        self.save()
    
    def mark_failed(self, error_message):
        self.status = 'failed'
        self.completed_at = timezone.now()
        self.error_message = error_message
        self.save()


class BackupArchive(models.Model):
    """Track archived backup files"""
    config = models.ForeignKey(BackupConfig, on_delete=models.CASCADE, related_name='archives')
    archive_name = models.CharField(max_length=255, help_text="Name of the archive file")
    archive_path = models.CharField(max_length=500, help_text="Full path to the archive file")
    archive_size = models.BigIntegerField(help_text="Size of the archive in bytes")
    backup_count = models.PositiveIntegerField(help_text="Number of backups in this archive")
    date_range_start = models.DateTimeField(help_text="Start date of backups in archive")
    date_range_end = models.DateTimeField(help_text="End date of backups in archive")
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Archive: {self.archive_name} ({self.backup_count} backups)"
    
    @property
    def archive_size_display(self):
        """Return human readable archive size"""
        size = self.archive_size
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} PB"


class NetworkConfig(models.Model):
    """Store network device configurations"""
    device = models.ForeignKey(Device, on_delete=models.CASCADE, related_name='configs')
    config_type = models.CharField(max_length=50, default='running')
    config_data = models.TextField()
    backup_timestamp = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    version = models.CharField(max_length=20, default='1.0')
    
    def __str__(self):
        return f"{self.device.ip_address} - {self.config_type} ({self.backup_timestamp})"
    
    def to_dict(self):
        return {
            'device_ip': self.device.ip_address,
            'device_hostname': self.device.hostname,
            'config_type': self.config_type,
            'config_data': self.config_data,
            'backup_timestamp': self.backup_timestamp.isoformat(),
            'version': self.version,
            'is_active': self.is_active
        }


class SearchConfig(models.Model):
    """Configuration for search functionality"""
    name = models.CharField(max_length=100, unique=True, help_text="Configuration name")
    enable_hostname_search = models.BooleanField(default=True, help_text="Enable hostname search functionality")
    enable_ip_search = models.BooleanField(default=True, help_text="Enable IP address search functionality")
    enable_suggestions = models.BooleanField(default=True, help_text="Enable search suggestions dropdown")
    min_search_length = models.PositiveIntegerField(default=2, help_text="Minimum characters before showing suggestions")
    max_suggestions = models.PositiveIntegerField(default=10, help_text="Maximum number of suggestions to show")
    search_fields = models.JSONField(
        default=list, 
        help_text="Fields to search in (JSON array of field names)",
        blank=True
    )
    is_active = models.BooleanField(default=True, help_text="Enable this search configuration")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.name} ({'Active' if self.is_active else 'Inactive'})"
    
    def save(self, *args, **kwargs):
        if not self.search_fields:
            self.search_fields = ['ip_address', 'hostname', 'description']
        super().save(*args, **kwargs)
    
    @classmethod
    def get_active_config(cls):
        """Get the active search configuration"""
        config = cls.objects.filter(is_active=True).first()
        if not config:
            # Create default configuration if none exists
            config = cls.objects.create(
                name="Default Search Config",
                is_active=True
            )
        return config


