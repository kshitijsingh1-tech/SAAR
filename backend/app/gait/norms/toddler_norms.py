"""
Toddler reference norms and developmental milestone context ported from ToddleAI GaitNorms.
"""
from ..schemas import CadenceRange

SOURCE_CITATION = "Context from Rygelova et al. (PLOS ONE 2023), Sutherland, and Dusing & Thorpe GAITRite norms"


def get_cadence_range(age_months: int) -> CadenceRange:
    """Returns context-only cadence bands synthesized from pediatric literature."""
    if age_months < 18:
        return CadenceRange(low=150.0, high=190.0, source=SOURCE_CITATION)
    elif age_months < 24:
        return CadenceRange(low=135.0, high=175.0, source=SOURCE_CITATION)
    elif age_months < 36:
        return CadenceRange(low=120.0, high=160.0, source=SOURCE_CITATION)
    elif age_months < 48:
        return CadenceRange(low=115.0, high=145.0, source=SOURCE_CITATION)
    else:
        return CadenceRange(low=110.0, high=135.0, source=SOURCE_CITATION)


def get_walking_milestone_context(age_months: int) -> str:
    """Developmental milestone context string from WHO and Sutherland studies."""
    if age_months < 18:
        return "Most children walk independently between 9 and 18 months (WHO). Early walking is variable, and toddler gait is still rapidly developing."
    elif age_months < 48:
        return "Most children walk independently between 9 and 18 months (WHO). Gait patterning becomes progressively more stable through the toddler and preschool years, with substantial maturation by about age 4 (Sutherland)."
    else:
        return "Most children walk independently between 9 and 18 months (WHO). Even after independent walking begins, gait continues to mature over early childhood, with substantial maturation by about age 4 (Sutherland)."
