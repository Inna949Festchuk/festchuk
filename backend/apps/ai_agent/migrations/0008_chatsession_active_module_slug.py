from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ai_agent', '0007_agentmodule_routing_keywords'),
    ]

    operations = [
        migrations.AddField(
            model_name='chatsession',
            name='active_module_slug',
            field=models.CharField(
                blank=True,
                default='',
                help_text='Slug модуля, отвечавшего в прошлом ходу (маркер смены персоны в истории)',
                max_length=50,
                verbose_name='Активный модуль',
            ),
        ),
    ]
