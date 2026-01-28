"""
Configuration module for blood work analysis.

Provides default settings, lab-specific patterns, and environment-based configuration.
"""
from bloodwork.config.defaults import Config, config
from bloodwork.config.patterns import (
    LIFELABS_SECTIONS,
    DATE_PATTERNS,
    DATE_FORMATS,
    PATIENT_FIELD_PATTERNS,
    TEST_PATTERN_WITH_FLAG,
    TEST_PATTERN_NO_FLAG,
    should_skip_line
)

__all__ = [
    "Config",
    "config",
    "LIFELABS_SECTIONS",
    "DATE_PATTERNS",
    "DATE_FORMATS",
    "PATIENT_FIELD_PATTERNS",
    "TEST_PATTERN_WITH_FLAG",
    "TEST_PATTERN_NO_FLAG",
    "should_skip_line",
]
