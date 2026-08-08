from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("myapp", "0006_userprofile_is_premium"),
    ]

    operations = [
        migrations.AddField(
            model_name="company",
            name="logo_source_url",
            field=models.URLField(blank=True, max_length=500, null=True),
        ),
        migrations.AddField(
            model_name="internship",
            name="external_id",
            field=models.CharField(
                blank=True, max_length=100, null=True, unique=True
            ),
        ),
        migrations.AddField(
            model_name="internship",
            name="is_premium",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="internship",
            name="job_type",
            field=models.CharField(default="Internship", max_length=50),
        ),
        migrations.AddField(
            model_name="internship",
            name="posted_date",
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="internship",
            name="scraped_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="internship",
            name="source_name",
            field=models.CharField(default="InternHub", max_length=100),
        ),
        migrations.AddField(
            model_name="internship",
            name="source_url",
            field=models.URLField(
                blank=True, max_length=500, null=True, unique=True
            ),
        ),
        migrations.AddField(
            model_name="payment",
            name="stripe_checkout_session_id",
            field=models.CharField(
                blank=True, max_length=255, null=True, unique=True
            ),
        ),
        migrations.AlterField(
            model_name="internship",
            name="application_deadline",
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name="internship",
            name="duration",
            field=models.CharField(default="Not specified", max_length=100),
        ),
        migrations.AlterField(
            model_name="internship",
            name="end_date",
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name="internship",
            name="start_date",
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AlterModelOptions(
            name="internship",
            options={"ordering": ["-posted_date", "-created_at"]},
        ),
    ]
