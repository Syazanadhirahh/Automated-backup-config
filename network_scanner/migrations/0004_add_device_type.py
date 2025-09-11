

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('network_scanner', '0003_remove_scan_models'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='device',
            options={'ordering': ['device_type', 'ip_address']},
        ),
        migrations.AddField(
            model_name='device',
            name='description',
            field=models.TextField(blank=True, help_text='Device description or notes'),
        ),
        migrations.AddField(
            model_name='device',
            name='device_type',
            field=models.CharField(choices=[('firewall', 'Checkpoint Firewall'), ('f5', 'F5 Load Balancer'), ('infoblox', 'Infoblox DNS/DHCP'), ('switch', 'Network Switch'), ('router', 'Router'), ('other', 'Other')], default='other', max_length=20),
        ),
    ]
