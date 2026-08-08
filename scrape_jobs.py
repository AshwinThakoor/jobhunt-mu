"""JobHunt MU multi-source opportunity importer.

Automatic sources:
  - MyJob.mu public job-board JSON
  - Jobs.mu published RSS + schema.org JobPosting detail
  - Mauritius Jobs official public employment search
  - Remotive public remote-jobs API

Optional credential-based sources:
  - Jooble REST API (JOOBLE_API_KEY)
  - Freelancer.com official API (FREELANCER_OAUTH_TOKEN)

LinkedIn, Upwork, Toptal and CareerHub are intentionally presented as official
outbound destinations in the website. Their content is not scraped.
"""

from __future__ import annotations

import argparse
import csv
import html
import json
import os
import re
import time
from abc import ABC, abstractmethod
from datetime import date, datetime, timezone as datetime_timezone
from email.utils import parsedate_to_datetime
from pathlib import Path
from typing import Any
from urllib.parse import urlparse
from xml.etree import ElementTree

import requests
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from scrape_myjobmu import MyJobScraper, clean_text, parse_description

DEFAULT_SOURCES = ("myjob", "jobsmu", "govmu", "remotive")
DEFAULT_CSV_PATH = Path("jobhunt_opportunities.csv")
USER_AGENT = "JobHuntMU/1.0 (+https://localhost; public-job-aggregator)"


def parse_iso_date(value: Any) -> date | None:
    text = clean_text(value)
    if not text:
        return None
    text = text.replace("Z", "+00:00")
    try:
        return datetime.fromisoformat(text).date()
    except ValueError:
        pass
    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%b %d, %Y"):
        try:
            return datetime.strptime(text, fmt).date()
        except ValueError:
            continue
    try:
        return parsedate_to_datetime(text).date()
    except (TypeError, ValueError, OverflowError):
        return None


def text_from_html(value: Any) -> str:
    decoded = html.unescape(clean_text(value))
    return clean_text(BeautifulSoup(decoded, "html.parser").get_text(" ", strip=True))


def classify_opportunity(
    title: str,
    job_type: str,
    *,
    remote: bool = False,
    freelance: bool = False,
) -> str:
    combined = f"{title} {job_type}".lower()
    if freelance or any(word in combined for word in ("freelance", "project-based")):
        return "freelance"
    if any(word in combined for word in ("intern", "trainee", "apprentice")):
        return "internship"
    if any(word in combined for word in ("graduate", "entry level", "junior")):
        return "graduate"
    if remote:
        return "remote"
    return "local"


def make_session() -> requests.Session:
    session = requests.Session()
    retry = Retry(
        total=4,
        connect=4,
        read=4,
        backoff_factor=0.75,
        status_forcelist=(429, 500, 502, 503, 504),
        allowed_methods=("GET", "POST"),
    )
    session.mount("https://", HTTPAdapter(max_retries=retry))
    session.headers.update(
        {
            "User-Agent": USER_AGENT,
            "Accept": "application/json, application/ld+json, text/html, application/rss+xml;q=0.9",
        }
    )
    return session


class JobSource(ABC):
    slug = ""
    name = ""
    credential_env: str | None = None

    def __init__(self, session: requests.Session, *, limit: int = 40) -> None:
        self.session = session
        self.limit = max(1, limit)

    @property
    def available(self) -> bool:
        return not self.credential_env or bool(os.getenv(self.credential_env))

    @abstractmethod
    def fetch(self) -> list[dict[str, Any]]:
        raise NotImplementedError


class MyJobSource(JobSource):
    slug = "myjob"
    name = "MyJob.mu"

    def fetch(self) -> list[dict[str, Any]]:
        # Fetch the complete public MyJob.mu job board, not only internships.
        # The API supports pagination and a maximum page size of 50.
        scraper = MyJobScraper(job_type="", pause=0.1, limit=50)
        records = scraper.scrape(max_pages=None)
        for record in records:
            combined = " ".join(
                str(record.get(key) or "")
                for key in ("job_title", "job_type", "description", "location")
            ).lower()
            is_remote = any(token in combined for token in ("remote", "work from home", "teletravail", "télétravail"))
            is_hybrid = "hybrid" in combined or "hybride" in combined
            record["opportunity_type"] = classify_opportunity(
                record.get("job_title", ""),
                record.get("job_type", ""),
                remote=is_remote,
            )
            record["work_mode"] = "hybrid" if is_hybrid else ("remote" if is_remote else "onsite")
            record["company_url"] = (
                f"https://www.myjob.mu/companies/{record.get('company_id')}/"
                f"{record.get('company_slug')}"
            )
        return records[: self.limit] if self.limit else records


class JobsMuSource(JobSource):
    slug = "jobsmu"
    name = "Jobs.mu"
    rss_url = "https://www.jobs.mu/rss/"

    def _job_posting(self, url: str) -> tuple[dict[str, Any], str]:
        response = self.session.get(url, timeout=25)
        if response.status_code == 404:
            legacy_match = re.search(r"/display-job/(\d+)/([^/?#]+)", url)
            if legacy_match:
                slug = re.sub(
                    r"[^a-z0-9]+",
                    "-",
                    legacy_match.group(2).removesuffix(".html").lower(),
                ).strip("-")
                current_url = (
                    f"https://www.jobs.mu/job/{legacy_match.group(1)}/{slug}/"
                )
                response = self.session.get(current_url, timeout=25)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        canonical = soup.find("link", rel="canonical")
        canonical_url = canonical.get("href") if canonical else response.url
        for script in soup.select('script[type="application/ld+json"]'):
            try:
                payload = json.loads(script.get_text(strip=True))
            except (json.JSONDecodeError, TypeError):
                continue
            candidates = payload if isinstance(payload, list) else [payload]
            for candidate in candidates:
                if isinstance(candidate, dict) and candidate.get("@type") == "JobPosting":
                    return candidate, canonical_url
        return {}, canonical_url

    def fetch(self) -> list[dict[str, Any]]:
        response = self.session.get(self.rss_url, timeout=25)
        response.raise_for_status()
        # Jobs.mu currently emits a UTF-8 BOM/leading whitespace before the XML
        # declaration, which strict XML parsers reject unless it is normalized.
        feed_xml = response.content.decode("utf-8-sig").lstrip()
        root = ElementTree.fromstring(feed_xml)
        records: list[dict[str, Any]] = []

        for item in root.findall("./channel/item")[: self.limit]:
            feed_title = clean_text(item.findtext("title"))
            feed_url = clean_text(item.findtext("link"))
            feed_description = item.findtext("description") or ""
            try:
                posting, canonical_url = self._job_posting(feed_url)
            except requests.RequestException as exc:
                print(f"  Jobs.mu detail failed for {feed_title}: {exc}")
                posting, canonical_url = {}, feed_url

            identifier = posting.get("identifier") or {}
            external_value = clean_text(identifier.get("value"))
            if not external_value:
                match = re.search(r"/(\d+)/", feed_url)
                external_value = match.group(1) if match else feed_url

            company_data = posting.get("hiringOrganization") or {}
            address = ((posting.get("jobLocation") or {}).get("address") or {})
            job_type = clean_text(posting.get("employmentType")).replace("_", " ").title()
            raw_description = posting.get("description") or feed_description
            parsed = parse_description(html.unescape(str(raw_description)))
            if not parsed["description"]:
                parsed["description"] = text_from_html(feed_description)

            title = clean_text(posting.get("title")) or feed_title
            company = clean_text(company_data.get("name")) or "Jobs.mu employer"
            opportunity_type = classify_opportunity(title, job_type)
            records.append(
                {
                    "external_id": f"jobsmu:{external_value}",
                    "source_name": self.name,
                    "source_url": canonical_url,
                    "scraped_at": datetime.now().isoformat(timespec="seconds"),
                    "job_title": title,
                    "company": company,
                    "company_id": external_value,
                    "company_slug": "",
                    "company_url": "",
                    "company_logo_url": clean_text(company_data.get("logo")),
                    "industry": "",
                    "location": clean_text(
                        address.get("addressLocality") or address.get("addressRegion")
                    )
                    or "Mauritius",
                    "job_type": job_type or "Job",
                    "opportunity_type": opportunity_type,
                    "work_mode": "onsite",
                    "salary": "Not disclosed",
                    "posted_date": parse_iso_date(posting.get("datePosted") or item.findtext("pubDate")),
                    "deadline": parse_iso_date(posting.get("validThrough")),
                    "skills": [],
                    "description": parsed["description"],
                    "requirements": parsed["requirements"],
                    "responsibilities": parsed["responsibilities"],
                    "benefits": parsed["benefits"],
                    "apply_url": canonical_url,
                }
            )
            time.sleep(0.08)
        return records


class MauritiusGovSource(JobSource):
    slug = "govmu"
    name = "Mauritius Jobs"
    search_url = "https://mauritiusjobs.govmu.org/index.php/jobsearch"

    def fetch(self) -> list[dict[str, Any]]:
        response = self.session.post(
            self.search_url,
            data={
                "local": "1",
                "international": "",
                "district": "",
                "keyword": "",
                "jobtitle": "",
                "qualification": "",
                "sector": "",
            },
            timeout=40,
        )
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        table = soup.select_one("table.job_list")
        if not table:
            return []

        records: list[dict[str, Any]] = []
        for row in table.find_all("tr", recursive=False):
            onclick = row.get("onclick", "")
            match = re.search(r"jobdetails\('([^']+)'\)", onclick)
            cells = row.find_all("td", recursive=False)
            if not match or len(cells) < 6:
                continue
            job_id = match.group(1)
            detail_container = soup.find(id=job_id)
            details: dict[str, str] = {}
            if detail_container:
                for detail_row in detail_container.select("table.job_details tr"):
                    detail_cells = detail_row.find_all("td", recursive=False)
                    if len(detail_cells) >= 2:
                        details[clean_text(detail_cells[0].get_text(" ", strip=True))] = clean_text(
                            detail_cells[1].get_text("\n", strip=True)
                        )

            title = clean_text(cells[1].get_text(" ", strip=True))
            industry = clean_text(cells[2].get_text(" ", strip=True))
            company = clean_text(cells[3].get_text(" ", strip=True))
            deadline = parse_iso_date(cells[5].get_text(" ", strip=True))
            responsibilities = details.get("Duties of Job", "")
            requirements_parts = [
                value
                for key, value in details.items()
                if any(
                    marker in key.lower()
                    for marker in (
                        "qualification",
                        "competenc",
                        "experience",
                        "skill",
                        "education",
                    )
                )
            ]
            location = (
                details.get("District in Mauritius")
                or details.get("Country")
                or clean_text(cells[4].get_text(" ", strip=True))
                or "Mauritius"
            )
            job_type = details.get("Nature of Employment", "Local job")
            records.append(
                {
                    "external_id": f"govmu:{job_id}",
                    "source_name": self.name,
                    "source_url": f"https://mauritiusjobs.govmu.org/jobsearch#job-{job_id}",
                    "scraped_at": datetime.now().isoformat(timespec="seconds"),
                    "job_title": title,
                    "company": company or details.get("Employer", "Mauritius employer"),
                    "company_id": job_id,
                    "company_slug": "",
                    "company_url": "",
                    "company_logo_url": "",
                    "industry": industry,
                    "location": location,
                    "job_type": job_type,
                    "opportunity_type": classify_opportunity(title, job_type),
                    "work_mode": "onsite",
                    "salary": details.get("Salary", "Not disclosed"),
                    "posted_date": None,
                    "deadline": deadline,
                    "skills": [],
                    "description": details.get("Job Summary") or responsibilities,
                    "requirements": "\n".join(requirements_parts),
                    "responsibilities": responsibilities,
                    "benefits": [],
                    "apply_url": "https://mauritiusjobs.govmu.org/jobsearch",
                }
            )
            if len(records) >= self.limit:
                break
        return records


class RemotiveSource(JobSource):
    slug = "remotive"
    name = "Remotive"
    api_url = "https://remotive.com/api/remote-jobs"

    def fetch(self) -> list[dict[str, Any]]:
        response = self.session.get(
            self.api_url,
            params={"limit": min(self.limit, 100)},
            timeout=30,
        )
        response.raise_for_status()
        jobs = response.json().get("jobs") or []
        records: list[dict[str, Any]] = []
        for job in jobs[: self.limit]:
            parsed = parse_description(job.get("description"))
            tags = [clean_text(tag) for tag in (job.get("tags") or []) if clean_text(tag)]
            job_type = clean_text(job.get("job_type")) or "Remote"
            is_freelance = any(
                word in job_type.lower() for word in ("freelance", "contract")
            )
            records.append(
                {
                    "external_id": f"remotive:{job.get('id')}",
                    "source_name": self.name,
                    "source_url": clean_text(job.get("url")),
                    "scraped_at": datetime.now().isoformat(timespec="seconds"),
                    "job_title": clean_text(job.get("title")),
                    "company": clean_text(job.get("company_name")) or "Remote employer",
                    "company_id": str(job.get("id") or ""),
                    "company_slug": "",
                    "company_url": "",
                    "company_logo_url": clean_text(job.get("company_logo")),
                    "industry": clean_text(job.get("category")),
                    "location": clean_text(job.get("candidate_required_location")) or "Worldwide",
                    "job_type": job_type,
                    "opportunity_type": classify_opportunity(
                        clean_text(job.get("title")),
                        job_type,
                        remote=True,
                        freelance=is_freelance,
                    ),
                    "work_mode": "remote",
                    "salary": clean_text(job.get("salary")) or "Not disclosed",
                    "posted_date": parse_iso_date(job.get("publication_date")),
                    "deadline": None,
                    "skills": tags,
                    "description": parsed["description"],
                    "requirements": parsed["requirements"] or "\n".join(tags),
                    "responsibilities": parsed["responsibilities"],
                    "benefits": parsed["benefits"],
                    "apply_url": clean_text(job.get("url")),
                }
            )
        return records


class JoobleSource(JobSource):
    slug = "jooble"
    name = "Jooble"
    credential_env = "JOOBLE_API_KEY"

    def fetch(self) -> list[dict[str, Any]]:
        response = self.session.post(
            f"https://jooble.org/api/{os.environ[self.credential_env]}",
            json={
                "keywords": "",
                "location": "Mauritius",
                "page": "1",
                "ResultOnPage": str(min(self.limit, 50)),
            },
            timeout=30,
        )
        response.raise_for_status()
        records: list[dict[str, Any]] = []
        for job in (response.json().get("jobs") or [])[: self.limit]:
            description = text_from_html(job.get("snippet"))
            title = clean_text(job.get("title"))
            job_type = clean_text(job.get("type")) or "Job"
            records.append(
                {
                    "external_id": f"jooble:{job.get('id')}",
                    "source_name": self.name,
                    "source_url": clean_text(job.get("link")),
                    "scraped_at": datetime.now().isoformat(timespec="seconds"),
                    "job_title": title,
                    "company": clean_text(job.get("company")) or "Mauritius employer",
                    "company_id": str(job.get("id") or ""),
                    "company_slug": "",
                    "company_url": "",
                    "company_logo_url": "",
                    "industry": "",
                    "location": clean_text(job.get("location")) or "Mauritius",
                    "job_type": job_type,
                    "opportunity_type": classify_opportunity(title, job_type),
                    "work_mode": "unspecified",
                    "salary": clean_text(job.get("salary")) or "Not disclosed",
                    "posted_date": parse_iso_date(job.get("updated")),
                    "deadline": None,
                    "skills": [],
                    "description": description,
                    "requirements": "",
                    "responsibilities": "",
                    "benefits": [],
                    "apply_url": clean_text(job.get("link")),
                }
            )
        return records


class FreelancerSource(JobSource):
    slug = "freelancer"
    name = "Freelancer.com"
    credential_env = "FREELANCER_OAUTH_TOKEN"
    api_url = "https://www.freelancer.com/api/projects/0.1/projects/active/"

    def fetch(self) -> list[dict[str, Any]]:
        response = self.session.get(
            self.api_url,
            headers={
                "freelancer-oauth-v1": os.environ[self.credential_env],
            },
            params={
                "compact": "true",
                "limit": min(self.limit, 50),
                "full_description": "true",
                "job_details": "true",
            },
            timeout=30,
        )
        response.raise_for_status()
        projects = ((response.json().get("result") or {}).get("projects") or [])
        records: list[dict[str, Any]] = []
        for project in projects[: self.limit]:
            currency = ((project.get("budget") or {}).get("currency") or {}).get("code", "")
            budget = project.get("budget") or {}
            budget_text = " - ".join(
                str(value)
                for value in (budget.get("minimum"), budget.get("maximum"))
                if value is not None
            )
            if currency and budget_text:
                budget_text = f"{currency} {budget_text}"
            skills = [
                clean_text(job.get("name"))
                for job in (project.get("jobs") or [])
                if clean_text(job.get("name"))
            ]
            seo_url = clean_text(project.get("seo_url"))
            source_url = (
                f"https://www.freelancer.com/projects/{seo_url.lstrip('/')}"
                if seo_url
                else "https://www.freelancer.com/jobs/"
            )
            posted = project.get("submitdate") or project.get("time_submitted")
            posted_date = (
                datetime.fromtimestamp(int(posted), tz=datetime_timezone.utc).date()
                if posted
                else None
            )
            records.append(
                {
                    "external_id": f"freelancer:{project.get('id')}",
                    "source_name": self.name,
                    "source_url": source_url,
                    "scraped_at": datetime.now().isoformat(timespec="seconds"),
                    "job_title": clean_text(project.get("title")),
                    "company": "Freelancer client",
                    "company_id": str(project.get("owner_id") or ""),
                    "company_slug": "",
                    "company_url": "",
                    "company_logo_url": "",
                    "industry": "Freelance project",
                    "location": "Remote",
                    "job_type": clean_text(project.get("type")).title() or "Freelance",
                    "opportunity_type": "freelance",
                    "work_mode": "remote",
                    "salary": budget_text or "Budget not disclosed",
                    "posted_date": posted_date,
                    "deadline": None,
                    "skills": skills,
                    "description": clean_text(project.get("description")),
                    "requirements": "\n".join(skills),
                    "responsibilities": "",
                    "benefits": [],
                    "apply_url": source_url,
                }
            )
        return records


SOURCE_CLASSES = {
    cls.slug: cls
    for cls in (
        MyJobSource,
        JobsMuSource,
        MauritiusGovSource,
        RemotiveSource,
        JoobleSource,
        FreelancerSource,
    )
}


class MultiSourceImporter:
    def __init__(
        self,
        source_slugs: list[str],
        *,
        limit: int = 40,
        source_limits: dict[str, int] | None = None,
    ) -> None:
        self.source_slugs = source_slugs
        self.limit = limit
        self.source_limits = source_limits or {}
        self.session = make_session()
        self.records: list[dict[str, Any]] = []
        self.report: list[dict[str, Any]] = []

    def collect(self) -> list[dict[str, Any]]:
        self.records = []
        self.report = []
        for slug in self.source_slugs:
            source_class = SOURCE_CLASSES.get(slug)
            if not source_class:
                self.report.append({"source": slug, "status": "unknown", "count": 0})
                continue
            source_limit = self.source_limits.get(slug, self.limit)
            source = source_class(self.session, limit=source_limit)
            if not source.available:
                self.report.append(
                    {
                        "source": source.name,
                        "status": f"needs {source.credential_env}",
                        "count": 0,
                    }
                )
                print(f"Skipping {source.name}: set {source.credential_env} to enable it.")
                continue
            print(f"Fetching {source.name}...")
            try:
                records = source.fetch()
            except (requests.RequestException, ValueError, ElementTree.ParseError) as exc:
                self.report.append(
                    {"source": source.name, "status": f"failed: {exc}", "count": 0}
                )
                print(f"  {source.name} failed: {exc}")
                continue
            self.records.extend(records)
            self.report.append(
                {"source": source.name, "status": "ok", "count": len(records)}
            )
            print(f"  Collected {len(records)} opportunities.")
        return self.records

    def save_csv(self, path: Path = DEFAULT_CSV_PATH) -> None:
        if not self.records:
            print("No opportunities collected; CSV was not changed.")
            return
        fieldnames = [
            "external_id",
            "source_name",
            "source_url",
            "scraped_at",
            "job_title",
            "company",
            "company_id",
            "company_slug",
            "company_url",
            "company_logo_url",
            "industry",
            "location",
            "job_type",
            "opportunity_type",
            "work_mode",
            "salary",
            "posted_date",
            "deadline",
            "skills",
            "description",
            "requirements",
            "responsibilities",
            "benefits",
            "apply_url",
        ]
        with path.open("w", newline="", encoding="utf-8-sig") as handle:
            writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
            writer.writeheader()
            for record in self.records:
                row = dict(record)
                for key in ("posted_date", "deadline"):
                    row[key] = row[key].isoformat() if row.get(key) else ""
                for key in ("skills", "benefits"):
                    row[key] = " | ".join(row.get(key) or [])
                writer.writerow(row)
        print(f"Saved {len(self.records)} opportunities to {path}")

    def _download_logo(
        self,
        record: dict[str, Any],
        media_root: Path,
    ) -> Path | None:
        logo_url = record.get("company_logo_url")
        if not logo_url:
            return None
        response = self.session.get(logo_url, timeout=25)
        response.raise_for_status()
        if len(response.content) > 5 * 1024 * 1024:
            raise ValueError("logo exceeds 5 MB")

        content_type = response.headers.get("Content-Type", "").split(";")[0]
        extension = {
            "image/jpeg": ".jpg",
            "image/png": ".png",
            "image/webp": ".webp",
            "image/gif": ".gif",
            "image/svg+xml": ".svg",
        }.get(content_type, Path(urlparse(logo_url).path).suffix.lower() or ".png")
        if extension not in {".jpg", ".jpeg", ".png", ".webp", ".gif", ".svg"}:
            extension = ".png"
        source_slug = re.sub(r"[^a-z0-9]+", "-", record["source_name"].lower()).strip("-")
        safe_id = re.sub(r"[^a-zA-Z0-9_-]+", "-", record["external_id"])
        logo_dir = media_root / "company_logos"
        logo_dir.mkdir(parents=True, exist_ok=True)
        path = logo_dir / f"{source_slug}-{safe_id}{extension}"
        temporary = path.with_suffix(path.suffix + ".tmp")
        temporary.write_bytes(response.content)
        temporary.replace(path)
        return path

    def sync_django(self, *, download_images: bool = False, archive_missing: bool = False) -> tuple[int, int]:
        os.environ.setdefault("DJANGO_SETTINGS_MODULE", "myproject.settings")
        import django

        django.setup()

        from django.conf import settings
        from django.utils import timezone
        from myapp.models import Company, Internship, ImportRun

        created_count = 0
        updated_count = 0
        media_root = Path(settings.MEDIA_ROOT)
        now = timezone.now()
        records_by_source = {}
        for record in self.records:
            records_by_source.setdefault(record["source_name"], []).append(record)
        successful_sources = {item["source"] for item in self.report if item["status"] == "ok"}
        runs = {name: ImportRun.objects.create(source_name=name, status='running', fetched_count=len(records_by_source.get(name, []))) for name in successful_sources}
        source_counts = {name: {'created': 0, 'updated': 0} for name in successful_sources}

        for record in self.records:
            company, _ = Company.objects.get_or_create(
                name=record["company"],
                defaults={
                    "description": (
                        f"Opportunities from {record['company']}, listed via "
                        f"{record['source_name']}."
                    ),
                    "location": record["location"],
                    "industry": record["industry"] or "Other",
                    "website": record.get("company_url") or None,
                    "logo_source_url": record.get("company_logo_url") or None,
                },
            )
            company_updates: list[str] = []
            for field, value in (
                ("location", record["location"]),
                ("industry", record["industry"] or company.industry),
                ("website", record.get("company_url") or company.website),
                (
                    "logo_source_url",
                    record.get("company_logo_url") or company.logo_source_url,
                ),
            ):
                if value and getattr(company, field) != value:
                    setattr(company, field, value)
                    company_updates.append(field)

            if download_images and record.get("company_logo_url"):
                try:
                    logo_path = self._download_logo(record, media_root)
                except (requests.RequestException, OSError, ValueError) as exc:
                    print(f"  Logo failed for {record['company']}: {exc}")
                else:
                    if logo_path:
                        relative_logo = logo_path.relative_to(media_root).as_posix()
                        if company.logo.name != relative_logo:
                            company.logo.name = relative_logo
                            company_updates.append("logo")
            if company_updates:
                company.save(update_fields=list(dict.fromkeys(company_updates)))

            deadline = record.get("deadline")
            status = "closed" if deadline and deadline < date.today() else "active"
            defaults = {
                "company": company,
                "title": record["job_title"],
                "description": record.get("description") or "See the original listing.",
                "requirements": record.get("requirements") or "See the original listing.",
                "responsibilities": record.get("responsibilities") or "See the original listing.",
                "location": record["location"],
                "duration": record["job_type"],
                "job_type": record["job_type"],
                "opportunity_type": record["opportunity_type"],
                "work_mode": record["work_mode"],
                "stipend": record.get("salary") or "Not disclosed",
                "skills_required": record.get("skills") or [],
                "benefits": record.get("benefits") or [],
                "application_deadline": deadline,
                "posted_date": record.get("posted_date"),
                "status": status,
                "source_name": record["source_name"],
                "source_url": record["source_url"],
                "scraped_at": now,
                "last_seen_at": now,
                "last_checked_at": now,
                "source_status": "active",
                "expired_at": None,
            }
            job, created = Internship.objects.update_or_create(
                external_id=record["external_id"],
                defaults=defaults,
            )
            if created and not job.first_seen_at:
                job.first_seen_at = now
                job.save(update_fields=['first_seen_at'])
            created_count += int(created)
            updated_count += int(not created)
            counts = source_counts.setdefault(record['source_name'], {'created': 0, 'updated': 0})
            counts['created'] += int(created)
            counts['updated'] += int(not created)
        archived_total = 0
        for source_name, run in runs.items():
            archived = 0
            if archive_missing:
                seen_ids = {r['external_id'] for r in records_by_source.get(source_name, [])}
                stale = Internship.objects.filter(source_name=source_name, status='active').exclude(external_id__in=seen_ids)
                archived = stale.update(status='closed', source_status='missing', expired_at=now, last_checked_at=now)
                archived_total += archived
            counts = source_counts.get(source_name, {'created': 0, 'updated': 0})
            run.status = 'success'
            run.created_count = counts['created']; run.updated_count = counts['updated']; run.archived_count = archived
            run.finished_at = now
            run.save(update_fields=['status','created_count','updated_count','archived_count','finished_at'])
        print(
            f"Django sync complete: {created_count} created, "
            f"{updated_count} updated, {archived_total} archived."
        )
        return created_count, updated_count


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Collect Mauritius, remote and freelance opportunities for JobHunt MU."
    )
    parser.add_argument(
        "--sources",
        default=",".join(DEFAULT_SOURCES),
        help=(
            "Comma-separated: myjob,jobsmu,govmu,remotive,jooble,freelancer"
        ),
    )
    parser.add_argument("--limit", type=int, default=40, help="Maximum per source (except MyJob when --myjob-all is used).")
    parser.add_argument(
        "--myjob-all",
        action="store_true",
        help="Import every currently available page from the public MyJob.mu job board.",
    )
    parser.add_argument(
        "--myjob-limit",
        type=int,
        default=None,
        help="Optional MyJob.mu-only cap. Use 0 for every available job.",
    )
    parser.add_argument("--csv", type=Path, default=DEFAULT_CSV_PATH)
    parser.add_argument("--django", action="store_true")
    parser.add_argument("--download-images", action="store_true")
    parser.add_argument("--archive-missing", action="store_true", help="Close jobs not seen during a complete successful source refresh.")
    return parser


def cli() -> None:
    args = build_parser().parse_args()
    source_slugs = [
        value.strip().lower() for value in args.sources.split(",") if value.strip()
    ]
    source_limits: dict[str, int] = {}
    if args.myjob_all:
        source_limits["myjob"] = 0
    elif args.myjob_limit is not None:
        source_limits["myjob"] = max(0, args.myjob_limit)
    importer = MultiSourceImporter(
        source_slugs,
        limit=args.limit,
        source_limits=source_limits,
    )
    importer.collect()
    importer.save_csv(args.csv)
    if args.django:
        importer.sync_django(download_images=args.download_images, archive_missing=args.archive_missing)
    print("\nSource report:")
    for item in importer.report:
        print(f"  {item['source']}: {item['status']} ({item['count']})")


if __name__ == "__main__":
    cli()
