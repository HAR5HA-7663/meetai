"""Load personal context from the resume repository for AI prompt personalization."""

import os
import logging
from pathlib import Path
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

RESUME_DIR = os.path.expanduser("~/Desktop/resume")
HTML_DIR = os.path.join(RESUME_DIR, "resumes", "html")
PERSONAL_DETAILS = os.path.join(RESUME_DIR, "references", "personal_details.md")

PROFILE_MAP = {
    "sde": "sde_engineer.html",
    "ml": "ml_engineer.html",
    "devops": "devops_engineer.html",
    "ai_automation": "ai_automation_engineer.html",
    "java_fullstack": "java_fullstack.html",
    "general": "resume.html",
}


def _extract_text_from_html(html_path: str) -> str:
    """Parse HTML resume and extract readable text."""
    try:
        with open(html_path, "r", encoding="utf-8") as f:
            soup = BeautifulSoup(f.read(), "html.parser")
        # Remove style and script tags
        for tag in soup(["style", "script"]):
            tag.decompose()
        text = soup.get_text(separator="\n", strip=True)
        # Clean up excessive whitespace
        lines = [line.strip() for line in text.split("\n") if line.strip()]
        return "\n".join(lines)
    except Exception as e:
        logger.error(f"Failed to parse HTML resume {html_path}: {e}")
        return ""


def _load_personal_details() -> str:
    """Load personal_details.md as plain text."""
    try:
        if os.path.exists(PERSONAL_DETAILS):
            with open(PERSONAL_DETAILS, "r", encoding="utf-8") as f:
                return f.read()
    except Exception as e:
        logger.error(f"Failed to load personal details: {e}")
    return ""


def load_context(profile: str = "sde") -> str:
    """Load and combine personal context for AI prompts.

    Args:
        profile: Resume profile to use (sde, ml, devops, ai_automation, java_fullstack, general)

    Returns:
        Combined context string with personal info and resume content.
    """
    parts = []

    # Load personal details (always included)
    details = _load_personal_details()
    if details:
        # Extract just the key sections, not the full file
        parts.append("=== PERSONAL BACKGROUND ===")
        parts.append(details[:3000])  # First 3000 chars covers key info

    # Load appropriate resume
    html_file = PROFILE_MAP.get(profile, "resume.html")
    html_path = os.path.join(HTML_DIR, html_file)
    if os.path.exists(html_path):
        resume_text = _extract_text_from_html(html_path)
        if resume_text:
            parts.append("\n=== RESUME ===")
            parts.append(resume_text[:4000])  # Cap at 4000 chars
    else:
        logger.warning(f"Resume file not found: {html_path}")
        # Try fallback to general resume
        fallback = os.path.join(HTML_DIR, "resume.html")
        if os.path.exists(fallback):
            resume_text = _extract_text_from_html(fallback)
            if resume_text:
                parts.append("\n=== RESUME ===")
                parts.append(resume_text[:4000])

    context = "\n".join(parts)
    if context:
        logger.info(f"Loaded personal context ({len(context)} chars, profile={profile})")
    else:
        logger.warning("No personal context loaded")
    return context


def get_available_profiles() -> list[str]:
    """Return list of available resume profiles."""
    available = []
    for key, filename in PROFILE_MAP.items():
        if os.path.exists(os.path.join(HTML_DIR, filename)):
            available.append(key)
    return available
