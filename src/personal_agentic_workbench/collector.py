"""Public-safe reconstruction: six recoverable fields from a synthetic page.

The original cross-device crawler source and its exact 14-field schema are not
present here. This module is not represented as the original crawler.
"""

from __future__ import annotations

from html.parser import HTMLParser
from pathlib import Path

from .core import validate_job

FIELDS = ("company", "title", "city", "description", "source_url", "deadline")


class _FixtureParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.values: dict[str, str] = {}
        self.active: str | None = None

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attrs_dict = dict(attrs)
        field = attrs_dict.get("data-field")
        if field in FIELDS:
            self.active = field
            if field == "source_url" and attrs_dict.get("href"):
                self.values[field] = attrs_dict["href"] or ""

    def handle_data(self, data: str) -> None:
        if self.active and self.active != "source_url":
            self.values[self.active] = self.values.get(self.active, "") + data

    def handle_endtag(self, tag: str) -> None:
        self.active = None


def extract_fixture_html(html: str) -> dict:
    """Dependency-free offline fixture extraction used by the default demo."""
    parser = _FixtureParser()
    parser.feed(html)
    return validate_job(parser.values)


def extract_with_playwright(html_path: Path) -> dict:
    """Optional real browser path; local synthetic HTML only, no account access."""
    try:
        from playwright.sync_api import sync_playwright
    except ImportError as exc:
        raise RuntimeError("Install the optional browser extra: pip install -e .[browser]") from exc
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        try:
            page = browser.new_page()
            page.goto(Path(html_path).resolve().as_uri())
            values = {}
            for field in FIELDS:
                locator = page.locator(f'[data-field="{field}"]')
                if locator.count():
                    values[field] = (locator.get_attribute("href") if field == "source_url" else locator.inner_text()) or ""
            return validate_job(values)
        finally:
            browser.close()
