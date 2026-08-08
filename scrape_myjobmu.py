"""Scrape complete MyJob.mu internship records and optionally sync Django.

MyJob.mu exposes its public job board as structured JSON. Using that feed is
more reliable than guessing CSS selectors, and it includes company logos,
closing dates, tags and the complete HTML job description.
"""

from __future__ import annotations

import argparse
import csv
import os
import re
import time
from datetime import date, datetime
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

API_ROOT = "https://app.myjob.mu/api/job-board"
SITE_ROOT = "https://www.myjob.mu"
DEFAULT_CSV_PATH = Path("interntrack_jobs.csv")
DEFAULT_MEDIA_ROOT = Path("media")
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/128.0.0.0 Safari/537.36"
)


def clean_text(value: Any) -> str:
    """Normalize whitespace and repair common UTF-8/Windows mojibake."""
    if value is None:
        return ""
    text = str(value)
    if any(marker in text for marker in ("Ã", "â€", "â€“", "â€”", "Â")):
        try:
            text = text.encode("latin-1").decode("utf-8")
        except (UnicodeEncodeError, UnicodeDecodeError):
            pass
    return re.sub(r"[ \t]+", " ", text).strip()


def parse_myjob_date(value: str | None) -> date | None:
    text = clean_text(value)
    text = re.sub(r"^(Posted|Closing)\s+", "", text, flags=re.IGNORECASE)
    for fmt in ("%b %d, %Y", "%d/%m/%Y", "%Y-%m-%d"):
        try:
            return datetime.strptime(text, fmt).date()
        except ValueError:
            continue
    return None


def _heading_bucket(line: str) -> str | None:
    normalized = re.sub(r"[^a-z ]", " ", line.lower())
    normalized = re.sub(r"\s+", " ", normalized).strip()
    if any(
        label in normalized
        for label in (
            "responsibilities",
            "responsibility",
            "duties",
            "your role",
            "what you will do",
        )
    ):
        return "responsibilities"
    if any(
        label in normalized
        for label in (
            "requirements",
            "qualifications",
            "who we are looking for",
            "what we are looking for",
            "your profile",
            "skills and experience",
        )
    ):
        return "requirements"
    if any(
        label in normalized
        for label in ("benefits", "what we offer", "why join", "perks")
    ):
        return "benefits"
    return None


def parse_description(description_html: str | None) -> dict[str, Any]:
    soup = BeautifulSoup(description_html or "", "html.parser")
    lines: list[str] = []
    for value in soup.stripped_strings:
        line = clean_text(value)
        if line and (not lines or line != lines[-1]):
            lines.append(line)

    sections: dict[str, list[str]] = {
        "requirements": [],
        "responsibilities": [],
        "benefits": [],
    }
    active_bucket: str | None = None
    for line in lines:
        bucket = _heading_bucket(line) if len(line) <= 100 else None
        if bucket:
            active_bucket = bucket
            continue
        if active_bucket:
            sections[active_bucket].append(line)

    return {
        "description": "\n".join(lines),
        "requirements": "\n".join(sections["requirements"]),
        "responsibilities": "\n".join(sections["responsibilities"]),
        "benefits": sections["benefits"],
    }


class MyJobScraper:
    def __init__(
        self,
        *,
        keyword: str = "",
        job_type: str = "Internship",
        pause: float = 0.35,
        timeout: float = 25,
        limit: int = 20,
    ) -> None:
        self.keyword = keyword.strip()
        self.job_type = job_type.strip()
        self.pause = max(0.0, pause)
        self.timeout = timeout
        self.limit = max(1, min(limit, 50))
        self.records: list[dict[str, Any]] = []
        self.session = requests.Session()
        retry = Retry(
            total=4,
            connect=4,
            read=4,
            backoff_factor=0.75,
            status_forcelist=(429, 500, 502, 503, 504),
            allowed_methods=("GET",),
        )
        self.session.mount("https://", HTTPAdapter(max_retries=retry))
        self.session.headers.update(
            {
                "User-Agent": USER_AGENT,
                "Accept": "application/ld+json, application/json;q=0.9",
            }
        )

    def _get_json(self, url: str, *, params: dict[str, Any] | None = None) -> dict:
        response = self.session.get(url, params=params, timeout=self.timeout)
        response.raise_for_status()
        return response.json()

    def _normalize_job(self, summary: dict, detail: dict) -> dict[str, Any]:
        payload = {**summary, **detail}
        company = payload.get("company") or {}
        category = payload.get("category") or {}
        tags = [
            clean_text(tag.get("label"))
            for tag in (payload.get("tags") or [])
            if clean_text(tag.get("label"))
        ]
        parsed = parse_description(payload.get("description"))
        if not parsed["requirements"] and tags:
            parsed["requirements"] = "\n".join(tags)

        job_id = str(payload.get("id") or "")
        slug = clean_text(payload.get("slug")) or "job"
        visible_salary = (
            clean_text(payload.get("salaryRange"))
            if payload.get("showSalary")
            else "Not disclosed"
        )
        return {
            "external_id": f"myjob:{job_id}",
            "source_name": "MyJob.mu",
            "source_url": f"{SITE_ROOT}/job/{job_id}/{slug}",
            "scraped_at": datetime.now().isoformat(timespec="seconds"),
            "job_title": clean_text(payload.get("title")) or "Untitled opportunity",
            "company": clean_text(company.get("name")) or "Confidential employer",
            "company_id": str(company.get("id") or ""),
            "company_slug": clean_text(company.get("slug")),
            "company_logo_url": clean_text(
                company.get("logo") or payload.get("logo")
            ),
            "industry": clean_text(category.get("name")),
            "location": clean_text(payload.get("location")) or "Mauritius",
            "job_type": clean_text(payload.get("jobType")) or self.job_type,
            "salary": visible_salary or "Not disclosed",
            "posted_date": parse_myjob_date(payload.get("postedAt")),
            "deadline": parse_myjob_date(payload.get("closingAt")),
            "skills": tags,
            "description": parsed["description"],
            "requirements": parsed["requirements"],
            "responsibilities": parsed["responsibilities"],
            "benefits": parsed["benefits"],
            "apply_url": clean_text(payload.get("applyUrl")),
        }

    def scrape(self, *, max_pages: int | None = None) -> list[dict[str, Any]]:
        self.records = []
        page = 1
        while True:
            params: dict[str, Any] = {
                "limit": self.limit,
                "sort": "latest",
                "page": page,
            }
            if self.keyword:
                params["keyword"] = self.keyword
            elif self.job_type:
                params["jobType"] = self.job_type

            print(f"Fetching MyJob.mu page {page}...")
            listing = self._get_json(f"{API_ROOT}/jobs", params=params)
            jobs = listing.get("hydra:member") or listing.get("member") or []
            if not jobs:
                break

            for summary in jobs:
                job_id = summary.get("id")
                try:
                    detail = self._get_json(f"{API_ROOT}/jobs/{job_id}")
                except requests.RequestException as exc:
                    print(f"  Detail request failed for job {job_id}: {exc}")
                    detail = {}
                self.records.append(self._normalize_job(summary, detail))
                if self.pause:
                    time.sleep(self.pause)

            view = listing.get("hydra:view") or {}
            has_next = bool(view.get("hydra:next"))
            if not has_next or (max_pages and page >= max_pages):
                break
            page += 1

        return self.records

    def download_logo(self, record: dict[str, Any], media_root: Path) -> Path | None:
        logo_url = record.get("company_logo_url")
        company_id = record.get("company_id")
        if not logo_url or not company_id:
            return None

        response = self.session.get(logo_url, timeout=self.timeout)
        response.raise_for_status()
        if len(response.content) > 5 * 1024 * 1024:
            raise ValueError(f"Logo for {record['company']} is larger than 5 MB")

        content_type = response.headers.get("Content-Type", "").split(";")[0]
        extension = {
            "image/jpeg": ".jpg",
            "image/png": ".png",
            "image/webp": ".webp",
            "image/gif": ".gif",
            "image/svg+xml": ".svg",
        }.get(content_type)
        if not extension:
            extension = Path(urlparse(logo_url).path).suffix.lower()
        if extension not in {".jpg", ".jpeg", ".png", ".webp", ".gif", ".svg"}:
            extension = ".png"

        logo_dir = media_root / "company_logos"
        logo_dir.mkdir(parents=True, exist_ok=True)
        logo_path = logo_dir / f"myjob-{company_id}{extension}"
        temporary_path = logo_path.with_suffix(logo_path.suffix + ".tmp")
        temporary_path.write_bytes(response.content)
        temporary_path.replace(logo_path)
        return logo_path

    def save_csv(self, path: Path = DEFAULT_CSV_PATH) -> None:
        if not self.records:
            print("No jobs were collected; CSV was not changed.")
            return

        fieldnames = list(self.records[0].keys())
        with path.open("w", newline="", encoding="utf-8-sig") as handle:
            writer = csv.DictWriter(handle, fieldnames=fieldnames)
            writer.writeheader()
            for record in self.records:
                row = dict(record)
                for key in ("posted_date", "deadline"):
                    row[key] = row[key].isoformat() if row[key] else ""
                for key in ("skills", "benefits"):
                    row[key] = " | ".join(row[key])
                writer.writerow(row)
        print(f"Saved {len(self.records)} complete jobs to {path}")

    def sync_django(
        self,
        *,
        download_images: bool = False,
        media_root: Path = DEFAULT_MEDIA_ROOT,
    ) -> tuple[int, int]:
        os.environ.setdefault("DJANGO_SETTINGS_MODULE", "myproject.settings")
        import django

        django.setup()

        from django.conf import settings
        from django.utils import timezone
        from myapp.models import Company, Internship

        created_count = 0
        updated_count = 0
        media_root = Path(settings.MEDIA_ROOT) if settings.MEDIA_ROOT else media_root

        for record in self.records:
            company, _ = Company.objects.get_or_create(
                name=record["company"],
                defaults={
                    "description": (
                        f"Latest opportunities from {record['company']} on MyJob.mu."
                    ),
                    "location": record["location"],
                    "industry": record["industry"] or "Other",
                    "website": (
                        f"{SITE_ROOT}/companies/{record['company_id']}/"
                        f"{record['company_slug']}"
                    ),
                    "logo_source_url": record["company_logo_url"] or None,
                },
            )
            changed_company_fields: list[str] = []
            for field, value in (
                ("location", record["location"]),
                ("industry", record["industry"] or company.industry),
                ("logo_source_url", record["company_logo_url"] or company.logo_source_url),
            ):
                if value and getattr(company, field) != value:
                    setattr(company, field, value)
                    changed_company_fields.append(field)

            if download_images and record["company_logo_url"]:
                try:
                    logo_path = self.download_logo(record, media_root)
                except (requests.RequestException, OSError, ValueError) as exc:
                    print(f"  Logo download failed for {record['company']}: {exc}")
                else:
                    if logo_path:
                        relative_logo = logo_path.relative_to(media_root).as_posix()
                        if company.logo.name != relative_logo:
                            company.logo.name = relative_logo
                            changed_company_fields.append("logo")
            if changed_company_fields:
                company.save(update_fields=list(dict.fromkeys(changed_company_fields)))

            deadline = record["deadline"]
            status = "closed" if deadline and deadline < date.today() else "active"
            defaults = {
                "company": company,
                "title": record["job_title"],
                "description": record["description"] or "See the original listing for details.",
                "requirements": record["requirements"] or "See the full job description.",
                "responsibilities": record["responsibilities"] or "See the full job description.",
                "location": record["location"],
                "duration": record["job_type"],
                "job_type": record["job_type"],
                "opportunity_type": "internship",
                "work_mode": "onsite",
                "stipend": record["salary"],
                "skills_required": record["skills"],
                "benefits": record["benefits"],
                "application_deadline": deadline,
                "posted_date": record["posted_date"],
                "status": status,
                "source_name": record["source_name"],
                "source_url": record["source_url"],
                "scraped_at": timezone.now(),
            }
            _, created = Internship.objects.update_or_create(
                external_id=record["external_id"],
                defaults=defaults,
            )
            created_count += int(created)
            updated_count += int(not created)

        print(
            f"Django sync complete: {created_count} created, "
            f"{updated_count} updated."
        )
        return created_count, updated_count


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Collect complete MyJob.mu listings, logos and descriptions."
    )
    parser.add_argument(
        "--keyword",
        default="",
        help="Optional keyword. When omitted, all internship-type jobs are fetched.",
    )
    parser.add_argument("--job-type", default="Internship")
    parser.add_argument("--pages", type=int, default=0, help="0 fetches every page.")
    parser.add_argument("--limit", type=int, default=20, help="Jobs per API page.")
    parser.add_argument("--pause", type=float, default=0.35)
    parser.add_argument("--csv", type=Path, default=DEFAULT_CSV_PATH)
    parser.add_argument(
        "--django",
        action="store_true",
        help="Create or update Company and Internship records.",
    )
    parser.add_argument(
        "--download-images",
        action="store_true",
        help="Download company logos into Django media storage.",
    )
    return parser


def cli() -> None:
    args = build_parser().parse_args()
    scraper = MyJobScraper(
        keyword=args.keyword,
        job_type=args.job_type,
        pause=args.pause,
        limit=args.limit,
    )
    scraper.scrape(max_pages=args.pages or None)
    scraper.save_csv(args.csv)
    if args.django:
        scraper.sync_django(download_images=args.download_images)


if __name__ == "__main__":
    cli()
