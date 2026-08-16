from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion

class Migration(migrations.Migration):
    dependencies = [('myapp', '0010_data_quality_and_matching')]
    operations = [
        migrations.CreateModel(
            name='CareerDocument',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('document_type', models.CharField(choices=[('tailored_resume','Tailored resume'),('cover_letter','Cover letter'),('application_email','Application email')], max_length=24)),
                ('title', models.CharField(max_length=240)),
                ('content', models.TextField()),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('cv', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='career_documents', to='myapp.cv')),
                ('internship', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='career_documents', to='myapp.internship')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='career_documents', to=settings.AUTH_USER_MODEL)),
            ],
            options={'ordering':['-updated_at']},
        )
    ]
