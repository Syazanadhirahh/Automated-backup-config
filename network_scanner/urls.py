from django.urls import path
from . import views


app_name = "network_scanner"

urlpatterns = [
    # Authentication URLs
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    
    # Backup management URLs
    path("", views.backup_dashboard, name="backup_dashboard"),
    path("backup/", views.backup_dashboard, name="backup_dashboard"),
    path("backup/config/<int:config_id>/", views.backup_config_detail, name="backup_config_detail"),
    path("backup/config/<int:config_id>/run/", views.run_backup_now, name="run_backup_now"),
    path("backup/config/<int:config_id>/toggle/", views.toggle_backup_config, name="toggle_backup_config"),
    path("backup/config/<int:config_id>/toggle-auto-push/", views.toggle_auto_push, name="toggle_auto_push"),
    path("backup/download/<int:backup_id>/", views.backup_download, name="backup_download"),
    path("backup/status/", views.backup_status_api, name="backup_status_api"),
    
    # Network configuration URLs
    path("configs/", views.network_configs, name="network_configs"),
    path("configs/device/<int:device_id>/", views.device_config_detail, name="device_config_detail"),
    path("configs/device/<int:device_id>/backup/", views.backup_device_config, name="backup_device_config"),
    
    # Device type filtering URLs
    path("device/<str:device_type>/", views.device_type_backups, name="device_type_backups"),
    
    # Public backup history URL (no authentication required)
    path("backup-history/", views.backup_history_public, name="backup_history_public"),
]



