# Etiqa Auto Backup System

This system has been enhanced with comprehensive automatic backup functionality for network device configurations.

## Features

### 🔄 Automatic Backup Scheduling
- **Multiple Frequencies**: Hourly, Daily, Weekly, Monthly
- **Flexible Backup Types**: Full system, Configuration only, Data only
- **Smart Scheduling**: Automatic next backup calculation
- **Retention Management**: Configurable backup retention policies

### 📊 Backup Management
- **Web Dashboard**: Easy-to-use interface for managing backups
- **Real-time Status**: Live backup status monitoring
- **History Tracking**: Complete backup history with success/failure tracking
- **Download Support**: Direct download of backup files

### 🔧 Network Configuration Backup
- **Device Management**: Track and manage network devices
- **Configuration Storage**: Store multiple versions of device configs
- **Version Control**: Track configuration changes over time
- **Active/Inactive States**: Manage configuration lifecycle

## Quick Start

### 1. Start the Development Server
```bash
python manage.py runserver
```

### 2. Access the Web Interface
- **Main Dashboard**: http://127.0.0.1:8000/
- **Backup Dashboard**: http://127.0.0.1:8000/backup/
- **Network Configs**: http://127.0.0.1:8000/configs/
- **Admin Panel**: http://127.0.0.1:8000/admin/

### 3. Start the Auto Backup Scheduler
```bash
# Option 1: Run the batch file (Windows)
start_backup_scheduler.bat

# Option 2: Run directly
python backup_scheduler.py
```

## Configuration

### Creating Backup Configurations

1. **Via Web Interface**:
   - Go to Backup Dashboard
   - Click "New Backup Config"
   - Fill in the configuration details

2. **Via Admin Panel**:
   - Go to Admin Panel → Backup Configs
   - Add new backup configuration

### Backup Configuration Options

- **Name**: Unique identifier for the backup
- **Type**: 
  - `full`: Complete system backup
  - `config`: Configuration files only
  - `data`: Database and data only
- **Frequency**: How often to run backups
- **Max Backups**: Maximum number of backups to keep
- **Include Options**:
  - Database: Include SQLite database
  - Media: Include media files
  - Logs: Include log files

## Management Commands

### Run Backups Manually
```bash
# Run all scheduled backups
python manage.py run_backups

# Run specific backup configuration
python manage.py run_backups --config "Daily Config Backup"

# Force run even if not due
python manage.py run_backups --config "Daily Config Backup" --force
```

### Check Backup Status
```bash
python manage.py backup_status
```

### Import Devices (CSV/JSON)
```bash
# CSV
python manage.py import_devices devices.csv

# JSON
python manage.py import_devices devices.json

# Update existing devices (matched by IP)
python manage.py import_devices devices.csv --update
```

Accepted columns/keys:
- `ip` or `ip_address` (required)
- `hostname`
- `device_type` or `type` (aliases supported)
- `status` (online/offline)
- `description`

Device type aliases:
- Check Point: `checkpoint`, `check point`, `cp`, `checkpoint firewall`
- F5 BIG-IP: `f5`, `bigip`, `big-ip`, `f5 bigip`, `f5 load balancer`
- Infoblox: `infoblox`, `nios`
- Network: `switch`, `router`, `other`

## API Endpoints

### Backup Status API
```
GET /backup/status/
```
Returns JSON with current backup status for all configurations.

### Backup Management
- `POST /backup/config/{id}/run/` - Run backup immediately
- `POST /backup/config/{id}/toggle/` - Enable/disable backup
- `GET /backup/download/{id}/` - Download backup file

## File Structure

```
network_scanner/
├── models.py              # Database models
├── backup_service.py      # Core backup logic
├── views.py               # Web views
├── urls.py                # URL routing
├── management/
│   └── commands/
│       ├── run_backups.py     # Manual backup command
│       └── backup_status.py   # Status check command
└── templates/
    └── network_scanner/
        ├── backup_dashboard.html
        ├── backup_config_detail.html
        ├── network_configs.html
        └── device_config_detail.html
```

## Database Models

### BackupConfig
Stores backup configuration settings:
- Name, type, frequency
- Enabled/disabled status
- Backup options (database, media, logs)
- Scheduling information

### BackupHistory
Tracks backup execution history:
- Status (pending, running, completed, failed)
- Start/completion times
- File paths and sizes
- Error messages

### NetworkConfig
Stores device configurations:
- Device association
- Configuration data
- Version tracking
- Active/inactive status

## Backup Storage

Backups are stored in the `backups/` directory:
```
backups/
├── config_name_20241209_143022.zip
├── config_name_20241209_150022.zip
└── ...
```

Each backup contains:
- `database.json` - Database dump
- `network_configs.json` - Device configurations
- `media/` - Media files (if enabled)
- `logs/` - Log files (if enabled)

## Scheduling

The backup scheduler runs every 5 minutes and checks for due backups. You can modify the frequency in `backup_scheduler.py`:

```python
# Change from every 5 minutes to every hour
schedule.every().hour.do(run_backups)
```

## Monitoring

### Web Dashboard
- Real-time backup status
- Recent backup history
- Quick action buttons
- Configuration management

### Status Indicators
- 🟢 **Enabled**: Backup configuration is active
- 🔴 **Disabled**: Backup configuration is inactive
- ⚠️ **Due**: Backup is overdue
- ✅ **OK**: Everything is running normally

## Troubleshooting

### Common Issues

1. **Backups not running**:
   - Check if scheduler is running
   - Verify backup configuration is enabled
   - Check Django logs for errors

2. **Permission errors**:
   - Ensure write permissions to backup directory
   - Check file system permissions

3. **Database errors**:
   - Run migrations: `python manage.py migrate`
   - Check database file permissions

### Logs
Check the Django console output for backup-related messages and errors.

## Security Considerations

- Backup files contain sensitive configuration data
- Ensure proper file permissions on backup directory
- Consider encrypting backup files for production use
- Regular cleanup of old backup files

## Production Deployment

For production deployment:

1. **Use a proper task queue** (Celery, RQ) instead of the simple scheduler
2. **Set up proper logging** with file rotation
3. **Configure backup storage** to a secure location
4. **Set up monitoring** and alerting
5. **Implement backup encryption** for sensitive data
6. **Configure automatic cleanup** of old backups

## Support

For issues or questions:
1. Check the Django admin panel for configuration errors
2. Review backup history for failed backups
3. Check the console output for error messages
4. Verify file permissions and disk space
