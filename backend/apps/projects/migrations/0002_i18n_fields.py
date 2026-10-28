"""
i18n for Project: rename ru-only fields to *_ru, add *_en counterparts.

Existing data is preserved — old column names are renamed in place.
"""
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('projects', '0001_initial'),
    ]

    operations = [
        migrations.RenameField(
            model_name='project',
            old_name='title',
            new_name='title_ru',
        ),
        migrations.RenameField(
            model_name='project',
            old_name='description',
            new_name='description_ru',
        ),
        migrations.RenameField(
            model_name='project',
            old_name='summary',
            new_name='summary_ru',
        ),
        migrations.RenameField(
            model_name='project',
            old_name='readme_content',
            new_name='readme_ru',
        ),
        migrations.AddField(
            model_name='project',
            name='description_en',
            field=models.TextField(blank=True, verbose_name='Описание (EN)'),
        ),
        migrations.AddField(
            model_name='project',
            name='readme_en',
            field=models.TextField(blank=True, verbose_name='README (EN, Markdown)'),
        ),
        migrations.AddField(
            model_name='project',
            name='summary_en',
            field=models.CharField(blank=True, max_length=500, verbose_name='Краткое описание (EN)'),
        ),
        migrations.AddField(
            model_name='project',
            name='title_en',
            field=models.CharField(blank=True, max_length=255, verbose_name='Название (EN)'),
        ),
    ]