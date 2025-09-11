

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Device',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('ip_address', models.GenericIPAddressField()),
                ('hostname', models.CharField(blank=True, max_length=255)),
                ('status', models.CharField(default='offline', max_length=20)),
                ('last_scanned_at', models.DateTimeField(blank=True, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='ScanResult',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('started_at', models.DateTimeField(auto_now_add=True)),
                ('completed_at', models.DateTimeField(blank=True, null=True)),
                ('target_input', models.CharField(max_length=255)),
            ],
        ),
        migrations.CreateModel(
            name='PortScan',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('port', models.PositiveIntegerField()),
                ('service', models.CharField(blank=True, max_length=100)),
                ('is_open', models.BooleanField(default=False)),
                ('response_time_ms', models.FloatField(blank=True, null=True)),
                ('device', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='port_scans', to='network_scanner.device')),
            ],
        ),
    ]
