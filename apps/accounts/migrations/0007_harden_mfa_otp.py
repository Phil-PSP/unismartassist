from django.db import migrations, models


def clear_legacy_plaintext_otps(apps, schema_editor):
    User = apps.get_model('accounts', 'User')
    User.objects.exclude(mfa_secret='').update(mfa_secret='', mfa_secret_expires=None)


class Migration(migrations.Migration):
    dependencies = [
        ('accounts', '0006_add_personal_email'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='mfa_secret',
            field=models.CharField(blank=True, max_length=64),
        ),
        migrations.AddField(
            model_name='user',
            name='mfa_attempts',
            field=models.PositiveSmallIntegerField(default=0),
        ),
        migrations.AddField(
            model_name='user',
            name='mfa_last_sent_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.RunPython(clear_legacy_plaintext_otps, migrations.RunPython.noop),
    ]
