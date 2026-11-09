from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ai_agent', '0005_agent_module_video_file'),
    ]

    operations = [
        migrations.AddField(
            model_name='agentmodule',
            name='tts_voice',
            field=models.CharField(blank=True, default='', help_text='Имя голоса для синтеза речи модуля (пусто — голос по умолчанию из .env)', max_length=50, verbose_name='TTS голос'),
        ),
    ]