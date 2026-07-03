"""
Enumerations for blood work data models.
"""
from enum import Enum


class ResultFlag(str, Enum):
    """Flag indicating if a test result is within normal range."""
    NORMAL = "NORMAL"
    HIGH = "HIGH"
    LOW = "LOW"

    @classmethod
    def from_lifelabs(cls, flag_str: str) -> "ResultFlag":
        """Convert LifeLabs flag format (HI/LO) to ResultFlag."""
        if not flag_str or flag_str.strip() == "":
            return cls.NORMAL

        flag_upper = flag_str.strip().upper()
        if flag_upper == "HI":
            return cls.HIGH
        elif flag_upper == "LO":
            return cls.LOW
        else:
            return cls.NORMAL


class TestCategory(str, Enum):
    """Categories of blood tests for grouping and analysis."""
    LIPID_PANEL = "LIPID_PANEL"
    LIVER_FUNCTION = "LIVER_FUNCTION"
    COMPLETE_BLOOD_COUNT = "COMPLETE_BLOOD_COUNT"
    HORMONES = "HORMONES"
    THYROID = "THYROID"
    METABOLIC_PANEL = "METABOLIC_PANEL"
    KIDNEY_FUNCTION = "KIDNEY_FUNCTION"
    VITAMINS = "VITAMINS"
    INFLAMMATION = "INFLAMMATION"
    IRON_STUDIES = "IRON_STUDIES"
    ELECTROLYTES = "ELECTROLYTES"
    OTHER = "OTHER"

    @classmethod
    def categorize_test(cls, test_name: str) -> "TestCategory":
        """
        Automatically categorize a test based on its name.

        Args:
            test_name: Name of the blood test

        Returns:
            TestCategory enum value
        """
        test_lower = test_name.lower()

        # Lipid panel
        if any(word in test_lower for word in ["cholesterol", "hdl", "ldl", "triglyceride", "lipid"]):
            return cls.LIPID_PANEL

        # Liver function
        if any(word in test_lower for word in ["alt", "ast", "alp", "alkaline phosphatase",
                                                 "alanine aminotransferase", "aspartate aminotransferase",
                                                 "ggt", "gamma glutamyl", "bilirubin", "albumin"]):
            return cls.LIVER_FUNCTION

        # Complete blood count
        if any(word in test_lower for word in ["wbc", "rbc", "hemoglobin", "hematocrit", "platelet",
                                                 "white blood", "red blood", "mcv", "mch", "mchc"]):
            return cls.COMPLETE_BLOOD_COUNT

        # Hormones
        if any(word in test_lower for word in ["testosterone", "estrogen", "progesterone", "cortisol",
                                                 "dhea", "prolactin", "growth hormone"]):
            return cls.HORMONES

        # Thyroid
        if any(word in test_lower for word in ["tsh", "thyroid", "t3", "t4", "thyroxine"]):
            return cls.THYROID

        # Metabolic panel
        if any(word in test_lower for word in ["glucose", "a1c", "hemoglobin a1c", "hba1c"]):
            return cls.METABOLIC_PANEL

        # Kidney function
        if any(word in test_lower for word in ["creatinine", "egfr", "bun", "urea"]):
            return cls.KIDNEY_FUNCTION

        # Vitamins
        if any(word in test_lower for word in ["vitamin", "b12", "folate", "25-hydroxy"]):
            return cls.VITAMINS

        # Inflammation
        if any(word in test_lower for word in ["crp", "c reactive protein", "esr", "sed rate"]):
            return cls.INFLAMMATION

        # Iron studies
        if any(word in test_lower for word in ["iron", "ferritin", "transferrin", "tibc"]):
            return cls.IRON_STUDIES

        # Electrolytes
        if any(word in test_lower for word in ["sodium", "potassium", "chloride", "calcium",
                                                 "magnesium", "phosphate"]):
            return cls.ELECTROLYTES

        return cls.OTHER
