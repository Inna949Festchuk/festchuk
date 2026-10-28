"""
i18n for Post: rename ru-only fields to *_ru, add *_en counterparts.

Existing data is preserved — old column names are renamed in place.
"""
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('blog', '0001_initial'),
    ]

    operations = [
        migrations.RenameField(
            model_name='post',
            old_name='title',
            new_name='title_ru',
        ),
        migrations.RenameField(
            model_name='post',
            old_name='excerpt',
            new_name='excerpt_ru',
        ),
        migrations.RenameField(
            model_name='post',
            old_name='content',
            new_name='content_ru',
        ),
        migrations.AddField(
            model_name='post',
            name='content_en',
            field=models.TextField(blank=True, verbose_name='Контент (EN, Markdown)'),
        ),
        migrations.AddField(
            model_name='post',
            name='excerpt_en',
            field=models.CharField(blank=True, max_length=500, verbose_name='Анонс (EN)'),
        ),
        migrations.AddField(
            model_name='post',
            name='title_en',
            field=models.CharField(blank=True, max_length=255, verbose_name='Заголовок (EN)'),
        ),
    ]