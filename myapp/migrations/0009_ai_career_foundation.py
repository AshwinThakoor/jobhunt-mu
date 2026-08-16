from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [('myapp', '0008_opportunity_categories_and_work_mode')]

    operations = [
        migrations.AddField(model_name='cv', name='extracted_text', field=models.TextField(blank=True, default='')),
        migrations.AddField(model_name='cv', name='extracted_skills', field=models.JSONField(blank=True, default=list)),
        migrations.AddField(model_name='cv', name='extraction_warnings', field=models.JSONField(blank=True, default=list)),
        migrations.AddField(model_name='cv', name='parsed_at', field=models.DateTimeField(blank=True, null=True)),
        migrations.AddField(model_name='recommendation', name='matched_skills', field=models.JSONField(blank=True, default=list)),
        migrations.AddField(model_name='recommendation', name='missing_skills', field=models.JSONField(blank=True, default=list)),
        migrations.AddField(model_name='recommendation', name='score_breakdown', field=models.JSONField(blank=True, default=dict)),
        migrations.AddField(model_name='recommendation', name='status', field=models.CharField(choices=[('active','Active'),('saved','Saved'),('dismissed','Not interested'),('applied','Applied')], default='active', max_length=12)),
        migrations.AddField(model_name='recommendation', name='updated_at', field=models.DateTimeField(auto_now=True)),
        migrations.CreateModel(
            name='SavedJob',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('internship', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='saved_by', to='myapp.internship')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='saved_jobs', to='auth.user')),
            ],
            options={'ordering':['-created_at']},
        ),
        migrations.AddConstraint(model_name='savedjob', constraint=models.UniqueConstraint(fields=('user','internship'), name='unique_saved_job')),
    ]
