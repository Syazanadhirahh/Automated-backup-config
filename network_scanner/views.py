from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
import json

from .models import Device, BackupConfig, BackupHistory, BackupArchive, NetworkConfig
from .backup_service import backup_service
from .forms import CustomLoginForm


def login_view(request):
    """Custom login view"""
    if request.user.is_authenticated:
        return redirect('network_scanner:backup_dashboard')
    
    if request.method == 'POST':
        form = CustomLoginForm(data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('network_scanner:backup_dashboard')
        else:
            messages.error(request, 'Invalid username or password.')
    else:
        form = CustomLoginForm()
    
    return render(request, 'network_scanner/login.html', {'form': form})


def logout_view(request):
    """Custom logout view"""
    if request.user.is_authenticated:
        username = request.user.username
        logout(request)
        messages.info(request, f'You have been logged out.')
    return redirect('network_scanner:login')


@login_required
def backup_dashboard(request):
    """Backup management dashboard"""
    configs = BackupConfig.objects.all()
    recent_backups = BackupHistory.objects.select_related('config').order_by('-started_at')[:10]
    backup_status = backup_service.get_backup_status()
    
    context = {
        'configs': configs,
        'recent_backups': recent_backups,
        'backup_status': backup_status,
    }
    return render(request, "network_scanner/backup_dashboard.html", context)


@login_required
def backup_config_detail(request, config_id):
    """Backup configuration detail view"""
    config = get_object_or_404(BackupConfig, id=config_id)
    backups = config.backups.order_by('-started_at')[:20]
    
    context = {
        'config': config,
        'backups': backups,
    }
    return render(request, "network_scanner/backup_config_detail.html", context)


@login_required
@require_POST
def run_backup_now(request, config_id):
    """Run backup immediately"""
    config = get_object_or_404(BackupConfig, id=config_id)
    
    try:
        backup_history = backup_service.run_backup(config)
        messages.success(request, f'Backup started successfully: {backup_history}')
    except Exception as e:
        messages.error(request, f'Error starting backup: {str(e)}')
    
    return redirect('network_scanner:backup_config_detail', config_id=config_id)


@login_required
@require_POST
def toggle_backup_config(request, config_id):
    """Toggle backup configuration enabled/disabled"""
    config = get_object_or_404(BackupConfig, id=config_id)
    config.enabled = not config.enabled
    config.save()
    
    status = "enabled" if config.enabled else "disabled"
    messages.success(request, f'Backup configuration {status}')
    
    return redirect('network_scanner:backup_dashboard')


@login_required
def backup_download(request, backup_id):
    """Download backup file"""
    backup = get_object_or_404(BackupHistory, id=backup_id)
    
    if not backup.file_path or backup.status != 'completed':
        messages.error(request, 'Backup file not available')
        return redirect('network_scanner:backup_dashboard')
    
    try:
        with open(backup.file_path, 'rb') as f:
            response = HttpResponse(f.read(), content_type='application/zip')
            response['Content-Disposition'] = f'attachment; filename="{backup.config.name}_{backup.started_at.strftime("%Y%m%d_%H%M%S")}.zip"'
            return response
    except FileNotFoundError:
        messages.error(request, 'Backup file not found')
        return redirect('network_scanner:backup_dashboard')


@login_required
def network_configs(request):
    """Network device configurations view"""
    devices = Device.objects.prefetch_related('configs').all()
    
    context = {
        'devices': devices,
    }
    return render(request, "network_scanner/network_configs.html", context)


@login_required
def device_config_detail(request, device_id):
    """Device configuration detail view"""
    device = get_object_or_404(Device, id=device_id)
    configs = device.configs.order_by('-backup_timestamp')
    active_configs_count = device.configs.filter(is_active=True).count()
    
    context = {
        'device': device,
        'configs': configs,
        'active_configs_count': active_configs_count,
    }
    return render(request, "network_scanner/device_config_detail.html", context)


@login_required
@require_POST
def backup_device_config(request, device_id):
    """Backup device configuration"""
    device = get_object_or_404(Device, id=device_id)
    
    # Letak ip address kat sini
    config_data = f"# Configuration backup for {device.ip_address}\n# Generated at {timezone.now()}\n# This is a placeholder - implement actual config retrieval"
    
    NetworkConfig.objects.create(
        device=device,
        config_type='running',
        config_data=config_data,
        version='1.0'
    )
    
    messages.success(request, f'Configuration backed up for {device.ip_address}')
    return redirect('network_scanner:device_config_detail', device_id=device_id)


@login_required
def backup_status_api(request):
    """API endpoint for backup status"""
    status = backup_service.get_backup_status()
    
    data = []
    for item in status:
        config = item['config']
        last_backup = item['last_backup']
        next_backup = item['next_backup']
        
        data.append({
            'name': config.name,
            'enabled': config.enabled,
            'backup_type': config.backup_type,
            'frequency': config.frequency,
            'last_backup': (
                last_backup.completed_at.isoformat()
                if last_backup and last_backup.completed_at
                else None
            ),
            'next_backup': next_backup.isoformat() if next_backup else None,
            'is_due': item['is_due'],
        })
    
    return JsonResponse({'backups': data})


@login_required
def device_type_backups(request, device_type):
    """View backups filtered by device type"""
    # Validate device type
    valid_types = [choice[0] for choice in Device.DEVICE_TYPE_CHOICES]
    if device_type not in valid_types:
        messages.error(request, 'Invalid device type.')
        return redirect('network_scanner:backup_dashboard')
    
    # Get devices of the specified type
    devices = Device.objects.filter(device_type=device_type).prefetch_related('configs')
    
    # Get all network configs for these devices
    device_ids = devices.values_list('id', flat=True)
    network_configs = NetworkConfig.objects.filter(device_id__in=device_ids).order_by('-backup_timestamp')
    
    # Get device type display name
    device_type_display = dict(Device.DEVICE_TYPE_CHOICES).get(device_type, device_type.title())
    
    # Get backup statistics
    total_devices = devices.count()
    online_devices = devices.filter(status='online').count()
    total_configs = network_configs.count()
    recent_configs = network_configs.filter(backup_timestamp__gte=timezone.now() - timezone.timedelta(days=7)).count()
    
    context = {
        'device_type': device_type,
        'device_type_display': device_type_display,
        'devices': devices,
        'network_configs': network_configs,
        'total_devices': total_devices,
        'online_devices': online_devices,
        'total_configs': total_configs,
        'recent_configs': recent_configs,
    }
    
    return render(request, 'network_scanner/device_type_backups.html', context)


def backup_history_public(request):
    """Public backup history view - accessible without authentication"""
    # Get all backup history records with related config data
    backup_history = BackupHistory.objects.select_related('config').order_by('-started_at')
    
    # Get statistics
    total_backups = backup_history.count()
    completed_backups = backup_history.filter(status='completed').count()
    failed_backups = backup_history.filter(status='failed').count()
    running_backups = backup_history.filter(status='running').count()
    
    # Get recent backups (last 7 days)
    recent_backups = backup_history.filter(
        started_at__gte=timezone.now() - timezone.timedelta(days=7)
    ).count()
    
    # Get backup history by status
    status_counts = {}
    for status, _ in BackupHistory.STATUS_CHOICES:
        status_counts[status] = backup_history.filter(status=status).count()
    
    # Get backup history by config
    config_stats = {}
    for config in BackupConfig.objects.all():
        config_backups = backup_history.filter(config=config)
        config_archives = BackupArchive.objects.filter(config=config)
        config_stats[config.name] = {
            'total': config_backups.count(),
            'completed': config_backups.filter(status='completed').count(),
            'failed': config_backups.filter(status='failed').count(),
            'last_backup': config_backups.first().started_at if config_backups.exists() else None,
            'archives': config_archives.count(),
            'archived_backups': sum(archive.backup_count for archive in config_archives),
        }
    
    # Get all archived backups
    archived_backups = BackupArchive.objects.select_related('config').order_by('-created_at')
    
    context = {
        'backup_history': backup_history,
        'archived_backups': archived_backups,
        'total_backups': total_backups,
        'completed_backups': completed_backups,
        'failed_backups': failed_backups,
        'running_backups': running_backups,
        'recent_backups': recent_backups,
        'status_counts': status_counts,
        'config_stats': config_stats,
    }
    
    return render(request, 'network_scanner/backup_history_public.html', context)



