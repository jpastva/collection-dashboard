"""
Call number parsing utilities using pycallnumber.
Handles Library of Congress and Dewey Decimal classification systems.
"""

from typing import Optional, Dict, Any, List
import re

try:
    import pycallnumber as pycn
    from pycallnumber.units.callnumbers.lc import LC as LCType
    from pycallnumber.units.callnumbers.dewey import Dewey as DeweyType
    PYCALLNUMBER_AVAILABLE = True
except ImportError:
    PYCALLNUMBER_AVAILABLE = False
    LCType = None
    DeweyType = None


def parse_call_number(call_number: str, call_number_type: str) -> Dict[str, Any]:
    """
    Parse a call number using pycallnumber to enable sorting and faceting.

    Args:
        call_number: Raw call number string
        call_number_type: Type of classification
            - "Library of Congress classification"
            - "Dewey Decimal classification"

    Returns:
        Dictionary with parsed call number components
    """
    result = {
        'original': call_number,
        'parsed': None,
        'classification_type': None,
        'class': None,
        'subclass': None,
        'numeric_part': None,
        'cutter': None,
        'year': None,
        'sortable_string': None,
        'parse_error': None,
    }

    if not call_number or not isinstance(call_number, str):
        return result

    call_number = call_number.strip()

    if not call_number:
        return result

    result['original'] = call_number

    if not PYCALLNUMBER_AVAILABLE:
        result['parse_error'] = 'pycallnumber not available'
        # Fall back to basic string sorting
        result['sortable_string'] = call_number
        return result

    try:
        if call_number_type == "Library of Congress classification":
            result['classification_type'] = 'LC'
            parsed = pycn.callnumber(call_number)
            result['parsed'] = parsed

            if LCType and isinstance(parsed, LCType):
                # Extract class (e.g., "QA") using regex
                class_match = re.match(r'^([A-Z]{1,2})', str(parsed))
                result['class'] = class_match.group(1) if class_match else None

                # Extract subclass (e.g., "QA76.73")
                if parsed.classification:
                    result['subclass'] = str(parsed.classification)

                # Extract cutters
                if parsed.cutters:
                    result['cutter'] = str(parsed.cutters)

                result['sortable_string'] = str(parsed)

        elif call_number_type == "Dewey Decimal classification":
            result['classification_type'] = 'DEWEY'

            try:
                parsed = pycn.callnumber(call_number)
                result['parsed'] = parsed

                if DeweyType and isinstance(parsed, DeweyType):
                    # Extract class (e.g., "005")
                    class_match = re.match(r'^(\d{3})', str(parsed))
                    result['class'] = class_match.group(1) if class_match else None

                    # Extract full number
                    if parsed.number:
                        result['numeric_part'] = str(parsed.number)

                    result['sortable_string'] = str(parsed)
                else:
                    # pycallnumber didn't recognize it as Dewey, use regex fallback
                    raise ValueError("Not recognized as Dewey by pycallnumber")
            except Exception:
                # Fallback to regex-based parsing for Dewey
                dewey_match = re.match(r'^(\d{3}(?:\.\d+)?)', call_number)
                if dewey_match:
                    result['class'] = dewey_match.group(1)
                    result['numeric_part'] = dewey_match.group(1)
                result['sortable_string'] = call_number

        else:
            # Unknown type, just use the string as-is for sorting
            result['sortable_string'] = call_number

    except Exception as e:
        result['parse_error'] = str(e)
        # Fall back to string sorting
        result['sortable_string'] = call_number

    return result


def get_lc_class(call_number: str) -> Optional[str]:
    """
    Extract the Library of Congress class from a call number.

    Args:
        call_number: LC call number string

    Returns:
        LC class (e.g., "QA", "PS", "E"), or None if not parseable
    """
    if not call_number or not isinstance(call_number, str):
        return None

    call_number = call_number.strip()

    if not call_number:
        return None

    # Try to extract LC class pattern (1-2 letters at start)
    match = re.match(r'^([A-Z]{1,2})', call_number.upper())
    if match:
        return match.group(1)

    # Try pycallnumber if available
    if PYCALLNUMBER_AVAILABLE:
        try:
            parsed = pycn.callnumber(call_number)
            if isinstance(parsed, pycn.LC):
                return parsed.classification_class
        except Exception:
            pass

    return None


def get_lc_subclass(call_number: str) -> Optional[str]:
    """
    Extract the Library of Congress subclass from a call number.

    Args:
        call_number: LC call number string

    Returns:
        LC subclass (e.g., "QA75", "PS3569"), or None if not parseable
    """
    if not call_number or not isinstance(call_number, str):
        return None

    call_number = call_number.strip()

    if not call_number:
        return None

    # Try pycallnumber if available
    if PYCALLNUMBER_AVAILABLE:
        try:
            parsed = pycn.callnumber(call_number)
            if isinstance(parsed, pycn.LC):
                return parsed.subclassification
        except Exception:
            pass

    # Fallback: try to extract class + numeric portion
    match = re.match(r'^([A-Z]{1,2}\d{1,4})', call_number.upper())
    if match:
        return match.group(1)

    return None


def get_dewey_class(call_number: str) -> Optional[str]:
    """
    Extract the Dewey Decimal class from a call number.

    Args:
        call_number: Dewey Decimal call number string

    Returns:
        Dewey class (e.g., "510", "813", "004"), or None if not parseable
    """
    if not call_number or not isinstance(call_number, str):
        return None

    call_number = call_number.strip()

    if not call_number:
        return None

    # Try to extract Dewey pattern (3 digits with optional decimal)
    match = re.match(r'^(\d{3}(?:\.\d+)?)', call_number)
    if match:
        return match.group(1)

    # Try pycallnumber if available
    if PYCALLNUMBER_AVAILABLE:
        try:
            parsed = pycn.callnumber(call_number)
            if isinstance(parsed, pycn.Dewey):
                return parsed.classification_class
        except Exception:
            pass

    return None


def get_dewey_subdivision(call_number: str) -> Optional[str]:
    """
    Extract the Dewey Decimal subdivision from a call number.

    Args:
        call_number: Dewey Decimal call number string

    Returns:
        Dewey subdivision (e.g., "510.5", "813.54"), or None if not parseable
    """
    if not call_number or not isinstance(call_number, str):
        return None

    call_number = call_number.strip()

    if not call_number:
        return None

    # Try pycallnumber if available
    if PYCALLNUMBER_AVAILABLE:
        try:
            parsed = pycn.callnumber(call_number)
            if isinstance(parsed, pycn.Dewey):
                return parsed.number
        except Exception:
            pass

    # Fallback: try to extract full Dewey number
    match = re.match(r'^(\d{3}(?:\.\d+)?)', call_number)
    if match:
        return match.group(1)

    return None


def get_lc_class_description(lc_class: str) -> str:
    """
    Get the description for a Library of Congress class.

    Args:
        lc_class: LC class code (e.g., "QA", "PS")

    Returns:
        Human-readable description of the class
    """
    lc_classes = {
        'A': 'General Works',
        'B': 'Philosophy, Psychology, Religion',
        'C': 'Auxiliary Sciences of History',
        'D': 'World History',
        'E': 'History of the Americas (General)',
        'F': 'History of the Americas (Local)',
        'G': 'Geography, Anthropology, Recreation',
        'H': 'Social Sciences',
        'J': 'Political Science',
        'K': 'Law',
        'L': 'Education',
        'M': 'Music',
        'N': 'Fine Arts',
        'P': 'Language and Literature',
        'Q': 'Science',
        'R': 'Medicine',
        'S': 'Agriculture',
        'T': 'Technology',
        'U': 'Military Science',
        'V': 'Naval Science',
        'Z': 'Bibliography, Library Science',
    }

    if not lc_class:
        return 'Unknown'

    # Get the first letter or two-letter class
    if lc_class[:2] in lc_classes:
        return lc_classes[lc_class[:2]]
    elif lc_class[:1] in lc_classes:
        return lc_classes[lc_class[:1]]

    return 'Unknown'


def get_dewey_class_description(dewey_class: str) -> str:
    """
    Get the description for a Dewey Decimal class.

    Args:
        dewey_class: Dewey class code (e.g., "510", "813")

    Returns:
        Human-readable description of the class
    """
    if not dewey_class:
        return 'Unknown'

    try:
        # Get the main class (first digit)
        main_class = dewey_class[0]

        dewey_classes = {
            '0': 'Computer Science, Information & General Works',
            '1': 'Philosophy & Psychology',
            '2': 'Religion',
            '3': 'Social Sciences',
            '4': 'Language',
            '5': 'Science',
            '6': 'Technology',
            '7': 'Arts & Recreation',
            '8': 'Literature',
            '9': 'History & Geography',
        }

        return dewey_classes.get(main_class, 'Unknown')
    except (IndexError, TypeError):
        return 'Unknown'
