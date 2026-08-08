"""Regression tests for job discovery, resume analysis, matching, payments, and application workflows."""
from django.utils import timezone
from datetime import date
from types import SimpleNamespace
from unittest.mock import patch

from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse

from scrape_myjobmu import parse_description

from .models import CV, Company, Internship, Payment, Recommendation, SavedJob
from .services.cv_analyzer import ExtractionResult, analyse_cv_text


class JobBoardTests(TestCase):
    def setUp(self):
        self.company = Company.objects.create(
            name="Northstar Studio",
            description="A growing product company.",
            location="Moka",
            industry="Technology",
        )
        self.internship = Internship.objects.create(
            company=self.company,
            title="Product Design Intern",
            description="Help the team research and design useful digital products.",
            requirements="Curiosity and a strong portfolio.",
            responsibilities="Support research, wireframes and prototypes.",
            location="Moka",
            stipend="Not disclosed",
            skills_required=["Figma", "Research"],
            benefits=["Mentorship"],
            application_deadline=date(2030, 8, 31),
            posted_date=date(2030, 7, 28),
        )

    def test_job_board_is_public_and_renders_complete_listing(self):
        response = self.client.get(reverse("internship_list"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Product Design Intern")
        self.assertContains(response, "Northstar Studio")
        self.assertContains(response, "One search. Many trusted sources.")
        self.assertContains(response, "Mauritius job")
        self.assertContains(response, "LinkedIn")

    def test_job_board_filters_by_category_and_source(self):
        self.internship.opportunity_type = "freelance"
        self.internship.source_name = "Freelancer.com"
        self.internship.save(update_fields=["opportunity_type", "source_name"])

        response = self.client.get(
            reverse("internship_list"),
            {"opportunity_type": "freelance", "source": "Freelancer.com"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Product Design Intern")
        self.assertEqual(response.context["total_count"], 1)

    def test_job_board_hides_non_matching_sources(self):
        response = self.client.get(
            reverse("internship_list"),
            {"source": "Remotive"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "Product Design Intern")
        self.assertEqual(response.context["total_count"], 0)

    def test_premium_description_is_hidden_from_anonymous_users(self):
        self.internship.is_premium = True
        self.internship.save(update_fields=["is_premium"])

        response = self.client.get(
            reverse("internship_detail", args=[self.internship.pk])
        )

        self.assertContains(response, "Unlock the complete opportunity")
        self.assertNotContains(response, self.internship.responsibilities)


@override_settings(
    STRIPE_SECRET_KEY="configured-test-key",
    PREMIUM_PRICE_CENTS=1999,
    PREMIUM_CURRENCY="usd",
)
class StripeCheckoutTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="student",
            password="secure-test-password",
            email="student@example.com",
        )
        self.client.force_login(self.user)

    @patch("myapp.views.stripe.checkout.Session.create")
    def test_checkout_creates_pending_payment_and_redirects_to_stripe(
        self, create_session
    ):
        create_session.return_value = SimpleNamespace(
            id="cs_test_123",
            url="https://checkout.stripe.com/c/pay/cs_test_123",
        )

        response = self.client.post(reverse("create_payment"))

        self.assertRedirects(
            response,
            "https://checkout.stripe.com/c/pay/cs_test_123",
            fetch_redirect_response=False,
        )
        payment = Payment.objects.get(user=self.user)
        self.assertEqual(payment.status, "pending")
        self.assertEqual(payment.stripe_checkout_session_id, "cs_test_123")

    @patch("myapp.views.stripe.checkout.Session.retrieve")
    def test_paid_checkout_activates_premium(self, retrieve_session):
        Payment.objects.create(
            user=self.user,
            payment_type="premium_subscription",
            amount="19.99",
            currency="USD",
            stripe_checkout_session_id="cs_paid",
        )
        retrieve_session.return_value = SimpleNamespace(
            id="cs_paid",
            client_reference_id=str(self.user.pk),
            payment_status="paid",
            payment_intent="pi_paid",
        )

        response = self.client.get(
            reverse("payment_success"),
            {"session_id": "cs_paid"},
        )

        self.assertEqual(response.status_code, 200)
        self.user.userprofile.refresh_from_db()
        payment = Payment.objects.get(stripe_checkout_session_id="cs_paid")
        self.assertTrue(self.user.userprofile.is_premium)
        self.assertEqual(payment.status, "completed")
        self.assertEqual(payment.stripe_payment_intent_id, "pi_paid")

    @patch("myapp.views.stripe.checkout.Session.retrieve")
    def test_unpaid_checkout_never_activates_premium(self, retrieve_session):
        Payment.objects.create(
            user=self.user,
            payment_type="premium_subscription",
            amount="19.99",
            currency="USD",
            stripe_checkout_session_id="cs_unpaid",
        )
        retrieve_session.return_value = SimpleNamespace(
            id="cs_unpaid",
            client_reference_id=str(self.user.pk),
            payment_status="unpaid",
            payment_intent=None,
        )

        self.client.get(
            reverse("payment_success"),
            {"session_id": "cs_unpaid"},
        )

        self.user.userprofile.refresh_from_db()
        payment = Payment.objects.get(stripe_checkout_session_id="cs_unpaid")
        self.assertFalse(self.user.userprofile.is_premium)
        self.assertEqual(payment.status, "pending")

    def test_legacy_success_url_cannot_grant_premium_without_session(self):
        self.client.get(reverse("confirm_premium_success"))

        self.user.userprofile.refresh_from_db()
        self.assertFalse(self.user.userprofile.is_premium)


class ScraperParsingTests(TestCase):
    def test_full_description_is_split_into_useful_sections(self):
        parsed = parse_description(
            """
            <p>Join our product team and learn from senior designers.</p>
            <h3>Key Responsibilities</h3>
            <ul><li>Interview customers</li><li>Build prototypes</li></ul>
            <h3>Who We Are Looking For</h3>
            <ul><li>Clear communication</li><li>A learning mindset</li></ul>
            <h3>What We Offer</h3>
            <ul><li>Weekly mentorship</li></ul>
            """
        )

        self.assertIn("Join our product team", parsed["description"])
        self.assertIn("Interview customers", parsed["responsibilities"])
        self.assertIn("Clear communication", parsed["requirements"])
        self.assertEqual(parsed["benefits"], ["Weekly mentorship"])


class CVAnalyzerTests(TestCase):
    def test_strong_evidence_scores_better_than_generic_thin_cv(self):
        strong_cv = """
        Alex Candidate
        alex@example.com | +230 5123 4567 | linkedin.com/in/alexcandidate

        PROFESSIONAL SUMMARY
        Data analyst who turns operational data into clear decisions using Python,
        SQL, Excel and Power BI.

        EXPERIENCE
        Data Analyst Intern, Northstar
        • Automated weekly reporting with Python, saving 6 hours every week.
        • Built 4 Power BI dashboards used by 25 team members.
        • Analysed 50,000 customer records and improved data quality by 18 percent.
        • Presented findings to 3 department leads and supported quarterly planning.
        • Reduced report preparation time by 30 percent through SQL automation.
        • Collaborated with sales teams to define 12 performance measures.

        EDUCATION
        BSc Data Science, University of Mauritius

        SKILLS
        Python, SQL, Excel, Power BI, data analysis, communication

        PROJECTS
        Designed a forecasting project using pandas and presented the results.
        """
        weak_cv = """
        Alex Candidate
        2020 - 2024
        I am a hardworking, results-driven team player. I work well under pressure
        and I am self-motivated. References available on request.
        """

        strong_report = analyse_cv_text(strong_cv)
        weak_report = analyse_cv_text(weak_cv)

        self.assertGreater(
            strong_report["overall_score"],
            weak_report["overall_score"],
        )
        self.assertGreaterEqual(strong_report["metrics"]["quantified_count"], 3)
        self.assertFalse(weak_report["checks"][1]["passed"])
        self.assertTrue(
            any(
                item["priority"] == "High"
                for item in weak_report["recommendations"]
            )
        )

    def test_targeted_analysis_reports_real_skill_gaps(self):
        report = analyse_cv_text(
            """
            Sam Lee | sam@example.com | +230 5987 6543
            SUMMARY
            Junior developer with Python experience.
            EXPERIENCE
            • Built a Python reporting tool for a student project.
            EDUCATION
            BSc Software Engineering
            SKILLS
            Python, Git
            """,
            target_role="Junior Data Analyst",
            job_description=(
                "Use Python, SQL, Power BI and Excel to deliver data analysis and "
                "data visualization."
            ),
        )

        self.assertIn("python", report["target"]["matched_skills"])
        self.assertIn("sql", report["target"]["missing_skills"])
        self.assertTrue(
            any(
                item["category"] == "Role alignment"
                for item in report["recommendations"]
            )
        )
        self.assertEqual(report["categories"][-1]["name"], "Role alignment")


class CVAnalyzerViewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="cv-owner",
            password="secure-test-password",
            email="owner@example.com",
        )
        self.other_user = User.objects.create_user(
            username="other-user",
            password="secure-test-password",
        )
        self.cv = CV.objects.create(
            user=self.user,
            title="Graduate CV",
            file=SimpleUploadedFile(
                "graduate.docx",
                b"placeholder document",
                content_type=(
                    "application/vnd.openxmlformats-officedocument."
                    "wordprocessingml.document"
                ),
            ),
        )

    def test_user_cannot_open_another_users_checker(self):
        self.client.force_login(self.other_user)

        response = self.client.get(reverse("cv_analyze", args=[self.cv.pk]))

        self.assertEqual(response.status_code, 404)

    @patch("myapp.views.extract_cv")
    def test_checker_renders_score_and_recommendations(self, extract_cv_mock):
        extract_cv_mock.return_value = ExtractionResult(
            text="""
            Jamie Doe | jamie@example.com | +230 5987 6543
            SUMMARY
            Graduate analyst with Python and Excel experience.
            EXPERIENCE
            • Built a Python dashboard for a university project.
            EDUCATION
            BSc Information Systems
            SKILLS
            Python, Excel
            """,
            file_type="DOCX",
        )
        self.client.force_login(self.user)

        response = self.client.post(
            reverse("cv_analyze", args=[self.cv.pk]),
            {
                "target_role": "Data Analyst",
                "job_description": "Use Python, SQL and Power BI for data analysis.",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Your CV scorecard")
        self.assertContains(response, "Prioritized recommendations")
        self.assertContains(response, "Role alignment")
        self.assertIsNotNone(response.context["report"])


class CareerMatchingTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='careeruser', password='safe-password')
        self.company = Company.objects.create(name='DataWorks', description='Analytics company', location='Moka', industry='Technology')
        self.job = Internship.objects.create(company=self.company, title='Junior Data Analyst', description='Analyse business data', requirements='Python SQL Excel Power BI', responsibilities='Build reports', location='Moka', skills_required=['Python','SQL','Excel','Power BI'], status='active')
        self.cv = CV.objects.create(user=self.user, title='Data CV', file=SimpleUploadedFile('resume.pdf', b'%PDF-1.4 test'), is_primary=True, extracted_text='Junior data analyst using Python SQL and Excel to build reports.', extracted_skills=['python','sql','excel'])
        self.client.force_login(self.user)

    def test_recommendations_are_explainable_and_ranked(self):
        response = self.client.get(reverse('recommendations'))
        self.assertEqual(response.status_code, 200)
        rec = Recommendation.objects.get(user=self.user, internship=self.job)
        self.assertGreater(rec.score, 0)
        self.assertIn('python', rec.matched_skills)
        self.assertIn('power bi', rec.missing_skills)
        self.assertContains(response, 'Detailed evidence is a Premium feature')
        self.assertNotContains(response, 'How this score was calculated')

    def test_user_can_save_a_recommendation(self):
        self.client.get(reverse('recommendations'))
        rec = Recommendation.objects.get(user=self.user, internship=self.job)
        response = self.client.post(reverse('recommendation_action', args=[rec.pk]), {'action':'save'})
        self.assertEqual(response.status_code, 302)
        self.assertTrue(SavedJob.objects.filter(user=self.user, internship=self.job).exists())

class RecommendationPlanAccessTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='basic-user', password='safe-password')
        self.client.force_login(self.user)
        self.cv = CV.objects.create(
            user=self.user,
            title='Primary CV',
            is_primary=True,
            extracted_text='Python SQL Excel data analysis communication',
            extracted_skills=['Python', 'SQL', 'Excel'],
            file=SimpleUploadedFile('resume.pdf', b'%PDF-1.4 test', content_type='application/pdf'),
        )
        company = Company.objects.create(
            name='Plan Test Co', description='Testing', location='Moka', industry='Technology'
        )
        for index in range(5):
            Internship.objects.create(
                company=company,
                title=f'Data Role {index}',
                description='Analyse data with Python and SQL.',
                requirements='Python SQL Excel',
                responsibilities='Build reports.',
                location='Moka',
                skills_required=['Python', 'SQL'],
                application_deadline=date(2030, 12, 31),
                posted_date=date(2030, 7, 1),
            )

    def test_basic_user_sees_only_three_matches_and_locked_evidence(self):
        response = self.client.get(reverse('recommendations'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['recommendations']), 3)
        self.assertContains(response, 'Basic preview')
        self.assertContains(response, 'Detailed evidence is a Premium feature')
        self.assertNotContains(response, 'How this score was calculated')

    def test_premium_user_sees_full_evidence_and_more_matches(self):
        profile = self.user.userprofile
        profile.is_premium = True
        profile.save(update_fields=['is_premium'])
        response = self.client.get(reverse('recommendations'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['recommendations']), 5)
        self.assertContains(response, 'How this score was calculated')
        self.assertNotContains(response, 'Detailed evidence is a Premium feature')


class DataQualityPhaseTests(TestCase):
    def test_matcher_normalizes_skill_aliases_and_confidence(self):
        from myapp.services.job_matcher import match_resume_to_job
        company = Company.objects.create(name='Alias Co', description='x', location='Moka', industry='Tech')
        job = Internship.objects.create(company=company, title='Data Analyst', description='Reporting', requirements='SQL and Power BI', responsibilities='Dashboards', location='Moka', skills_required=['SQL','Power BI'])
        result = match_resume_to_job(resume_text='Data analyst with MySQL, business intelligence and reporting experience. ' * 12, profile_skills=[], job=job)
        self.assertIn('sql', result['matched_skills'])
        self.assertIn(result['match_confidence'], {'medium','high'})
        self.assertGreater(result['score'], 0.3)

    def test_import_run_duration_is_non_negative(self):
        from myapp.models import ImportRun
        run = ImportRun.objects.create(source_name='Test', status='success', finished_at=timezone.now())
        self.assertGreaterEqual(run.duration_seconds, 0)

class ApplicationStudioTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='studio-user', password='safe-password', email='studio@example.com', first_name='Studio', last_name='User')
        self.company = Company.objects.create(name='Studio Co', description='Data company', location='Moka', industry='Technology')
        self.job = Internship.objects.create(company=self.company, title='Junior Data Analyst', description='Analyse data', requirements='Python SQL Power BI', responsibilities='Build dashboards', location='Moka', skills_required=['Python','SQL','Power BI'])
        self.cv = CV.objects.create(user=self.user, title='Primary CV', is_primary=True, file=SimpleUploadedFile('cv.pdf', b'%PDF test'), extracted_text='Data analyst. Built a Python and SQL dashboard for a university project.', extracted_skills=['python','sql'])
        self.client.force_login(self.user)

    def test_basic_user_gets_analysis_but_not_generation(self):
        response = self.client.get(reverse('application_studio', args=[self.job.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Why you match')
        self.assertContains(response, 'Premium document generation')
        response = self.client.post(reverse('application_studio', args=[self.job.pk]), {'action':'cover_letter','cv_id':self.cv.pk})
        self.assertEqual(response.status_code, 302)
        from .models import CareerDocument
        self.assertFalse(CareerDocument.objects.filter(user=self.user).exists())

    def test_premium_user_can_generate_edit_and_download_docx(self):
        self.user.userprofile.is_premium = True
        self.user.userprofile.save(update_fields=['is_premium'])
        response = self.client.post(reverse('application_studio', args=[self.job.pk]), {'action':'cover_letter','cv_id':self.cv.pk})
        self.assertEqual(response.status_code, 302)
        from .models import CareerDocument
        document = CareerDocument.objects.get(user=self.user)
        self.assertIn('Junior Data Analyst', document.content)
        edit = self.client.post(reverse('career_document_edit', args=[document.pk]), {'title':'Edited letter','content':'Verified content'})
        self.assertEqual(edit.status_code, 302)
        download = self.client.get(reverse('career_document_download', args=[document.pk]))
        self.assertEqual(download.status_code, 200)
        self.assertIn('wordprocessingml.document', download['Content-Type'])
