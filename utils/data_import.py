"""
Data import and processing module.
Handles loading, cleaning, and storing bibliographic records.
"""

import pandas as pd
import re
from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.orm import Session
import os
from datetime import datetime

from models.bibliographic_record import BibliographicRecord
from utils.cleaners import (
    clean_oclc_control_number,
    normalize_isbn,
    normalize_issn,
    normalize_barcode,
    normalize_mms_id,
    clean_title,
    clean_author,
    clean_publisher,
    normalize_publication_date,
    normalize_title,
    normalize_publication_date_range,
    normalize_summary_holdings,
    normalize_field_590,
    normalize_language,
    normalize_e_overlap_interface,
    extract_first_value,
    parse_subjects,
)
from utils.call_number_parser import parse_call_number


# Column name mappings (handling potential variations)
COLUMN_MAPPINGS = {
    'Library Name': ['Library Name', 'library_name', 'library', 'library name'],
    'Location Name': ['Location Name', 'location_name', 'location', 'location name'],
    'Permanent Call Number Type': ['Permanent Call Number Type', 'call_number_type', 'call number type', 'permanent_call_number_type'],
    'Permanent Call Number': ['Permanent Call Number', 'permanent_call_number', 'call_number', 'permanent call number', 'call number'],
    'Item Copy Id': ['Item Copy Id', 'item_copy_id', 'item_copy', 'item id', 'copy id'],
    'Material Type': ['Material Type', 'material_type', 'material type', 'format'],
    'Item Policy': ['Item Policy', 'item_policy', 'item policy'],
    'Barcode': ['Barcode', 'barcode'],
    'Retention Note': ['Retention Note', 'Retention note', 'retention_note', 'retention note', 'notes', 'Notes'],
    'Title': ['Title', 'title'],
    'Title (Normalized)': ['Title (Normalized)', 'title_normalized', 'normalized_title'],
    'Author': ['Author', 'author', 'creator', 'primary_author'],
    'Author (Contributor)': ['Author (contributor)', 'author_contributor', 'contributor', 'contributors', 'additional authors'],
    'Publisher': ['Publisher', 'publisher'],
    'Publication Place': ['Publication Place', 'publication_place', 'pub_place', 'place_published'],
    'Publication Date': ['Publication Date', 'publication_date', 'pub_date', 'date', 'year'],
    'Begin Publication Date': ['Begin Pub Date', 'begin_publication_date', 'begin date', 'start date'],
    'End Publication Date': ['End Pub Date', 'end_publication_date', 'end date', 'finish date'],
    'Type of date': ['Type of date', 'type_of_date', 'date type', 'date_type'],
    'Edition': ['Edition', 'edition'],
    'Series': ['Series', 'series'],
    'MMS Id': ['MMS Id', 'mms_id', 'mmsid', 'mms id'],
    'ISBN': ['ISBN', 'isbn'],
    'ISBN (Normalized)': ['ISBN (Normalized)', 'isbn_normalized', 'normalized_isbn'],
    'ISSN': ['ISSN', 'issn'],
    'ISSN (Normalized)': ['ISSN (Normalized)', 'issn_normalized', 'normalized_issn'],
    'OCLC Control Number (035a)': ['OCLC Control Number (035a)', 'oclc_control_number', 'oclc', 'oclc_number', '035a'],
    'OCLC Number': ['OCLC Number', 'oclc_number_raw', 'oclc_raw'],
    'Subjects': ['Subjects', 'subjects', 'subject', 'topic'],
    'Summary Holdings': ['Summary Holdings', 'summary_holdings', 'holdings', 'coverage'],
    '590': ['590', 'field_590', 'marc_590'],
    'Loans Including Pre-Migration (In House + Not In House)': ['Num of Loans Including Pre-Migration (In House + Not In House)', 'Number of Loans Including Pre-Migration (In House + Not In House)', 'num_loans', 'loans', 'circulation', 'total_loans', 'Loans Including Pre-Migration (In House + Not In House)'],
    'Loans (In House + Not In House)': ['Loans (In House + Not In House)', 'num_loans_actual', 'actual_loans'],
    'Requests (Total)': ['Num of Requests (Total)', 'Number of Requests (Total)', 'Requests (Total)', 'num_requests', 'requests', 'total_requests', 'Requests (Total)'],
    'Last Loan Date': ['Last Loan Date', 'last_loan_date', 'last_circulation_date'],
    'Creation Date': ['Creation Date', 'creation_date', 'created_date', 'date_created'],
    'E-copy?': ['E-copy?', 'e_copy', 'ecopy'],
    'E-overlap collection': ['E-overlap collection', 'e_overlap_collection', 'overlap_collection'],
    'E-overlap interface': ['E-overlap interface', 'e_overlap_interface', 'interface_overlap'],
    'Language': ['Language', 'language', 'lang'],
    'Normalized Call Number': ['Normalized Call Number', 'normalized_call_number', 'sort_call_number'],
    'Open Access': ['Open Access', 'open_access', 'open access'],
    'Electronic access type': ['eR access type', 'electronic_access_type', 'access_type', 'eR access type'],
    'Has Committed To Retain': ['Has Committed To Retain', 'has_committed_to_retain', 'committed_to_retain', 'retain', 'Has Committeed to Retain', 'has_committeed_to_retain', 'committeed_to_retain'],
    'Decision': ['Decision', 'decision'],
    'OCLC Holdings': ['OCLC Holdings', 'oclc_holdings', 'holdings', 'oclc holdings'],
    'PALCI Holdings': ['PALCI Holdings', 'palci_holdings', 'palci'],
    'HathiTrust': ['HathiTrust', 'hathitrust'],
    'Permanent LC Classification Top Line': ['Permanent LC Classification Top Line', 'lc_subclass', 'lc_top_line'],
}


def normalize_column_name(col_name: str) -> str:
    """Normalize column name for matching."""
    import re
    # Strip whitespace, convert to lowercase, replace underscores/hyphens with spaces
    normalized = col_name.strip().lower().replace('_', ' ').replace('-', ' ')
    # Collapse multiple spaces to single space
    normalized = re.sub(r'\s+', ' ', normalized)
    return normalized


def find_column(df_columns: List[str], target_column: str) -> Optional[str]:
    """
    Find a column in the dataframe that matches the target column.
    Handles variations in column naming.
    """
    target_lower = target_column.lower()

    # Direct match
    if target_column in df_columns:
        return target_column

    # Case-insensitive match
    for col in df_columns:
        if col.lower() == target_lower:
            return col

    # Check against known variations
    if target_column in COLUMN_MAPPINGS:
        variations = COLUMN_MAPPINGS[target_column]
        for variation in variations:
            for col in df_columns:
                if normalize_column_name(col) == normalize_column_name(variation):
                    return col

    return None


def load_data_file(file_path: str) -> pd.DataFrame:
    """
    Load data from a CSV or Excel file.

    Args:
        file_path: Path to the data file

    Returns:
        pandas DataFrame with the loaded data
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")

    file_ext = os.path.splitext(file_path)[1].lower()

    if file_ext == '.csv':
        return pd.read_csv(file_path, dtype=str)
    elif file_ext in ['.xlsx', '.xlsm', '.xls']:
        return pd.read_excel(file_path, dtype=str)
    else:
        raise ValueError(f"Unsupported file format: {file_ext}")


def clean_and_normalize_row(row: pd.Series) -> Dict[str, Any]:
    """
    Clean and normalize a single row of data.

    Args:
        row: pandas Series representing a row

    Returns:
        Dictionary with cleaned and normalized values
    """
    result = {}

    # Get raw values with defaults
    def get_val(col: str, default=None):
        # Try direct lookup first
        if col in row.index:
            val = row[col]
        else:
            # Try to find a matching column using our normalization
            target_normalized = normalize_column_name(col)
            val = None
            for col_name in row.index:
                if normalize_column_name(col_name) == target_normalized:
                    val = row[col_name]
                    break
            if val is None:  # No match found
                val = default

        return str(val) if val is not None and pd.notna(val) else default

    # Key identifiers
    result['mms_id'] = normalize_mms_id(get_val('MMS Id'))
    result['barcode'] = normalize_barcode(get_val('Barcode'))
    result['permanent_call_number'] = get_val('Permanent Call Number')
    result['isbn'] = normalize_isbn(get_val('ISBN'))
    result['isbn_normalized'] = normalize_isbn(get_val('ISBN (Normalized)'))
    result['issn'] = normalize_issn(get_val('ISSN'))
    result['issn_normalized'] = normalize_issn(get_val('ISSN (Normalized)'))
    result['oclc_control_number'] = clean_oclc_control_number(get_val('OCLC Control Number (035a)'))
    result['oclc_number_raw'] = get_val('OCLC Number')

    # Basic info
    result['Library Name'] = extract_first_value(get_val('Library Name', ''))
    result['Location Name'] = extract_first_value(get_val('Location Name', ''))
    result['Title'] = clean_title(get_val('Title', ''))
    result['Title (Normalized)'] = normalize_title(get_val('Title (Normalized)', '')) or normalize_title(get_val('Title', ''))
    result['Author'] = clean_author(get_val('Author', ''))
    result['Author (Contributor)'] = clean_author(get_val('Author (Contributor)', ''))
    result['Publisher'] = clean_publisher(get_val('Publisher', ''))
    result['Publication Place'] = get_val('Publication Place')
    result['Publication Date'] = get_val('Publication Date', '')
    result['Begin Publication Date'] = get_val('Begin Publication Date', '')
    result['End Publication Date'] = get_val('End Publication Date', '')
    result['Type of date'] = get_val('Type of date', '')

    # Item Policy and Serial/Monograph separation
    item_policy = get_val('Item Policy', '').strip().upper()
    result['Item Policy'] = item_policy
    is_serial = item_policy in ['JOURNAL', 'SERIAL']

    # Publication date - use begin/end if provided, otherwise extract from publication_date
    if result['Begin Publication Date'] and result['End Publication Date']:
        # Use explicitly provided begin/end dates
        begin_result = normalize_publication_date(result['Begin Publication Date'], is_serial=is_serial)
        end_result = normalize_publication_date(result['End Publication Date'], is_serial=is_serial)
        result['Publication Year Start'] = begin_result[0] if begin_result[0] is not None else None
        result['Publication Year End'] = end_result[1] if end_result[1] is not None else None
        # Fallback to publication_date if begin/end parsing failed
        if result['Publication Year Start'] is None or result['Publication Year End'] is None:
            pub_date_result = normalize_publication_date(result['Publication Date'], is_serial=is_serial)
            result['Publication Year Start'] = pub_date_result[0]
            result['Publication Year End'] = pub_date_result[1]
    else:
        # Extract from publication_date
        pub_date_result = normalize_publication_date(result['Publication Date'], is_serial=is_serial)
        result['Publication Year Start'] = pub_date_result[0]
        result['Publication Year End'] = pub_date_result[1]

    result['edition'] = extract_first_value(get_val('Edition', ''))
    result['series'] = extract_first_value(get_val('Series', ''))

    # Item info
    result['Item Copy Id'] = get_val('Item Copy Id')
    result['Material Type'] = extract_first_value(get_val('Material Type', ''))
    result['Permanent Call Number Type'] = extract_first_value(get_val('Permanent Call Number Type', ''))
    result['Permanent Call Number'] = get_val('Permanent Call Number')
    result['Normalized Call Number'] = get_val('Normalized Call Number')
    result['Retention Note'] = get_val('Retention Note', '')

    # Parse call number
    call_number_result = parse_call_number(
        result['Permanent Call Number'] or '',
        result['Permanent Call Number Type'] or ''
    )
    result['call_number_classification'] = call_number_result.get('classification_type')
    result['call_number_class'] = call_number_result.get('class')
    # Map 'Permanent LC Classification Top Line' to call_number_subclass as requested
    result['Permanent LC Classification Top Line'] = get_val('Permanent LC Classification Top Line') or call_number_result.get('subclass')
    result['call_number_sortable'] = call_number_result.get('sortable_string')

    # Usage
    num_loans_str = get_val('Loans Including Pre-Migration (In House + Not In House)', '0')
    try:
        result['Loans Including Pre-Migration (In House + Not In House)'] = int(float(num_loans_str)) if num_loans_str else 0
    except (ValueError, TypeError):
        result['Loans Including Pre-Migration (In House + Not In House)'] = 0

    # Try to get Loans (In House + Not In House) from its expected column
    num_loans_actual_str = get_val('Loans (In House + Not In House)', '0')
    # If we got the default value, try to get it from the similar column that does exist
    if num_loans_actual_str == '0':
        # Try to get the value from Loans Including Pre-Migration (In House + Not In House)
        alt_value = get_val('Loans Including Pre-Migration (In House + Not In House)', '0')
        if alt_value != '0':
            num_loans_actual_str = alt_value
    try:
        result['Loans (In House + Not In House)'] = int(float(num_loans_actual_str)) if num_loans_actual_str else 0
    except (ValueError, TypeError):
        result['Loans (In House + Not In House)'] = 0

    num_requests_str = get_val('Requests (Total)', '0')
    try:
        result['Requests (Total)'] = int(float(num_requests_str)) if num_requests_str else 0
    except (ValueError, TypeError):
        result['Requests (Total)'] = 0

    # Boolean fields
    open_access_val = get_val('Open Access', '')
    result['Open Access'] = str(open_access_val).lower() in ['yes', 'true', '1', 'y']

    e_copy_val = get_val('E-copy?', '')
    result['E-copy?'] = str(e_copy_val).lower() in ['yes', 'true', '1', 'y']
    result['Electronic access type'] = get_val('Electronic access type')
    result['E-overlap collection'] = get_val('E-overlap collection')
    result['E-overlap interface'] = normalize_e_overlap_interface(get_val('E-overlap interface'))

    hathi_val = get_val('HathiTrust', '')
    result['HathiTrust'] = str(hathi_val).lower() in ['yes', 'true', '1', 'y']

    # Handle Decision field - try both possible source column names
    decision_value = get_val('Has Committed To Retain', None)
    if decision_value is None:
        decision_value = get_val('Decision', None)
    if decision_value is None:
        decision_value = ''
    result['Decision'] = decision_value  # Store original value for display
    result['Has Committed To Retain'] = str(decision_value).lower() in ['yes', 'true', '1', 'y']  # Boolean for internal use

    # Dates
    result['Creation Date'] = get_val('Creation Date')
    result['Last Loan Date'] = get_val('Last Loan Date')

    # Subjects - store original for display, parse for faceting
    subjects_raw = get_val('Subjects', '')
    result['Subjects'] = subjects_raw

    # Summary Holdings - process for coverage calculation
    summary_holdings_raw = get_val('Summary Holdings', '')
    result['Summary Holdings'] = summary_holdings_raw
    # Also compute normalized begin/end years for coverage visualization
    if summary_holdings_raw:
        hold_begin, hold_end = normalize_summary_holdings(summary_holdings_raw)
        result['Summary Holdings Begin Year'] = hold_begin
        result['Summary Holdings End Year'] = hold_end
    else:
        result['Summary Holdings Begin Year'] = None
        result['Summary Holdings End Year'] = None

    # 590 field
    field_590_raw = get_val('590', '')
    result['590'] = normalize_field_590(field_590_raw)

    # Language
    language_raw = get_val('Language', '')
    result['Language'] = normalize_language(language_raw)

    # Holdings
    oclc_holdings_str = get_val('OCLC Holdings', '')
    try:
        result['OCLC Holdings'] = int(float(oclc_holdings_str)) if oclc_holdings_str else None
    except (ValueError, TypeError):
        result['OCLC Holdings'] = None

    palci_holdings_str = get_val('PALCI Holdings', '')
    try:
        result['PALCI Holdings'] = int(float(palci_holdings_str)) if palci_holdings_str else None
    except (ValueError, TypeError):
        result['PALCI Holdings'] = None

    # Metadata
    result['Created At'] = datetime.now().isoformat()
    result['Updated At'] = datetime.now().isoformat()

    return result


def process_dataframe(df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Process a DataFrame by cleaning and normalizing all columns.
    Returns a DataFrame with Google Sheet column names for known columns.

    Args:
        df: Raw DataFrame from file

    Returns:
        Tuple of (processed DataFrame with Google Sheet column names, processing stats)
    """
    # Build mappings for renaming
    reverse_mapping = {}
    for standard, variations in COLUMN_MAPPINGS.items():
        for v in variations:
            reverse_mapping[v] = standard

    display_mapping = {}
    for standard, variations in COLUMN_MAPPINGS.items():
        display_mapping[standard] = variations[0]  # First variation is the Google Sheet column name

    stats = {
        'total_rows': len(df),
        'columns_found': [],
        'columns_missing': [],
        'errors': [],
    }

    # Rename input dataframe to internal standard names for known columns
    df_renamed = df.rename(columns=reverse_mapping)

    # Process each row using internal standard names
    processed_rows = []
    for idx, row in df_renamed.iterrows():
        try:
            processed_row = clean_and_normalize_row(row)
            processed_rows.append(processed_row)
        except Exception as e:
            stats['errors'].append(f"Row {idx}: {str(e)}")

    # Create processed DataFrame with internal standard names
    processed_df = pd.DataFrame(processed_rows)

    # Rename back to Google Sheet column names for known columns
    # Only rename columns that are in our display_mapping (known columns)
    columns_to_rename = {col: display_mapping[col] for col in processed_df.columns if col in display_mapping}
    processed_df = processed_df.rename(columns=columns_to_rename)

    # Update stats to show Google Sheet column names
    for standard_col in COLUMN_MAPPINGS.keys():
        google_sheet_col = display_mapping[standard_col]
        # Check if this column was found in the original data (by seeing if we have data for it)
        # We'll check if the column exists in the processed dataframe and has non-null values
        if google_sheet_col in processed_df.columns and not processed_df[google_sheet_col].isna().all():
            # Find what the original column name was (for reporting)
            original_col = None
            for col in df.columns:
                if col in reverse_mapping and reverse_mapping[col] == standard_col:
                    original_col = col
                    break
            if original_col:
                stats['columns_found'].append(f"{standard_col} (from '{original_col}' -> '{google_sheet_col}')")
            else:
                stats['columns_found'].append(f"{standard_col} (mapped to '{google_sheet_col}')")
        else:
            stats['columns_missing'].append(f"{standard_col} (expected '{google_sheet_col}')")

    return processed_df, stats


def store_records(session: Session, df: pd.DataFrame) -> int:
    """
    Store processed records in the database.

    Args:
        session: SQLAlchemy session
        df: Processed DataFrame

    Returns:
        Number of records stored
    """
    # Clear existing records
    session.query(BibliographicRecord).delete()

    records = []
    for _, row in df.iterrows():
        record = BibliographicRecord(**row.to_dict())
        records.append(record)

    session.bulk_save_objects(records)
    session.commit()

    return len(records)


def import_file(file_path: str, session: Session) -> Dict[str, Any]:
    """
    Import a data file, process it, and store in database.

    Args:
        file_path: Path to the data file
        session: SQLAlchemy session

    Returns:
        Dictionary with import results and stats
    """
    result = {
        'success': False,
        'file_path': file_path,
        'records_imported': 0,
        'processing_stats': {},
        'error': None,
    }

    try:
        # Load data
        df = load_data_file(file_path)
        result['processing_stats']['raw_rows'] = len(df)
        result['processing_stats']['raw_columns'] = list(df.columns)

        # Process data
        processed_df, process_stats = process_dataframe(df)
        result['processing_stats'].update(process_stats)

        # Store in database
        num_records = store_records(session, processed_df)
        result['records_imported'] = num_records
        result['success'] = True

    except Exception as e:
        result['error'] = str(e)
        session.rollback()

    return result


def get_all_records(session: Session) -> List[BibliographicRecord]:
    """Get all records from the database."""
    return session.query(BibliographicRecord).all()


def get_records_as_dataframe(session: Session) -> pd.DataFrame:
    """Get all records as a pandas DataFrame."""
    records = get_all_records(session)
    if not records:
        return pd.DataFrame()

    data = [record.to_dict() for record in records]
    return pd.DataFrame(data)


def get_record_by_id(session: Session, record_id: int) -> Optional[BibliographicRecord]:
    """Get a single record by ID."""
    return session.query(BibliographicRecord).filter(BibliographicRecord.id == record_id).first()


def get_facet_values(session: Session, column: str) -> List[Dict[str, Any]]:
    """
    Get unique values for a facet column with counts.

    Args:
        session: SQLAlchemy session
        column: Column name to facet on

    Returns:
        List of dicts with 'value' and 'count' keys
    """
    from sqlalchemy import func

    query = session.query(
        getattr(BibliographicRecord, column),
        func.count(BibliographicRecord.id).label('count')
    ).group_by(getattr(BibliographicRecord, column)).order_by(
        getattr(BibliographicRecord, column)
    )

    results = []
    for row in query:
        value = row[0]
        if value is not None and str(value).strip():
            results.append({
                'value': str(value),
                'count': row[1]
            })

    return results


def get_subjects_facet(session: Session) -> List[Dict[str, Any]]:
    """
    Get parsed subjects with counts.
    Handles semicolon-delimited subjects.
    """
    from sqlalchemy import func

    # Get all non-null subjects
    records = session.query(BibliographicRecord.subjects).filter(
        BibliographicRecord.subjects.isnot(None)
    ).all()

    subject_counts = {}
    for record in records:
        if record.subjects:
            subjects = parse_subjects(record.subjects)
            for subject in subjects:
                subject_counts[subject] = subject_counts.get(subject, 0) + 1

    return [
        {'value': subject, 'count': count}
        for subject, count in sorted(subject_counts.items(), key=lambda x: -x[1])
    ]


def apply_filters(
    session: Session,
    filters: Dict[str, Any] = None
) -> List[BibliographicRecord]:
    """
    Apply filters to retrieve matching records.

    Args:
        session: SQLAlchemy session
        filters: Dictionary of column -> value filters

    Returns:
        List of matching BibliographicRecord objects
    """
    query = session.query(BibliographicRecord)

    if filters:
        for column, value in filters.items():
            if value is None or value == '' or value == []:
                continue

            col = getattr(BibliographicRecord, column, None)
            if col is None:
                continue

            if isinstance(value, list):
                if value:
                    query = query.filter(col.in_(value))
            elif isinstance(value, str):
                query = query.filter(col == value)
            elif isinstance(value, tuple):
                # Range filter
                min_val, max_val = value
                if min_val is not None:
                    query = query.filter(col >= min_val)
                if max_val is not None:
                    query = query.filter(col <= max_val)

    return query.all()
