# Generated by Django 4.2.6 on 2023-11-04 02:08

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ecomapp', '0003_admin'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='admin',
            name='address',
        ),
        migrations.RemoveField(
            model_name='admin',
            name='joined_on',
        ),
        migrations.AddField(
            model_name='admin',
            name='image',
            field=models.ImageField(default='/images/admin.admin.png', upload_to='admins'),
        ),
        migrations.AddField(
            model_name='admin',
            name='mobile',
            field=models.CharField(blank=True, max_length=20, null=True),
        ),
        migrations.AlterField(
            model_name='admin',
            name='full_name',
            field=models.CharField(max_length=50),
        ),
    ]
