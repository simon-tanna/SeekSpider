"""
Backfill module for fetching missing job descriptions.

This module provides tools for backfilling job descriptions that are missing
from the database, fetching them from Seek's GraphQL API (which bypasses the
Cloudflare-protected HTML job page).

Usage:
    # As a module
    from backfill import JobDescriptionBackfiller, BackfillConfig

    config = BackfillConfig(workers=3, region_filter='Sydney')
    backfiller = JobDescriptionBackfiller(config)
    backfiller.run(limit=100)

    # As a CLI command
    python -m backfill --region Sydney --limit 100
"""

from .config import BackfillConfig, DEFAULT_CONFIG
from .core import JobDescriptionBackfiller
from .fetcher import fetch_job_detail
from .ai_processor import BackfillAIProcessor, run_post_ai_analysis

__all__ = [
    'JobDescriptionBackfiller',
    'BackfillConfig',
    'DEFAULT_CONFIG',
    'fetch_job_detail',
    'BackfillAIProcessor',
    'run_post_ai_analysis',
]

__version__ = '1.0.0'
