from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):
    dependencies = [('myapp', '0009_ai_career_foundation')]

    operations = [
        migrations.AddField(model_name='internship', name='first_seen_at', field=models.DateTimeField(blank=True, null=True)),
        migrations.AddField(model_name='internship', name='last_seen_at', field=models.DateTimeField(blank=True, null=True)),
        migrations.AddField(model_name='internship', name='last_checked_at', field=models.DateTimeField(blank=True, null=True)),
        migrations.AddField(model_name='internship', name='expired_at', field=models.DateTimeField(blank=True, null=True)),
        migrations.AddField(model_name='internship', name='source_status', field=models.CharField(default='active', max_length=20)),
        migrations.AddField(model_name='recommendation', name='match_confidence', field=models.CharField(default='medium', max_length=10)),
        migrations.CreateModel(
            name='ImportRun',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('source_name', models.CharField(db_index=True, max_length=100)),
                ('status', models.CharField(choices=[('running','Running'),('success','Success'),('partial','Partial'),('failed','Failed'),('skipped','Skipped')], default='running', max_length=10)),
                ('fetched_count', models.PositiveIntegerField(default=0)),
                ('created_count', models.PositiveIntegerField(default=0)),
                ('updated_count', models.PositiveIntegerField(default=0)),
                ('archived_count', models.PositiveIntegerField(default=0)),
                ('error_message', models.TextField(blank=True, default='')),
                ('started_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('finished_at', models.DateTimeField(blank=True, null=True)),
            ],
            options={'ordering':['-started_at']},
        ),
    ]
