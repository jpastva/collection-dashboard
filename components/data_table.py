"""
Data table component for displaying bibliographic records.
"""

import streamlit as st
import pandas as pd
from typing import Optional, Dict, Any, List


def render_data_table(
    df: pd.DataFrame,
    key: str = "data_table",
    width: str = 'stretch'
) -> Optional[int]:
    """
    Render an interactive data table with sorting and selection.

    Args:
        df: DataFrame with bibliographic records
        key: Streamlit key for the component
        width: 'stretch' for full width, 'content' for content width

    Returns:
        Selected row index or None
    """
    if df.empty:
        st.info("No data available to display.")
        return None

    # Select columns to display in specified order
    display_columns = [
        'permanent_call_number',  # Call Number
        'title',                  # Title
        'author',                 # Author
        'publisher',              # Publisher
        'edition',                # Edition
        'publication_date',       # Publication Date
        'material_type',          # Material Type
        'num_loans',              # Loans
        'last_loan_date',         # Last Loan Date
        'oclc_holdings',          # OCLC Holdings
        'palci_holdings',         # PALCI Holdings
        'e_copy',                 # E-copy?
        'open_access',            # Open Access
        'oclc_control_number',    # OCLC Num
        'isbn_normalized',        # ISBN
        'issn_normalized',        # ISSN
        'mms_id',                 # MMS ID
        'barcode',                # Barcode
    ]

    # Filter to available columns
    available_columns = [col for col in display_columns if col in df.columns]

    # Create display dataframe
    display_df = df[available_columns].copy()

    # Rename columns for display
    column_names = {
        'permanent_call_number': 'Call Number',
        'title': 'Title',
        'author': 'Author',
        'publisher': 'Publisher',
        'edition': 'Edition',
        'publication_date': 'Publication Date',
        'material_type': 'Material Type',
        'num_loans': 'Loans',
        'last_loan_date': 'Last Loan Date',
        'oclc_holdings': 'OCLC Holdings',
        'palci_holdings': 'PALCI Holdings',
        'e_copy': 'E-copy?',
        'open_access': 'Open Access',
        'oclc_control_number': 'OCLC Num',
        'isbn_normalized': 'ISBN',
        'issn_normalized': 'ISSN',
        'mms_id': 'MMS ID',
        'barcode': 'Barcode',
    }

    display_df = display_df.rename(columns=column_names)

    event = st.dataframe(
        display_df,
        key=key,
        width=width,
        on_select="rerun",
        selection_mode="single-row",
    )

    if event.selection and len(event.selection.rows) > 0:
        return event.selection.rows[0]

    return None


def render_detail_view(record: Dict[str, Any]) -> None:
    """
    Render a detailed view of a single bibliographic record.

    Args:
        record: Dictionary containing record data
    """
    st.markdown("### Item Details")

    # Create visualization section for OCLC holdings, PALCI holdings, and circulation usage
    st.markdown("#### Holdings & Usage Visualization")

    # Create simple visualizations using Streamlit's built-in charting or metrics
    viz_col1, viz_col2, viz_col3 = st.columns(3)

    with viz_col1:
        oclc_holdings = record.get('oclc_holdings', 0) or 0
        st.metric("OCLC Holdings", f"{oclc_holdings} libraries")
        # Simple progress bar representation (normalized to a reasonable max)
        if oclc_holdings > 0:
            # Normalize to a max of 100 for display purposes
            normalized_oclc = min(oclc_holdings / 100.0, 1.0) if oclc_holdings < 100 else 1.0
            st.progress(normalized_oclc)

    with viz_col2:
        palci_holdings = record.get('palci_holdings', 0) or 0
        st.metric("PALCI Holdings", f"{palci_holdings} libraries")
        if palci_holdings > 0:
            normalized_palci = min(palci_holdings / 50.0, 1.0) if palci_holdings < 50 else 1.0
            st.progress(normalized_palci)

    with viz_col3:
        num_loans = record.get('num_loans', 0) or 0
        st.metric("Circulation Usage", f"{num_loans} loans")
        if num_loans > 0:
            # Normalize to a max of 50 loans for display purposes
            normalized_loans = min(num_loans / 50.0, 1.0) if num_loans < 50 else 1.0
            st.progress(normalized_loans)

    st.divider()

    # Create two columns for main information
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### Bibliographic Information")
        st.markdown(f"**Title:** {record.get('title', 'N/A')}")
        st.markdown(f"**Author:** {record.get('author', 'N/A') or 'N/A'}")
        if record.get('author_contributor'):
            st.markdown(f"**Contributor:** {record.get('author_contributor')}")
        st.markdown(f"**Publisher:** {record.get('publisher', 'N/A') or 'N/A'}")
        st.markdown(f"**Publication Date:** {record.get('publication_date', 'N/A') or 'N/A'}")
        if record.get('edition'):
            st.markdown(f"**Edition:** {record.get('edition')}")
        if record.get('series'):
            st.markdown(f"**Series:** {record.get('series')}")

    with col2:
        st.markdown("#### Item Information")
        st.markdown(f"**Library:** {record.get('library_name', 'N/A') or 'N/A'}")
        st.markdown(f"**Location:** {record.get('location_name', 'N/A') or 'N/A'}")
        st.markdown(f"**Material Type:** {record.get('material_type', 'N/A') or 'N/A'}")
        st.markdown(f"**Call Number:** {record.get('permanent_call_number', 'N/A') or 'N/A'}")
        if record.get('call_number_type'):
            st.markdown(f"**Call Number Type:** {record.get('call_number_type')}")
        if record.get('item_copy_id'):
            st.markdown(f"**Copy ID:** {record.get('item_copy_id')}")

    # Identifiers section
    st.markdown("#### Identifiers")
    id_cols = st.columns(4)
    with id_cols[0]:
        st.markdown(f"**MMS ID:** {record.get('mms_id', 'N/A') or 'N/A'}")
    with id_cols[1]:
        st.markdown(f"**Barcode:** {record.get('barcode', 'N/A') or 'N/A'}")
    with id_cols[2]:
        st.markdown(f"**ISBN:** {record.get('isbn', 'N/A') or 'N/A'}")
        # Also show normalized ISBN if different
        isbn_norm = record.get('isbn_normalized')
        if isbn_norm and isbn_norm != record.get('isbn'):
            st.markdown(f"*Normalized:* {isbn_norm}")
    with id_cols[3]:
        st.markdown(f"**ISSN:** {record.get('issn', 'N/A') or 'N/A'}")
        # Also show normalized ISSN if different
        issn_norm = record.get('issn_normalized')
        if issn_norm and issn_norm != record.get('issn'):
            st.markdown(f"*Normalized:* {issn_norm}")

    if record.get('oclc_control_number'):
        st.markdown(f"**OCLC Control Number (035a):** {record.get('oclc_control_number')}")

    # Usage section
    st.markdown("#### Usage Statistics")
    usage_cols = st.columns(3)
    with usage_cols[0]:
        st.metric("Total Loans", record.get('num_loans', 0))
    with usage_cols[1]:
        st.metric("Creation Date", record.get('creation_date', 'N/A') or 'N/A')
    with usage_cols[2]:
        st.metric("Last Loan Date", record.get('last_loan_date', 'N/A') or 'N/A')

    # Additional info
    st.markdown("#### Additional Information")
    info_cols = st.columns(3)
    with info_cols[0]:
        open_access = "Yes" if record.get('open_access') else "No"
        st.markdown(f"**Open Access:** {open_access}")
    with info_cols[1]:
        e_copy = "Yes" if record.get('e_copy') else "No"
        st.markdown(f"**E-copy?:** {e_copy}")
    with info_cols[2]:
        retain = "Yes" if record.get('has_committed_to_retain') else "No"
        st.markdown(f"**Committed to Retain:** {retain}")

    # Holdings info
    holdings_cols = st.columns(2)
    with holdings_cols[0]:
        if record.get('oclc_holdings') is not None:
            st.markdown(f"**OCLC Holdings:** {record.get('oclc_holdings')} libraries")
    with holdings_cols[1]:
        if record.get('palci_holdings') is not None:
            st.markdown(f"**PALCI Holdings:** {record.get('palci_holdings')} libraries")

    # Subjects
    if record.get('subjects'):
        st.markdown("#### Subjects")
        from utils.cleaners import parse_subjects
        subjects = parse_subjects(record.get('subjects', ''))
        for subject in subjects:
            st.markdown(f"- {subject}")

    # Call number classification details
    if record.get('call_number_classification'):
        st.markdown("#### Call Number Classification")
        st.markdown(f"**Classification System:** {record.get('call_number_classification')}")
        if record.get('call_number_class'):
            st.markdown(f"**Class:** {record.get('call_number_class')}")
        if record.get('call_number_subclass'):
            st.markdown(f"**Subclass:** {record.get('call_number_subclass')}")


def render_summary_cards(df: pd.DataFrame) -> None:
    """
    Render summary statistic cards.

    Args:
        df: DataFrame with bibliographic records
    """
    from components.visualizations import create_summary_cards

    cards = create_summary_cards(df)

    if not cards:
        return

    # Create columns for cards
    cols = st.columns(min(len(cards), 4))

    for i, card in enumerate(cards):
        with cols[i % len(cols)]:
            st.metric(
                label=card['title'],
                value=card['value'],
            )
