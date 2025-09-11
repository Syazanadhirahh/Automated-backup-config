

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('network_scanner', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='BackupConfig',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, unique=True)),
                ('backup_type', models.CharField(choices=[('full', 'Full System Backup'), ('config', 'Configuration Only'), ('data', 'Data Only')], default='config', max_length=10)),
                ('frequency', models.CharField(choices=[('hourly', 'Hourly'), ('daily', 'Daily'), ('weekly', 'Weekly'), ('monthly', 'Monthly')], default='daily', max_length=10)),
                ('enabled', models.BooleanField(default=True)),
                ('max_backups', models.PositiveIntegerField(default=30, help_text='Maximum number of backups to keep')),
                ('backup_path', models.CharField(default='backups/', max_length=500)),
                ('include_database', models.BooleanField(default=True)),
                ('include_media', models.BooleanField(default=False)),
                ('include_logs', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('last_backup_at', models.DateTimeField(blank=True, null=True)),
                ('next_backup_at', models.DateTimeField(blank=True, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='BackupHistory',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('status', models.CharField(choices=[('pending', 'Pending'), ('running', 'Running'), ('completed', 'Completed'), ('failed', 'Failed'), ('cancelled', 'Cancelled')], default='pending', max_length=10)),
                ('started_at', models.DateTimeField(auto_now_add=True)),
                ('completed_at', models.DateTimeField(blank=True, null=True)),
                ('file_path', models.CharField(blank=True, max_length=500)),
                ('file_size', models.BigIntegerField(blank=True, null=True)),
                ('error_message', models.TextField(blank=True)),
                ('backup_data', models.JSONField(blank=True, default=dict)),
                ('config', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='backups', to='network_scanner.backupconfig')),
            ],
        ),
        migrations.CreateModel(
            name='NetworkConfig',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('config_type', models.CharField(default='running', max_length=50)),
                ('config_data', models.TextField()),
                ('backup_timestamp', models.DateTimeField(auto_now_add=True)),
                ('is_active', models.BooleanField(default=True)),
                ('version', models.CharField(default='1.0', max_length=20)),
                ('device', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='configs', to='network_scanner.device')),
            ],
        ),
    ]
