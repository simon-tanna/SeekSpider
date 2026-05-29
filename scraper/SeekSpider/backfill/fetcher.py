"""
Job description fetcher using Seek's GraphQL API.

The public job detail page (https://www.seek.com.au/job/<id>) is behind
Cloudflare and returns 403 from datacenter IPs, which made the previous
browser-based backfill fail on every job. Seek's GraphQL endpoint returns the
same job description as JSON without a Cloudflare challenge, so we fetch from it
directly — no browser, no chromedriver, no anti-detection needed.
"""

import logging
from typing import Optional, Tuple

import requests

GRAPHQL_URL = "https://www.seek.com.au/graphql"

# Minimal query: the description content plus the location label (suburb).
_QUERY = (
    "query jobDetails($jobId: ID!) { "
    "jobDetails(id: $jobId) { job { title content(platform: WEB) location { label } } } "
    "}"
)

_HEADERS = {
    "Content-Type": "application/json",
    "Accept": "application/json",
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4.1 Safari/605.1.15"
    ),
}

# Statuses worth retrying (transient); everything else is terminal for the job.
TRANSIENT_STATUSES = frozenset({"timeout", "rate_limited", "http_error", "request_error"})


def fetch_job_detail(
    job_id: str,
    timeout: float = 30.0,
    session: Optional[requests.Session] = None,
    logger: Optional[logging.Logger] = None,
) -> Tuple[Optional[str], Optional[str], str]:
    """Fetch (description_html, suburb, status) for a job via Seek's GraphQL API.

    status is one of: 'success', 'no_description', 'not_found', 'rate_limited',
    'http_error', 'request_error', 'timeout', 'graphql_error', 'invalid_json'.
    """
    http = session or requests
    payload = {
        "operationName": "jobDetails",
        "variables": {"jobId": str(job_id)},
        "query": _QUERY,
    }

    try:
        resp = http.post(GRAPHQL_URL, json=payload, headers=_HEADERS, timeout=timeout)
    except requests.Timeout:
        return None, None, "timeout"
    except requests.RequestException as e:
        if logger:
            logger.warning(f"  Request error for job {job_id}: {e}")
        return None, None, "request_error"

    if resp.status_code == 429:
        return None, None, "rate_limited"
    if resp.status_code != 200:
        return None, None, "http_error"

    try:
        body = resp.json()
    except ValueError:
        return None, None, "invalid_json"

    errors = body.get("errors")
    if errors:
        # Seek signals rate limiting as HTTP 200 with a RATE_LIMITED error in the
        # body (not an HTTP 429), so treat that as transient/retryable.
        if any(
            (e.get("extensions") or {}).get("code") == "RATE_LIMITED"
            or "too many requests" in str(e.get("message", "")).lower()
            for e in errors
        ):
            return None, None, "rate_limited"
        if logger:
            logger.warning(f"  GraphQL errors for job {job_id}: {errors}")
        return None, None, "graphql_error"

    details = (body.get("data") or {}).get("jobDetails") or {}
    job = details.get("job")
    if not job:
        return None, None, "not_found"

    content = job.get("content")
    suburb = (job.get("location") or {}).get("label")

    if not content:
        return None, None, "no_description"

    return content, suburb, "success"
