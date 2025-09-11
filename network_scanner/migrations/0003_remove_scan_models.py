

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('network_scanner', '0002_backupconfig_backuphistory_networkconfig'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='portscan',
            name='device',
        ),
        migrations.DeleteModel(
            name='ScanResult',
        ),
        migrations.DeleteModel(
            name='PortScan',
        ),
    ]
