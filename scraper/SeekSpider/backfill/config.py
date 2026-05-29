"""
Backfill module configuration and default parameters.
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class BackfillConfig:
    """Configuration for job description backfill (GraphQL API based)"""

    # Processing settings
    delay: float = 5.0  # Base delay between requests in seconds
    workers: int = 3  # Number of concurrent worker threads (1-5)
    limit: Optional[int] = None  # Maximum jobs to process (None = no limit)

    # HTTP settings
    request_timeout: float = 30.0  # Per-request timeout in seconds
    max_job_retries: int = 2  # Max retries for a single job on transient failures

    # Filtering
    region_filter: Optional[str] = None  # Filter jobs by region
    include_inactive: bool = False  # Include inactive jobs

    # AI settings
    enable_async_ai: bool = True  # Enable async AI analysis
    skip_ai_post: bool = False  # Skip AI analysis after backfill

    # Output
    region: Optional[str] = None  # Region for output organization

    def validate(self):
        """Validate configuration values"""
        if self.workers < 1 or self.workers > 5:
            raise ValueError("workers must be between 1 and 5")
        if self.delay < 0.5 or self.delay > 30.0:
            raise ValueError("delay must be between 0.5 and 30.0")
        if self.limit is not None and self.limit < 1:
            raise ValueError("limit must be at least 1")


# Default configuration instance
DEFAULT_CONFIG = BackfillConfig()
