# Generated by Django 5.0.5 on 2024-06-18 15:15

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('apps', '0008_rename_assignment_submission_assignment_id_and_more'),
    ]

    operations = [
        migrations.RenameField(
            model_name='submission',
            old_name='is_submited',
            new_name='is_submitted',
        ),
    ]
