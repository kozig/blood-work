"""
Default configuration values for blood work analysis.

This module contains default settings that can be overridden by
environment variables or configuration files.
"""
import os
from typing import Optional


class Config:
    """
    Configuration class for blood work analysis.

    All values can be overridden via environment variables.
    """

    # Database configuration
    DATABASE_URL: str = os.getenv(
        "BLOODWORK_DATABASE_URL",
        "postgresql://bloodwork:bloodwork@localhost/bloodwork"
    )

    # Parser configuration
    MAX_PDF_SIZE_MB: int = int(os.getenv("BLOODWORK_MAX_PDF_SIZE_MB", "50"))
    SUPPORTED_PDF_TYPES: list = ["application/pdf"]

    # Logging configuration
    LOG_LEVEL: str = os.getenv("BLOODWORK_LOG_LEVEL", "INFO")
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    # Result deduplication
    DEDUPLICATE_RESULTS: bool = os.getenv("BLOODWORK_DEDUPLICATE", "true").lower() == "true"

    # Privacy settings
    REDACT_PHI_IN_LOGS: bool = os.getenv("BLOODWORK_REDACT_PHI", "true").lower() == "true"

    # Validation settings
    MIN_TEST_NAME_LENGTH: int = int(os.getenv("BLOODWORK_MIN_TEST_NAME_LENGTH", "2"))
    REQUIRE_NUMERIC_RESULT: bool = os.getenv("BLOODWORK_REQUIRE_NUMERIC", "true").lower() == "true"

    # Visualization defaults
    DEFAULT_CHART_WIDTH: int = int(os.getenv("BLOODWORK_CHART_WIDTH", "800"))
    DEFAULT_CHART_HEIGHT: int = int(os.getenv("BLOODWORK_CHART_HEIGHT", "600"))

    @classmethod
    def from_env(cls) -> "Config":
        """
        Create configuration from environment variables.

        Returns:
            Config instance with values from environment
        """
        return cls()

    @classmethod
    def validate(cls) -> bool:
        """
        Validate configuration values.

        Returns:
            True if configuration is valid

        Raises:
            ValueError: If configuration is invalid
        """
        if cls.MAX_PDF_SIZE_MB < 1:
            raise ValueError("MAX_PDF_SIZE_MB must be at least 1")

        if cls.MIN_TEST_NAME_LENGTH < 1:
            raise ValueError("MIN_TEST_NAME_LENGTH must be at least 1")

        return True

    @classmethod
    def get_database_url(cls, default: Optional[str] = None) -> str:
        """
        Get database URL from environment or use default.

        Args:
            default: Default URL if not set in environment

        Returns:
            Database connection string
        """
        return os.getenv("BLOODWORK_DATABASE_URL", default or cls.DATABASE_URL)


# Module-level configuration instance
config = Config()
