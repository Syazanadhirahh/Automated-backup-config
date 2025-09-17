from django.contrib import admin

from .models import Device, BackupConfig, BackupHistory, NetworkConfig, SearchConfig


@admin.register(Device)
class DeviceAdmin(admin.ModelAdmin):
    list_display = ("ip_address", "hostname", "device_type", "status", "last_scanned_at")
    search_fields = ("ip_address", "hostname", "description")
    list_filter = ("device_type", "status", "last_scanned_at")
    fieldsets = (
        ("Device Information", {
            "fields": ("ip_address", "hostname", "device_type", "description")
        }),
        ("Status", {
            "fields": ("status", "last_scanned_at")
        }),
    )


@admin.register(BackupConfig)
class BackupConfigAdmin(admin.ModelAdmin):
    list_display = ("name", "backup_type", "frequency", "enabled", "last_backup_at", "next_backup_at")
    list_filter = ("backup_type", "frequency", "enabled")
    search_fields = ("name",)
    fieldsets = (
        ("Basic Settings", {
            "fields": ("name", "backup_type", "frequency", "enabled")
        }),
        ("Backup Options", {
            "fields": ("max_backups", "backup_path", "include_database", "include_media", "include_logs")
        }),
        ("Timing", {
            "fields": ("last_backup_at", "next_backup_at"),
            "classes": ("collapse",)
        }),
    )


@admin.register(BackupHistory)
class BackupHistoryAdmin(admin.ModelAdmin):
    list_display = ("id", "config", "status", "started_at", "completed_at", "file_size")
    list_filter = ("status", "started_at", "config")
    search_fields = ("config__name",)
    readonly_fields = ("started_at", "completed_at", "duration")


@admin.register(NetworkConfig)
class NetworkConfigAdmin(admin.ModelAdmin):
    list_display = ("device", "config_type", "version", "backup_timestamp", "is_active")
    list_filter = ("config_type", "is_active", "backup_timestamp")
    search_fields = ("device__ip_address", "device__hostname")


@admin.register(SearchConfig)
class SearchConfigAdmin(admin.ModelAdmin):
    list_display = ("name", "is_active", "enable_hostname_search", "enable_ip_search", "enable_suggestions", "created_at")
    list_filter = ("is_active", "enable_hostname_search", "enable_ip_search", "enable_suggestions")
    search_fields = ("name",)
    fieldsets = (
        ("Basic Settings", {
            "fields": ("name", "is_active")
        }),
        ("Search Options", {
            "fields": ("enable_hostname_search", "enable_ip_search", "enable_suggestions")
        }),
        ("Suggestion Settings", {
            "fields": ("min_search_length", "max_suggestions", "search_fields")
        }),
    )
    
    def get_queryset(self, request):
        """Ensure only one active configuration at a time"""
        return super().get_queryset(request)
    
    def save_model(self, request, obj, form, change):
        """Ensure only one active configuration"""
        if obj.is_active:
            # Deactivate all other configurations
            SearchConfig.objects.filter(is_active=True).exclude(id=obj.id).update(is_active=False)
        super().save_model(request, obj, form, change)


