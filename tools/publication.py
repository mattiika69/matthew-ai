"""Small shared helpers for public source metadata and publication review."""
import re
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse


def sanitized_url(value):
    """Remove queries/fragments except well-defined public YouTube locators.

    Full URLs belong in the ignored raw manifest. Arbitrary share tokens must not
    become public merely because a source was labelled public.
    """
    if value is None:
        return None
    parsed = urlparse(value)
    if parsed.scheme not in ("http", "https") or not parsed.netloc or parsed.username or parsed.password:
        raise ValueError("Use an original HTTP(S) source URL without embedded credentials, or omit it.")
    allowed = []
    if parsed.hostname in ("youtube.com", "www.youtube.com", "m.youtube.com", "youtu.be"):
        for key, item in parse_qsl(parsed.query, keep_blank_values=True):
            if key == "v" and re.fullmatch(r"[A-Za-z0-9_-]{11}", item):
                allowed.append((key, item))
            elif key in ("t", "start", "end") and re.fullmatch(r"(?:\d+h)?(?:\d+m)?\d+s?|\d+", item):
                allowed.append((key, item))
    return urlunparse((parsed.scheme, parsed.netloc, parsed.path, parsed.params, urlencode(allowed), ""))


def public_record(record):
    """Keep private capture metadata out of the public catalog until reviewed."""
    result = dict(record)
    result["url"] = sanitized_url(record.get("url"))
    if record["visibility"] == "private":
        result.update(type="unreviewed-source", title=f"Unreviewed source {record['id']}",
                      url=None, date=None, author="Withheld pending review", topics=[],
                      capture_method="withheld-pending-review", coverage="Withheld pending review")
    return result


def validate_public_metadata(records):
    for record in records:
        source_id = record["id"]
        if record.get("publication_status") != "cleared":
            raise ValueError(f"Source metadata and curated material require deliberate public-distribution review: {source_id}")
        for key, value in record.items():
            if value is not None and (key == "url" or key.endswith("_url")):
                if not isinstance(value, str) or sanitized_url(value) != value:
                    raise ValueError(f"Public source URL must be sanitized and credential-free: {source_id}.{key}")
