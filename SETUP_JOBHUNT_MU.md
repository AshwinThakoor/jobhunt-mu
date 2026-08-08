# JobHunt MU setup guide

JobHunt MU is a Django job-discovery platform for Mauritius jobs, internships,
graduate roles, remote work, and freelance projects. It keeps the original
source on every imported opportunity and directs candidates back to the
official listing.

## 1. What you need

- Windows 10 or 11
- Python 3.12 or 3.13 from <https://www.python.org/downloads/>
- Internet access for the importers
- A Stripe account if you want to charge for Premium
- Optional provider credentials for Jooble and Freelancer.com

Never paste secret keys into chat, source code, or Git. Store them only in the
local `.env` file and in your deployment provider's secret settings.

## 2. Create a clean Python environment

Open PowerShell and run:

```powershell
cd "C:\Users\lovyt\Downloads\Python\myproject - Copy"
py -3.13 -m venv .venv-jobhunt
.\.venv-jobhunt\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

If Python 3.13 is not installed, use `py -3.12` instead. The repository's old
`.venv` points to a Python installation that is no longer present, so the
separate `.venv-jobhunt` environment avoids overwriting it.

## 3. Configure the app

Create the local settings file:

```powershell
Copy-Item .env.example .env
```

Open `.env` and replace `DJANGO_SECRET_KEY` with a long random value. For local
testing, keep:

```dotenv
DJANGO_DEBUG=true
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1
```

SQLite is already the zero-configuration default. You do not need MySQL to run
the app locally.

## 4. Create the database

```powershell
python manage.py migrate
python manage.py createsuperuser
```

The superuser is optional, but it gives you access to `/admin/`.

## 5. Import jobs and company pictures

The default command imports public data from MyJob.mu, Jobs.mu, the official
Mauritius Jobs portal, and Remotive:

```powershell
python scrape_jobs.py --django --download-images
```

It also writes a reviewable `jobhunt_opportunities.csv`. Imports are
idempotent: running the same command again updates matching records instead of
creating duplicates.

Useful variations:

```powershell
# Faster test: maximum 10 records per source
python scrape_jobs.py --django --download-images --limit 10

# Only Mauritius sources
python scrape_jobs.py --sources myjob,jobsmu,govmu --django --download-images

# Only the remote feed
python scrape_jobs.py --sources remotive --django --download-images
```

## 6. Run JobHunt MU

```powershell
python manage.py runserver
```

Open <http://127.0.0.1:8000/>. The opportunity feed is available at
<http://127.0.0.1:8000/internships/>.

## 7. Enable Stripe payments

1. Create or sign in to your Stripe account at <https://dashboard.stripe.com/>.
2. Start in **test mode**.
3. Copy a fresh publishable key and secret key into `.env`.
4. Install the Stripe CLI from
   <https://docs.stripe.com/stripe-cli/install>.
5. While Django is running, forward Stripe test webhooks:

   ```powershell
   stripe listen --forward-to localhost:8000/payments/webhook/
   ```

6. Put the printed `whsec_...` signing secret in `STRIPE_WEBHOOK_SECRET`.
7. Restart Django after changing `.env`.
8. Test checkout with Stripe's test card `4242 4242 4242 4242`, any future
   expiry date, and any three-digit CVC.

The relevant `.env` settings are:

```dotenv
STRIPE_PUBLISHABLE_KEY=pk_test_replace_me
STRIPE_SECRET_KEY=sk_test_replace_me
STRIPE_WEBHOOK_SECRET=whsec_replace_me
PREMIUM_PRICE_CENTS=1999
PREMIUM_CURRENCY=usd
```

Before production, rotate any key that was previously placed in source code,
switch to live keys, use HTTPS, set `DJANGO_DEBUG=false`, and configure the
production webhook URL.

## 8. Optional source credentials

### Jooble

Request an API key at <https://jooble.org/api/about>, then add it to `.env`:

```dotenv
JOOBLE_API_KEY=your_key_here
```

Run:

```powershell
python scrape_jobs.py --sources jooble --django
```

### Freelancer.com

Create an approved API application through
<https://developers.freelancer.com/>, obtain an OAuth token, and add:

```dotenv
FREELANCER_OAUTH_TOKEN=your_token_here
```

Run:

```powershell
python scrape_jobs.py --sources freelancer --django
```

### LinkedIn, Upwork, Toptal, and CareerHub

These platforms are included in the source directory as official outbound
destinations, but JobHunt MU does not scrape them:

- LinkedIn prohibits unauthorized scraping and its job posting API is
  restricted to approved partners.
- Upwork requires API approval, with commercial integrations limited to select
  partners.
- Toptal does not provide a general public job-feed API; talent applies through
  its network.
- CareerHub needs written permission or an official feed/API before automatic
  importing should be enabled.

If one of these platforms approves you, keep the credentials private and add a
connector that follows its official API terms.

## 9. Schedule daily updates

`update_internships.bat` uses `.venv-jobhunt` when it exists.

1. Search Windows for **Task Scheduler**.
2. Choose **Create Basic Task**.
3. Set the trigger to **Daily**.
4. Choose **Start a program**.
5. Select:
   `C:\Users\lovyt\Downloads\Python\myproject - Copy\update_internships.bat`
6. Set **Start in** to:
   `C:\Users\lovyt\Downloads\Python\myproject - Copy`

For unattended scheduling, remove the final `pause` line from the batch file
after you have confirmed the importer works on your computer.

## 10. Production checklist

- Use PostgreSQL or MySQL instead of SQLite.
- Set a strong `DJANGO_SECRET_KEY`.
- Set `DJANGO_DEBUG=false`.
- Add only your real domain to `DJANGO_ALLOWED_HOSTS`.
- Serve the site through HTTPS.
- Store secrets in the hosting provider, not in `.env` committed to Git.
- Run `python manage.py collectstatic`.
- Configure persistent media storage for downloaded company logos and uploads.
- Configure Stripe live keys and the production webhook.
- Schedule `scrape_jobs.py` daily with your host's scheduler.
- Review each provider's current API, attribution, and redistribution terms.


## AI Career Foundation (Phase 1)

After updating the code, run:

```powershell
python manage.py migrate
python manage.py test
python manage.py runserver
```

New features: secure PDF/DOCX CV parsing, detected skills, explainable resume-to-job matching, recommendation feedback, saved jobs, profile completion, and an interactive application dashboard. Match percentages are compatibility estimates, not hiring predictions.

## Import the complete MyJob.mu catalogue

The normal importer keeps a per-source safety cap. To fetch every currently available
page from MyJob.mu while keeping the other source caps controlled, run:

```powershell
python scrape_jobs.py --django --download-images --myjob-all
```

This imports all public job types (full-time, part-time, contract, internship,
trainee and others), follows the MyJob.mu API pagination until there is no next
page, updates existing records by external ID, and creates new records without
duplicating previous imports. The command can take several minutes because it
loads each job detail and optional company logo.

Use a temporary cap during development when needed:

```powershell
python scrape_jobs.py --django --download-images --myjob-limit 100
```



## Phase 1.3 data-quality commands

Complete refresh with safe missing-job archiving:

```powershell
python scrape_jobs.py --django --download-images --myjob-all --archive-missing
```

Preview stale/expired cleanup:

```powershell
python manage.py archive_stale_jobs --days 14 --dry-run
```

Apply cleanup:

```powershell
python manage.py archive_stale_jobs --days 14
```

Importer health and counts are available in Django Admin under **Import runs**.

## Phase 1.4 — Application Studio

After installing this version, run:

```powershell
python manage.py migrate
python manage.py test
python manage.py runserver
```

Migration `0011_career_document` stores editable application drafts.

Open any job and choose **Analyse & prepare application**. Basic users receive the explainable match and improvement plan. Premium users can generate, edit, save and download DOCX drafts for a tailored resume, cover letter and application email. Every generated document must be reviewed; the generator only uses information already present in the user's CV/profile and does not guarantee hiring outcomes.
