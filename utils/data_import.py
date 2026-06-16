"""
Data import and processing module.
Handles loading, cleaning, and storing bibliographic records.
"""

import pandas as pd
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
    'Library Name': ['library_name', 'library', 'library name'],
    'Location Name': ['location_name', 'location', 'location name'],
    'Permanent Call Number Type': ['call_number_type', 'call number type', 'permanent_call_number_type'],
    'Permanent Call Number': ['permanent_call_number', 'call_number', 'permanent call number', 'call number'],
    'Item Copy Id': ['item_copy_id', 'item_copy', 'item id', 'copy id'],
    'Material Type': ['material_type', 'material type', 'format'],
    'Item Policy': ['item_policy', 'item policy'],
    'Barcode': ['barcode'],
    'Retention Note': ['retention_note', 'retention note', 'notes'],
    'Title': ['title'],
    'Title (Normalized)': ['title_normalized', 'normalized_title'],
    'Author': ['author', 'creator', 'primary_author'],
    'Author (Contributor)': ['author_contributor', 'contributor', 'contributors', 'additional authors'],
    'Publisher': ['publisher'],
    'Publication Place': ['publication_place', 'pub_place', 'place_published'],
    'Publication Date': ['publication_date', 'pub_date', 'date', 'year'],
    'Begin Publication Date': ['begin_publication_date', 'begin date', 'start date'],
    'End Publication Date': ['end_publication_date', 'end date', 'finish date'],
    'Type of Date': ['type_of_date', 'date type', 'date_type'],
    'Edition': ['edition'],
    'Series': ['series'],
    'MMS Id': ['mms_id', 'mmsid', 'mms id'],
    'ISBN': ['isbn'],
    'ISBN (Normalized)': ['isbn_normalized', 'normalized_isbn'],
    'ISSN': ['issn'],
    'ISSN (Normalized)': ['issn_normalized', 'normalized_issn'],
    'OCLC Control Number (035a)': ['oclc_control_number', 'oclc', 'oclc_number', '035a'],
    'OCLC Number': ['oclc_number_raw', 'oclc_raw'],
    'Subjects': ['subjects', 'subject', 'topic'],
    'Summary Holdings': ['summary_holdings', 'holdings', 'coverage'],
    '590': ['field_590', 'marc_590'],
    'Num of Loans Including Pre-Migration (In House + Not In House)': ['num_loans', 'loans', 'circulation', 'total_loans'],
    'Num of Loans (In House + Not In House)': ['num_loans_actual', 'actual_loans'],
    'Num of Requests (Total)': ['num_requests', 'requests', 'total_requests'],
    'Last Loan Date': ['last_loan_date', 'last_circulation_date'],
    'Creation Date': ['creation_date', 'created_date', 'date_created'],
    'E-copy?': ['e_copy', 'ecopy'],
    'E-overlap collection': ['e_overlap_collection', 'overlap_collection'],
    'E-overlap interface': ['e_overlap_interface', 'interface_overlap'],
    'Language': ['language', 'lang'],
    'Normalized Call Number': ['normalized_call_number', 'sort_call_number'],
    'Open Access': ['open_access', 'open access'],
    'Electronic access type': ['electronic_access_type', 'access_type'],
    'Has Committed To Retain': ['has_committed_to_retain', 'committed_to_retain', 'retain'],
    'OCLC Holdings': ['oclc_holdings', 'holdings', 'oclc holdings'],
    'PALCI Holdings': ['palci_holdings', 'palci'],
    'Permanent LC Classification Top Line': ['lc_subclass', 'lc_top_line'],
}


def normalize_column_name(col_name: str) -> str:
    """Normalize column name for matching."""
    return col_name.strip().lower().replace('_', ' ').replace('-', ' ')


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
                if normalize_column_name(col) == variation:
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
        val = row.get(col, default)
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
    result['library_name'] = extract_first_value(get_val('Library Name', ''))
    result['location_name'] = extract_first_value(get_val('Location Name', ''))
    result['title'] = clean_title(get_val('Title', ''))
    result['title_normalized'] = normalize_title(get_val('Title (Normalized)', '')) or normalize_title(get_val('Title', ''))
    result['author'] = clean_author(get_val('Author', ''))
    result['author_contributor'] = clean_author(get_val('Author (Contributor)', ''))
    result['publisher'] = clean_publisher(get_val('Publisher', ''))
    result['publication_place'] = get_val('Publication Place')
    result['publication_date'] = get_val('Publication Date', '')
    result['begin_publication_date'] = get_val('Begin Publication Date', '')
    result['end_publication_date'] = get_val('End Publication Date', '')
    result['type_of_date'] = get_val('Type of Date', '')

    # Item Policy and Serial/Monograph separation
    item_policy = get_val('Item Policy', '').strip().upper()
    result['item_policy'] = item_policy
    is_serial = item_policy in ['JOURNAL', 'SERIAL']

    # Publication date - use begin/end if provided, otherwise extract from publication_date
    if result['begin_publication_date'] and result['end_publication_date']:
        # Use explicitly provided begin/end dates
        begin_result = normalize_publication_date(result['begin_publication_date'], is_serial=is_serial)
        end_result = normalize_publication_date(result['end_publication_date'], is_serial=is_serial)
        result['publication_year_start'] = begin_result[0] if begin_result[0] is not None else None
        result['publication_year_end'] = end_result[1] if end_result[1] is not None else None
        # Fallback to publication_date if begin/end parsing failed
        if result['publication_year_start'] is None or result['publication_year_end'] is None:
            pub_date_result = normalize_publication_date(result['publication_date'], is_serial=is_serial)
            result['publication_year_start'] = pub_date_result[0]
            result['publication_year_end'] = pub_date_result[1]
    else:
        # Extract from publication_date
        pub_date_result = normalize_publication_date(result['publication_date'], is_serial=is_serial)
        result['publication_year_start'] = pub_date_result[0]
        result['publication_year_end'] = pub_date_result[1]

    result['edition'] = extract_first_value(get_val('Edition', ''))
    result['series'] = extract_first_value(get_val('Series', ''))

    # Item info
    result['item_copy_id'] = get_val('Item Copy Id')
    result['material_type'] = extract_first_value(get_val('Material Type', ''))
    result['call_number_type'] = extract_first_value(get_val('Permanent Call Number Type', ''))
    result['permanent_call_number_original'] = get_val('Permanent Call Number')
    result['normalized_call_number'] = get_val('Normalized Call Number')
    result['retention_note'] = get_val('Retention Note', '')

    # Parse call number
    call_number_result = parse_call_number(
        result['permanent_call_number'] or '',
        result['call_number_type'] or ''
    )
    result['call_number_classification'] = call_number_result.get('classification_type')
    result['call_number_class'] = call_number_result.get('class')
    # Map 'Permanent LC Classification Top Line' to call_number_subclass as requested
    result['call_number_subclass'] = get_val('Permanent LC Classification Top Line') or call_number_result.get('subclass')
    result['call_number_sortable'] = call_number_result.get('sortable_string')

    # Usage
    num_loans_str = get_val('Num of Loans Including Pre-Migration (In House + Not In House)', '0')
    try:
        result['num_loans'] = int(float(num_loans_str)) if num_loans_str else 0
    except (ValueError, TypeError):
        result['num_loans'] = 0

    num_loans_actual_str = get_val('Num of Loans (In House + Not In House)', '0')
    try:
        result['num_loans_actual'] = int(float(num_loans_actual_str)) if num_loans_actual_str else 0
    except (ValueError, TypeError):
        result['num_loans_actual'] = 0

    num_requests_str = get_val('Num of Requests (Total)', '0')
    try:
        result['num_requests'] = int(float(num_requests_str)) if num_requests_str else 0
    except (ValueError, TypeError):
        result['num_requests'] = 0

    # Boolean fields
    open_access_val = get_val('Open Access', '')
    result['open_access'] = str(open_access_val).lower() in ['yes', 'true', '1', 'y']

    e_copy_val = get_val('E-copy?', '')
    result['e_copy'] = str(e_copy_val).lower() in ['yes', 'true', '1', 'y']
    result['electronic_access_type'] = get_val('Electronic access type')
    result['e_overlap_collection'] = get_val('E-overlap collection')
    result['e_overlap_interface'] = normalize_e_overlap_interface(get_val('E-overlap interface'))

    retain_val = get_val('Has Committed To Retain', '')
    result['has_committed_to_retain'] = str(retain_val).lower() in ['yes', 'true', '1', 'y']

    # Dates
    result['creation_date'] = get_val('Creation Date')
    result['last_loan_date'] = get_val('Last Loan Date')

    # Subjects - store original for display, parse for faceting
    subjects_raw = get_val('Subjects', '')
    result['subjects'] = subjects_raw

    # Summary Holdings - process for coverage calculation
    summary_holdings_raw = get_val('Summary Holdings', '')
    result['summary_holdings'] = summary_holdings_raw
    # Also compute normalized begin/end years for coverage visualization
    if summary_holdings_raw:
        hold_begin, hold_end = normalize_summary_holdings(summary_holdings_raw)
        result['summary_holdings_begin_year'] = hold_begin
        result['summary_holdings_end_year'] = hold_end
    else:
        result['summary_holdings_begin_year'] = None
        result['summary_holdings_end_year'] = None

    # 590 field
    field_590_raw = get_val('590', '')
    result['field_590'] = normalize_field_590(field_590_raw)

    # Language
    language_raw = get_val('Language', '')
    result['language'] = normalize_language(language_raw)

    # Holdings
    oclc_holdings_str = get_val('OCLC Holdings', '')
    try:
        result['oclc_holdings'] = int(float(oclc_holdings_str)) if oclc_holdings_str else None
    except (ValueError, TypeError):
        result['oclc_holdings'] = None

    palci_holdings_str = get_val('PALCI Holdings', '')
    try:
        result['palci_holdings'] = int(float(palci_holdings_str)) if palci_holdings_str else None
    except (ValueError, TypeError):
        result['palci_holdings'] = None

    # Metadata
    result['created_at'] = datetime.now().isoformat()
    result['updated_at'] = datetime.now().isoformat()

    return result


def process_dataframe(df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Process a DataFrame by cleaning and normalizing all columns.

    Args:
        df: Raw DataFrame from file

    Returns:
        Tuple of (processed DataFrame, processing stats)
    """
    stats = {
        'total_rows': len(df),
        'columns_found': [],
        'columns_missing': [],
        'errors': [],
    }

    # Map columns
    column_map = {}
    for standard_col in COLUMN_MAPPINGS.keys():
        found_col = find_column(list(df.columns), standard_col)
        if found_col:
            column_map[found_col] = standard_col
            stats['columns_found'].append(f"{standard_col} (from '{found_col}')")
        else:
            stats['columns_missing'].append(standard_col)

    # Rename columns to standard names
    df_renamed = df.rename(columns=column_map)

    # Process each row
    processed_rows = []
    for idx, row in df_renamed.iterrows():
        try:
            processed_row = clean_and_normalize_row(row)
            processed_rows.append(processed_row)
        except Exception as e:
            stats['errors'].append(f"Row {idx}: {str(e)}")

    # Create processed DataFrame
    processed_df = pd.DataFrame(processed_rows)

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
