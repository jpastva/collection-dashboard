"""
Data cleaning and normalization functions for bibliographic records.
"""

import re
from typing import Optional, List, Tuple
from dateutil import parser as date_parser


def clean_oclc_control_number(oclc_number: str) -> Optional[str]:
    """
    Clean OCLC control number to conform to proper format.
    Removes prefixes (ocm, ocn, on) and leading zeros.
    Reference: https://help.oclc.org/Metadata_Services/WorldShare_Collection_Manager/Data_sync_collections/Prepare_your_data/30035_field_and_OCLC_control_numbers

    Args:
        oclc_number: Raw OCLC control number string

    Returns:
        Cleaned numeric OCLC number as string, or None if invalid
    """
    if not oclc_number or not isinstance(oclc_number, str):
        return None

    # Strip whitespace
    oclc_number = oclc_number.strip()

    if not oclc_number:
        return None

    # Remove common prefixes (case-insensitive)
    prefix_pattern = r'^(ocm|ocn|on)\s*'
    oclc_number = re.sub(prefix_pattern, '', oclc_number, flags=re.IGNORECASE)

    # Remove any non-numeric characters except leading zeros we'll handle next
    oclc_number = re.sub(r'[^\d]', '', oclc_number)

    if not oclc_number:
        return None

    # Remove leading zeros
    oclc_number = oclc_number.lstrip('0')

    # If string is empty after stripping zeros, it was all zeros
    if not oclc_number:
        return None

    return oclc_number


def normalize_isbn(isbn: str) -> Optional[str]:
    """
    Normalize ISBN to allow for sorting and matching.
    Handles ISBN-10 and ISBN-13 formats.

    Args:
        isbn: Raw ISBN string

    Returns:
        Normalized ISBN (ISBN-13 format preferred), or None if invalid
    """
    if not isbn or not isinstance(isbn, str):
        return None

    # Strip whitespace and common separators
    isbn = isbn.strip()
    isbn = re.sub(r'[-\s]', '', isbn)

    # Remove any "ISBN" prefix
    isbn = re.sub(r'^ISBN', '', isbn, flags=re.IGNORECASE)

    # Extract only digits and X (for ISBN-10 check digit)
    isbn = re.sub(r'[^\dX]', '', isbn, flags=re.IGNORECASE)

    if not isbn:
        return None

    # Handle ISBN-10 to ISBN-13 conversion
    if len(isbn) == 10:
        # Keep as ISBN-10 but normalize (uppercase X)
        return isbn[:-1] + isbn[-1].upper() if isbn[-1].upper() == 'X' else isbn
    elif len(isbn) == 13:
        return isbn
    elif len(isbn) > 13:
        # Try to extract a valid ISBN from longer string
        # ISBN-13
        match = re.search(r'\d{13}', isbn)
        if match:
            return match.group()
        # ISBN-10
        match = re.search(r'\d{9}[\dX]', isbn, flags=re.IGNORECASE)
        if match:
            result = match.group()
            return result[:-1] + result[-1].upper() if result[-1].upper() == 'X' else result

    return None


def normalize_issn(issn: str) -> Optional[str]:
    """
    Normalize ISSN to standard format (XXXX-XXXX).

    Args:
        issn: Raw ISSN string

    Returns:
        Normalized ISSN in XXXX-XXXX format, or None if invalid
    """
    if not issn or not isinstance(issn, str):
        return None

    # Strip whitespace
    issn = issn.strip()

    # Remove "ISSN" prefix
    issn = re.sub(r'^ISSN', '', issn, flags=re.IGNORECASE)
    issn = issn.strip()

    # Extract digits and X
    chars = re.findall(r'[\dX]', issn, flags=re.IGNORECASE)

    if len(chars) != 8:
        return None

    # Validate check digit (X can only be in last position)
    for i, char in enumerate(chars[:-1]):
        if char.upper() == 'X':
            return None

    # Format as XXXX-XXXX
    result = ''.join(chars[:4]) + '-' + ''.join(chars[4:])

    # Uppercase X in check digit position
    if result[-1].upper() == 'X':
        result = result[:-1] + 'X'

    return result


def normalize_barcode(barcode: str) -> Optional[str]:
    """
    Normalize barcode for sorting and matching.
    Removes spaces and common prefixes.

    Args:
        barcode: Raw barcode string

    Returns:
        Normalized barcode string, or None if invalid
    """
    if not barcode or not isinstance(barcode, str):
        return None

    # Strip whitespace
    barcode = barcode.strip()

    if not barcode:
        return None

    # Remove common prefixes that might be present
    barcode = re.sub(r'^BARCODE\s*', '', barcode, flags=re.IGNORECASE)

    # Remove spaces and hyphens for consistency
    barcode = re.sub(r'[\s\-]', '', barcode)

    return barcode if barcode else None


def normalize_mms_id(mms_id: str) -> Optional[str]:
    """
    Normalize MMS ID for sorting and matching.
    Treats as text, removes leading/trailing whitespace.

    Args:
        mms_id: Raw MMS ID string

    Returns:
        Normalized MMS ID string, or None if invalid
    """
    if not mms_id or not isinstance(mms_id, str):
        return None

    # Strip whitespace
    mms_id = mms_id.strip()

    if not mms_id:
        return None

    # Remove any leading zeros if it's purely numeric
    if mms_id.isdigit():
        mms_id = mms_id.lstrip('0') or '0'

    return mms_id


def clean_title(title: str) -> Optional[str]:
    """
    Clean title by removing extraneous punctuation and normalizing spaces.
    Improves searching and sorting.

    Args:
        title: Raw title string

    Returns:
        Cleaned title string, or None if invalid
    """
    if not title or not isinstance(title, str):
        return None

    # Strip whitespace
    title = title.strip()

    if not title:
        return None

    # Remove trailing punctuation marks (but keep internal punctuation)
    title = re.sub(r'[;,:\.\-\/\=\[\]\(\)\{\}]+$', '', title)

    # Remove leading punctuation marks
    title = re.sub(r'^[;,:\.\-\/\=\[\]\(\)\{\}]+', '', title)

    # Normalize multiple spaces to single space
    title = re.sub(r'\s+', ' ', title)

    # Remove leading/trailing spaces that may have resulted
    title = title.strip()

    # Remove leading articles in brackets (common in MARC records)
    title = re.sub(r'^\[[Aa]n?|The\]\s*', '', title)

    return title if title else None


def clean_author(author: str) -> Optional[str]:
    """
    Clean author name (personal or corporate) formatted according to
    Library of Congress names. Normalizes for effective grouping and faceting.

    Args:
        author: Raw author name string

    Returns:
        Cleaned author name, or None if invalid
    """
    if not author or not isinstance(author, str):
        return None

    # Strip whitespace
    author = author.strip()

    if not author:
        return None

    # Remove trailing punctuation
    author = re.sub(r'[;,\.]+$', '', author)

    # Normalize multiple spaces
    author = re.sub(r'\s+', ' ', author)

    # Remove common prefixes/suffixes that don't aid identification
    # but keep meaningful name parts

    # Handle LC name format: "Last, First" or "Corporate Name"
    # Keep as-is for faceting but ensure consistency

    author = author.strip()

    return author if author else None


def clean_publisher(publisher: str) -> Optional[str]:
    """
    Clean publisher name by removing unnecessary punctuation.
    Improves faceting of publisher data.

    Args:
        publisher: Raw publisher string

    Returns:
        Cleaned publisher name, or None if invalid
    """
    if not publisher or not isinstance(publisher, str):
        return None

    # Strip whitespace
    publisher = publisher.strip()

    if not publisher:
        return None

    # Remove common publishing terms that don't add value
    publisher = re.sub(r'\bPress\b', '', publisher, flags=re.IGNORECASE)
    publisher = re.sub(r'\bPublishing\b', '', publisher, flags=re.IGNORECASE)
    publisher = re.sub(r'\bPublisher\b', '', publisher, flags=re.IGNORECASE)
    publisher = re.sub(r'\bCo\b\.?', '', publisher, flags=re.IGNORECASE)
    publisher = re.sub(r'\bInc\b\.?', '', publisher, flags=re.IGNORECASE)
    publisher = re.sub(r'\bLtd\b\.?', '', publisher, flags=re.IGNORECASE)

    # Remove trailing punctuation
    publisher = re.sub(r'[;,:\.\-\/\=\[\]\(\)\{\}]+$', '', publisher)

    # Remove leading punctuation
    publisher = re.sub(r'^[;,:\.\-\/\=\[\]\(\)\{\}]+', '', publisher)

    # Normalize multiple spaces
    publisher = re.sub(r'\s+', ' ', publisher)

    publisher = publisher.strip()

    return publisher if publisher else None


def normalize_publication_date(date_str: str, is_serial: bool = False) -> Tuple[Optional[int], Optional[int], Optional[str]]:
    """
    Normalize publication date according to specific bibliographic rules.
    - Strips 'c' or copyright symbols at the start.
    - Strips non-numeric characters (?,u,(,),[,],<,>) and hyphens (unless it's a serial span).
    - Retains 4-digit years (YYYY).
    - For serials, splits 4-digit spans separated by '-' into start and end dates.

    Args:
        date_str: Raw publication date string
        is_serial: Whether the record is a serial (influences hyphen handling)

    Returns:
        Tuple of (start_year, end_year, normalized_display)
    """
    if not date_str or not isinstance(date_str, str):
        return (None, None, None)

    # Strip whitespace
    date_str = date_str.strip()
    if not date_str:
        return (None, None, None)

    # 1. Strip leading 'c' or copyright symbol (©)
    date_str = re.sub(r'^[c©\s]+', '', date_str, flags=re.IGNORECASE)

    # 2. Handle Serial Date Spans first (if it's a serial and has a hyphen)
    if is_serial and '-' in date_str:
        # Look for two 4-digit years separated by a hyphen
        span_match = re.search(r'(\b\d{4}\b)\s*-\s*(\b\d{4}\b)', date_str)
        if span_match:
            start_year = int(span_match.group(1))
            end_year = int(span_match.group(2))
            return (start_year, end_year, f"{start_year}-{end_year}")

    # 3. General normalization: Strip specific non-numeric characters
    # Characters to strip: ? , © u ( ) [ ] < > and now hyphens since we handled the span
    chars_to_strip = r'[?,©u\(\)\[\]<>\-]'
    date_str = re.sub(chars_to_strip, ' ', date_str)

    # 4. Extract 4-digit years
    years = re.findall(r'\b\d{4}\b', date_str)

    if not years:
        return (None, None, None)

    if len(years) >= 2:
        start_year = int(years[0])
        end_year = int(years[-1])
        return (start_year, end_year, f"{start_year}-{end_year}")
    elif len(years) == 1:
        year = int(years[0])
        return (year, year, str(year))

    return (None, None, None)


def extract_first_value(value: str, delimiter: str = ';') -> Optional[str]:
    """
    Extract the first value from a delimited string.
    Used for columns with multiple values separated by delimiter.

    Args:
        value: Raw string potentially containing multiple values
        delimiter: Delimiter character (default: semicolon)

    Returns:
        First value, or None if invalid
    """
    if not value or not isinstance(value, str):
        return None

    # Strip whitespace
    value = value.strip()

    if not value:
        return None

    # Split by delimiter and take first value
    parts = value.split(delimiter)
    first_value = parts[0].strip() if parts else value

    return first_value if first_value else None


def parse_subjects(subjects: str) -> List[str]:
    """
    Parse subjects column with multiple entries delimited by semicolon.
    Returns list of individual subjects for faceting and sorting.

    Args:
        subjects: Raw subjects string with semicolon delimiters

    Returns:
        List of individual subject strings
    """
    if not subjects or not isinstance(subjects, str):
        return []

    # Strip whitespace
    subjects = subjects.strip()

    if not subjects:
        return []

    # Split by semicolon and clean each subject
    subject_list = [s.strip() for s in subjects.split(';')]

    # Filter out empty strings
    subject_list = [s for s in subject_list if s]

    return subject_list


def normalize_call_number(call_number: str, call_number_type: str) -> dict:
    """
    Normalize call number for sorting and faceting.
    Uses pycallnumber for LC and Dewey classification.

    Args:
        call_number: Raw call number string
        call_number_type: Type of classification (Library of Congress or Dewey Decimal)

    Returns:
        Dictionary with normalized call number and classification details
    """
    result = {
        'original': call_number,
        'normalized': None,
        'classification': None,
        'class': None,
        'subclass': None,
        'sortable': None,
    }

    if not call_number or not isinstance(call_number, str):
        return result

    call_number = call_number.strip()

    if not call_number:
        return result

    result['normalized'] = call_number

    if call_number_type:
        result['classification'] = call_number_type

    # Further parsing is handled by pycallnumber in the call_number_parser module
    return result


def normalize_title(title: str) -> Optional[str]:
    """
    Normalize title for sorting and matching.
    Similar to clean_title but focused on normalization for comparison.

    Args:
        title: Raw title string

    Returns:
        Normalized title string, or None if invalid
    """
    if not title or not isinstance(title, str):
        return None

    # Strip whitespace
    title = title.strip()

    if not title:
        return None

    # Convert to lowercase for normalization
    title = title.lower()

    # Remove punctuation
    title = re.sub(r'[^\w\s]', '', title)

    # Normalize multiple spaces to single space
    title = re.sub(r'\s+', ' ', title)

    # Remove leading/trailing spaces
    title = title.strip()

    # Remove leading articles
    title = re.sub(r'^(a|an|the)\s+', '', title)

    return title if title else None


def normalize_publication_date_range(date_str: str) -> Tuple[Optional[int], Optional[int]]:
    """
    Normalize publication date to extract begin and end years.
    Handles various date formats including ranges.

    Args:
        date_str: Raw publication date string

    Returns:
        Tuple of (begin_year, end_year)
    """
    if not date_str or not isinstance(date_str, str):
        return (None, None)

    # Strip whitespace
    date_str = date_str.strip()
    if not date_str:
        return (None, None)

    # Use existing normalize_publication_date function which already handles ranges
    start_year, end_year, _ = normalize_publication_date(date_str, is_serial=True)
    return (start_year, end_year)


def normalize_summary_holdings(holdings: str) -> Tuple[Optional[int], Optional[int]]:
    """
    Normalize summary holdings to extract date span of held issues.
    Based on guidelines from https://journal.code4lib.org/articles/17839

    Args:
        holdings: Raw summary holdings string (e.g., "1990-2020", "v.1:v.10", etc.)

    Returns:
        Tuple of (begin_year, end_year) of held coverage, or None if invalid
    """
    if not holdings or not isinstance(holdings, str):
        return (None, None)

    # Strip whitespace
    holdings = holdings.strip()
    if not holdings:
        return (None, None)

    # Convert to uppercase for consistent processing
    holdings_upper = holdings.upper()

    # Look for year patterns (4-digit years)
    year_matches = re.findall(r'\b\d{4}\b', holdings_upper)

    if not year_matches:
        # If no 4-digit years found, try to extract volume/issue information
        # This is a simplified approach - in reality, this would need more complex parsing
        # to map volumes to years based on publication patterns
        return (None, None)

    # Extract years and convert to integers
    years = [int(year) for year in year_matches]

    if len(years) >= 2:
        # Range format like "1990-2020" or list like "1990, 1991, 1992"
        return (min(years), max(years))
    elif len(years) == 1:
        # Single year
        return (years[0], years[0])
    else:
        return (None, None)


def normalize_field_590(field_590: str) -> Optional[str]:
    """
    Normalize MARC 590 field (Local notes).
    Extracts useful information for serials tracking.

    Args:
        field_590: Raw MARC 590 field string

    Returns:
        Cleaned and normalized string, or None if invalid
    """
    if not field_590 or not isinstance(field_590, str):
        return None

    # Strip whitespace
    field_590 = field_590.strip()
    if not field_590:
        return None

    # Remove common prefixes that don't add value
    field_590 = re.sub(r'^590\s*\\\\\\$a\s*', '', field_590, flags=re.IGNORECASE)
    field_590 = re.sub(r'^590\s*', '', field_590, flags=re.IGNORECASE)

    # Normalize multiple spaces
    field_590 = re.sub(r'\s+', ' ', field_590)

    # Remove leading/trailing spaces
    field_590 = field_590.strip()

    return field_590 if field_590 else None


def normalize_language(language: str) -> Optional[str]:
    """
    Normalize language code or name.
    Converts to standard 3-letter ISO 639-2/B or 2-letter ISO 639-1 codes where possible.

    Args:
        language: Raw language string

    Returns:
        Normalized language string, or None if invalid
    """
    if not language or not isinstance(language, str):
        return None

    # Strip whitespace
    language = language.strip()
    if not language:
        return None

    # Convert to lowercase for normalization
    language = language.lower()

    # Remove extra characters
    language = re.sub(r'[^a-z\-]', '', language)

    # Handle common language names (simplified mapping)
    language_map = {
        'english': 'eng',
        'spanish': 'spa',
        'french': 'fre',
        'german': 'ger',
        'italian': 'ita',
        'portuguese': 'por',
        'russian': 'rus',
        'chinese': 'chi',
        'japanese': 'jpn',
        'korean': 'kor',
        'arabic': 'ara',
    }

    # Check if it's a known language name
    if language in language_map:
        return language_map[language]

    # If it's already a code-like format (2-3 letters), return as-is
    if re.match(r'^[a-z]{2,3}$', language):
        return language

    # Otherwise, return the cleaned version
    return language if language else None


def normalize_e_overlap_interface(interface: str) -> Optional[str]:
    """
    Normalize E-overlap interface field.
    Cleans up interface descriptions for electronic serials overlap.

    Args:
        interface: Raw e-overlap interface string

    Returns:
        Normalized interface string, or None if invalid
    """
    if not interface or not isinstance(interface, str):
        return None

    # Strip whitespace
    interface = interface.strip()
    if not interface:
        return None

    # Remove common prefixes
    interface = re.sub(r'^E-OVERLAP\s+INTERFACE\s*:?\s*', '', interface, flags=re.IGNORECASE)
    interface = re.sub(r'^INTERFACE\s*:?\s*', '', interface, flags=re.IGNORECASE)

    # Normalize multiple spaces
    interface = re.sub(r'\s+', ' ', interface)

    # Remove leading/trailing spaces
    interface = interface.strip()

    return interface if interface else None
