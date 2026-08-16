from django.db import migrations, models


def classify_existing_jobs(apps, schema_editor):
    Internship = apps.get_model("myapp", "Internship")
    Internship.objects.filter(source_name="MyJob.mu").update(
        opportunity_type="internship",
        work_mode="onsite",
    )


class Migration(migrations.Migration):

    dependencies = [
        ("myapp", "0007_scraped_job_details_and_checkout"),
    ]

    operations = [
        migrations.AddField(
            model_name="internship",
            name="opportunity_type",
            field=models.CharField(
                choices=[
                    ("local", "Mauritius job"),
                    ("internship", "Internship"),
                    ("graduate", "Graduate role"),
                    ("remote", "Remote job"),
                    ("freelance", "Freelance project"),
                ],
                default="local",
                max_length=20,
            ),
        ),
        migrations.AddField(
            model_name="internship",
            name="work_mode",
            field=models.CharField(
                choices=[
                    ("onsite", "On-site"),
                    ("hybrid", "Hybrid"),
                    ("remote", "Remote"),
                    ("unspecified", "Not specified"),
                ],
                default="unspecified",
                max_length=20,
            ),
        ),
        migrations.AlterField(
            model_name="internship",
            name="source_name",
            field=models.CharField(default="JobHunt MU", max_length=100),
        ),
        migrations.RunPython(classify_existing_jobs, migrations.RunPython.noop),
    ]
