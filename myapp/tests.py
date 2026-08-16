"""Public regression tests for recruiter-visible JobHunt MU components.

Tests for private source adapters, recommendation scoring and application-generation
rules live with the private implementation and are intentionally excluded here.
"""
from datetime import date
from types import SimpleNamespace
from unittest.mock import patch

from django.contrib.auth.models import User
from django.test import TestCase, override_settings
from django.urls import reverse

from .models import Company, Internship, Payment
from .services.cv_analyzer import analyse_cv_text


class JobBoardTests(TestCase):
    def setUp(self):
        self.company = Company.objects.create(
            name="Northstar Studio",
            description="A growing product company.",
            location="Moka",
            industry="Technology",
        )
        self.opportunity = Internship.objects.create(
            company=self.company,
            title="Product Design Intern",
            description="Help research and design useful digital products.",
            requirements="Curiosity and a strong portfolio.",
            responsibilities="Support research, wireframes and prototypes.",
            location="Moka",
            stipend="Not disclosed",
            skills_required=["Figma", "Research"],
            benefits=["Mentorship"],
            application_deadline=date(2030, 8, 31),
            posted_date=date(2030, 7, 28),
        )

    def test_public_job_board_renders_listing(self):
        response = self.client.get(reverse("internship_list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Product Design Intern")
        self.assertContains(response, "Northstar Studio")

    def test_job_board_filters_by_source(self):
        self.opportunity.source_name = "Remotive"
        self.opportunity.save(update_fields=["source_name"])
        response = self.client.get(reverse("internship_list"), {"source": "Remotive"})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Product Design Intern")


class CVAnalyzerTests(TestCase):
    def test_evidence_rich_resume_scores_above_thin_generic_text(self):
        strong = """
        Alex Candidate | alex@example.com | +230 5123 4567
        SUMMARY
        Data analyst using Python, SQL, Excel and Power BI.
        EXPERIENCE
        Automated weekly reporting with Python, saving 6 hours every week.
        Built 4 Power BI dashboards used by 25 team members.
        Analysed 50,000 records and improved data quality by 18 percent.
        EDUCATION
        Diploma in Data Analytics
        SKILLS
        Python, SQL, Excel, Power BI
        """
        weak = "Alex Candidate. Hardworking team player. References available on request."
        self.assertGreater(
            analyse_cv_text(strong)["overall_score"],
            analyse_cv_text(weak)["overall_score"],
        )

    def test_targeted_analysis_reports_skill_gaps(self):
        report = analyse_cv_text(
            "Junior developer with Python experience. SKILLS Python, Git",
            target_role="Junior Data Analyst",
            job_description="Use Python, SQL, Power BI and Excel for data analysis.",
        )
        self.assertIn("python", report["target"]["matched_skills"])
        self.assertIn("sql", report["target"]["missing_skills"])


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
    def test_checkout_creates_pending_payment_and_redirects(self, create_session):
        create_session.return_value = SimpleNamespace(
            id="cs_test_123",
            url="https://checkout.stripe.com/c/pay/cs_test_123",
        )
        response = self.client.post(reverse("create_payment"))
        self.assertEqual(response.status_code, 302)
        payment = Payment.objects.get(user=self.user)
        self.assertEqual(payment.status, "pending")
        self.assertEqual(payment.stripe_checkout_session_id, "cs_test_123")

    @patch("myapp.views.stripe.checkout.Session.retrieve")
    def test_unpaid_checkout_does_not_activate_premium(self, retrieve_session):
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
        self.client.get(reverse("payment_success"), {"session_id": "cs_unpaid"})
        self.user.userprofile.refresh_from_db()
        self.assertFalse(self.user.userprofile.is_premium)
