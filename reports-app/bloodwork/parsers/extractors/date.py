"""
Date extraction and parsing utilities.

Handles extraction of dates from PDF text and conversion to standard format.
"""
import re
from datetime import datetime, date
from typing import Optional, List
from bloodwork.config import DATE_PATTERNS, DATE_FORMATS


class DateExtractor:
    """Extract and parse dates from text."""

    def __init__(self, date_patterns: Optional[List[str]] = None, date_formats: Optional[List[str]] = None):
        """
        Initialize date extractor.

        Args:
            date_patterns: List of regex patterns to extract dates (uses defaults if None)
            date_formats: List of date format strings to try when parsing (uses defaults if None)
        """
        self.date_patterns = date_patterns or DATE_PATTERNS
        self.date_formats = date_formats or DATE_FORMATS

    def extract_date(self, text: str) -> Optional[date]:
        """
        Extract date from text using configured patterns.

        Args:
            text: Text to search for date

        Returns:
            date object if found and parsed, None otherwise
        """
        for pattern in self.date_patterns:
            match = re.search(pattern, text)
            if match:
                date_str = match.group(1).strip()
                parsed_date = self.parse_date(date_str)
                if parsed_date:
                    return parsed_date

        return None

    def parse_date(self, date_str: str) -> Optional[date]:
        """
        Parse date string to date object.

        Tries multiple date formats and returns the first successful parse.

        Args:
            date_str: Date string to parse

        Returns:
            date object if successfully parsed, None otherwise
        """
        if not date_str:
            return None

        # Remove time portion if present (e.g., "Jun 10 2025 08:07" -> "Jun 10 2025")
        date_str = re.sub(r'\s+\d{2}:\d{2}.*', '', date_str).strip()

        # Try each date format
        for fmt in self.date_formats:
            try:
                date_obj = datetime.strptime(date_str, fmt)
                return date_obj.date()
            except ValueError:
                continue

        # If all formats fail, return None
        return None

    @staticmethod
    def format_date(date_obj: date) -> str:
        """
        Format date object to ISO format string (YYYY-MM-DD).

        Args:
            date_obj: date object to format

        Returns:
            ISO format date string
        """
        return date_obj.isoformat()
