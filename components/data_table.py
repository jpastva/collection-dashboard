"""
Data table component for displaying bibliographic records.
"""

import streamlit as st
import pandas as pd
from typing import Optional, Dict, Any, List
from datetime import datetime


def _compute_coverage(row: pd.Series) -> Optional[float]:
    """
    Compute coverage percentage from summary holdings and publication date.
    Returns percentage (0-100) or None if insufficient data.
    """
    from utils.cleaners import normalize_summary_holdings, normalize_publication_date

    # Get summary holdings raw string
    holdings_raw = row.get('Summary Holdings')
    if not holdings_raw or not isinstance(holdings_raw, str) or not holdings_raw.strip():
        return None
    # Normalize summary holdings to get begin and end years
    hold_begin, hold_end = normalize_summary_holdings(holdings_raw.strip())
    if hold_begin is None or hold_end is None:
        return None

    # Get publication date fields
    begin_date = row.get('Begin Pub Date')
    end_date = row.get('End Pub Date')
    pub_date = row.get('Publication Date')

    # Determine if serial (assuming all items are serials for coverage calculation)
    is_serial = True

    # Compute publication year start and end
    if begin_date and end_date and \
       isinstance(begin_date, str) and begin_date.strip() and \
       isinstance(end_date, str) and end_date.strip():
        # Use explicitly provided begin/end dates
        begin_result = normalize_publication_date(begin_date.strip(), is_serial=is_serial)
        end_result = normalize_publication_date(end_date.strip(), is_serial=is_serial)
        pub_begin = begin_result[0] if begin_result[0] is not None else None
        pub_end = end_result[1] if end_result[1] is not None else None
        # Fallback to publication_date if begin/end parsing failed
        if pub_begin is None or pub_end is None:
            pub_result = normalize_publication_date(pub_date.strip() if isinstance(pub_date, str) else pub_date, is_serial=is_serial)
            pub_begin = pub_result[0]
            pub_end = pub_result[1]
    else:
        # Extract from publication_date
        pub_result = normalize_publication_date(pub_date.strip() if isinstance(pub_date, str) else pub_date, is_serial=is_serial)
        pub_begin = pub_result[0]
        pub_end = pub_result[1]

    # If any missing, cannot compute
    if pub_begin is None or pub_end is None:
        return None

    # If publication end missing, treat as ongoing -> use current year
    if pub_end is None:
        pub_end = datetime.now().year

    # Ensure years are integers
    try:
        hold_begin = int(hold_begin)
        hold_end = int(hold_end)
        pub_begin = int(pub_begin)
        pub_end = int(pub_end)
    except (ValueError, TypeError):
        return None

    # Validate ranges
    if hold_end < hold_begin or pub_end < pub_begin:
        return None

    held_years = hold_end - hold_begin + 1
    pub_years = pub_end - pub_begin + 1

    if pub_years <= 0:
        return None

    coverage = (held_years / pub_years) * 100.0
    # Cap at 100
    if coverage > 100:
        coverage = 100.0
    return coverage


def render_data_table(
    df: pd.DataFrame,
    key: str = "data_table",
    width: str = 'stretch'
) -> Optional[int]:
    """
    Render an interactive data table with sorting and selection.

    Args:
        df: DataFrame with bibliographic records (using Google Sheet column names)
        key: Streamlit key for the component
        width: 'stretch' for full width, 'content' for content width

    Returns:
        Selected row index or None
    """
    if df.empty:
        st.info("No data available to display.")
        return None

    # Select columns to display in specified order (using Google Sheet column names)
    display_columns = [
        'Title (Normalized)',   # Title (Normalized)
        'Title',                # Title
        'Publication Date',     # Publication Date
        'Begin Pub Date',       # Begin Publication Date
        'End Pub Date',         # End Publication Date
        'Type of date',         # Type of Date
        'Publisher',            # Publisher
        'Publication Place',    # Publication Place
        'Edition',              # Edition
        'Series',               # Series
        'Author',               # Author
        'Author (contributor)', # Author (Contributor)
        'Summary Holdings',     # Summary Holdings
        '590',                  # 590
        'Num of Loans Including Pre-Migration (In House + Not In House)',  # Num of Loans Including Pre-Migration (In House + Not In House)
        'Loans (In House + Not In House)',                          # Num of Loans (In House + Not In House)
        'Num of Requests (Total)',         # Num of Requests (Total)
        'Last Loan Date',           # Last Loan Date
        'E-copy?',                  # E-copy?
        'eR access type',           # E-overlap collection (Note: checking mapping)
        'eR interface',             # E-overlap interface (Note: checking mapping)
        'Barcode',                  # Barcode
        'ISSN (Normalized)',        # ISSN (Normalized)
        'ISSN',                     # ISSN
        'MMS Id',                   # MMS Id
        'ISBN',                     # ISBN
        'OCLC Control Number (035a)', # OCLC Control Number (035a)
        'Language',                 # Language
        'Subjects',                 # Subjects
        'Modification Date',        # Creation Date (Note: checking mapping)
        'Permanent LC Classification Top Line',  # Permanent LC Classification Top Line
        'OCLC Holdings',            # OCLC Holdings
        'PALCI Holdings',           # PALCI Holdings
        'Item Copy Id',             # Item ID
        'Decision',                 # DECISION
        'Selector',                 # Selector (placeholder)
        'Retention Note',           # Notes
    ]

    # Filter to available columns
    available_columns = [col for col in display_columns if col in df.columns]

    # Create display dataframe
    display_df = df[available_columns].copy()

    # Compute Coverage column
    coverage_vals = []
    for _, row in display_df.iterrows():
        cov = _compute_coverage(row)
        coverage_vals.append(cov if cov is not None else None)
    display_df['Coverage'] = coverage_vals

    # Define display names for columns (including Coverage)
    column_names = {
        'Title (Normalized)': 'Title (Normalized)',
        'Title': 'Title',
        'Publication Date': 'Publication Date',
        'Begin Pub Date': 'Begin Publication Date',
        'End Pub Date': 'End Publication Date',
        'Type of date': 'Type of Date',
        'Publisher': 'Publisher',
        'Publication Place': 'Publication Place',
        'Edition': 'Edition',
        'Series': 'Series',
        'Author': 'Author',
        'Author (contributor)': 'Author (Contributor)',
        'Summary Holdings': 'Summary Holdings',
        '590': '590',
        'Num of Loans Including Pre-Migration (In House + Not In House)': 'Num of Loans Including Pre-Migration (In House + Not In House)',
        'Loans (In House + Not In House)': 'Num of Loans (In House + Not In House)',
        'Num of Requests (Total)': 'Num of Requests (Total)',
        'Last Loan Date': 'Last Loan Date',
        'E-copy?': 'E-copy?',
        'eR access type': 'E-overlap collection',
        'eR interface': 'E-overlap interface',
        'Barcode': 'Barcode',
        'ISSN (Normalized)': 'ISSN (Normalized)',
        'ISSN': 'ISSN',
        'MMS Id': 'MMS Id',
        'ISBN': 'ISBN',
        'OCLC Control Number (035a)': 'OCLC Control Number (035a)',
        'Language': 'Language',
        'Subjects': 'Subjects',
        'Modification Date': 'Creation Date',
        'Permanent LC Classification Top Line': 'Permanent LC Classification Top Line',
        'OCLC Holdings': 'OCLC Holdings',
        'PALCI Holdings': 'PALCI Holdings',
        'Item Copy Id': 'Item ID',
        'Decision': 'DECISION',
        'Selector': 'Selector',
        'Retention Note': 'Notes',
        'Coverage': 'Coverage (%)',
    }

    # Rename columns for display (though many are already correct)
    display_df = display_df.rename(columns=column_names)

    # Reorder columns to match the order in display_columns + Coverage at end
    ordered_display_names = [column_names[col] for col in display_columns] + ['Coverage (%)']
    # Ensure we only keep columns that exist
    ordered_display_names = [name for name in ordered_display_names if name in display_df.columns]
    display_df = display_df[ordered_display_names]

    # Configure column types for proper display (optional)
    # We'll let Streamlit decide; but we can format numbers
    # For simplicity, we'll just show the dataframe.

    event = st.dataframe(
        display_df,
        key=key,
        width=width,
        on_select="rerun",
        selection_mode="single-row",
    )

    selected_idx = None
    if event.selection and len(event.selection.rows) > 0:
        selected_idx = event.selection.rows[0]
        # Store selected index in session state to show dialog
        st.session_state['selected_record_idx'] = selected_idx

    # Show dialog if a record is selected
    if 'selected_record_idx' in st.session_state:
        idx = st.session_state['selected_record_idx']
        # Ensure idx is within bounds
        if 0 <= idx < len(df):
            record = df.iloc[idx].to_dict()
            _show_record_dialog(record)

    return selected_idx


def _show_record_dialog(record: Dict[str, Any]) -> None:
    """
    Show a dialog with a nicely formatted data summary card for a record.
    """
    @st.dialog("Record Details")
    def show_dialog():
        # Use a nice layout
        title = record.get('Title', record.get('title', 'N/A'))
        st.markdown(f"### {title}")
        st.divider()

        # Create two columns for main info
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("**Bibliographic Information**")
            author = record.get('Author', 'N/A')
            st.markdown(f"**Author:** {author or 'N/A'}")
            author_contrib = record.get('Author (contributor)')
            if author_contrib:
                st.markdown(f"**Contributor:** {author_contrib}")
            publisher = record.get('Publisher', 'N/A')
            st.markdown(f"**Publisher:** {publisher or 'N/A'}")
            pub_date = record.get('Publication Date', 'N/A')
            st.markdown(f"**Publication Date:** {pub_date or 'N/A'}")
            begin_date = record.get('Begin Pub Date', 'N/A')
            st.markdown(f"**Begin Publication Date:** {begin_date or 'N/A'}")
            end_date = record.get('End Pub Date', 'N/A')
            st.markdown(f"**End Publication Date:** {end_date or 'N/A'}")
            date_type = record.get('Type of date', 'N/A')
            st.markdown(f"**Type of Date:** {date_type or 'N/A'}")
            edition = record.get('Edition', 'N/A')
            st.markdown(f"**Edition:** {edition or 'N/A'}")
            series = record.get('Series', 'N/A')
            st.markdown(f"**Series:** {series or 'N/A'}")

        with col2:
            st.markdown("**Item & Identifiers**")
            pub_place = record.get('Publication Place', 'N/A')
            st.markdown(f"**Publication Place:** {pub_place or 'N/A'}")
            material_type = record.get('Material Type', 'N/A')
            st.markdown(f"**Material Type:** {material_type or 'N/A'}")
            call_number = record.get('Permanent Call Number', 'N/A')
            st.markdown(f"**Call Number:** {call_number or 'N/A'}")
            call_number_type = record.get('Permanent Call Number Type', 'N/A')
            st.markdown(f"**Call Number Type:** {call_number_type or 'N/A'}")
            copy_id = record.get('Item Copy Id', 'N/A')
            st.markdown(f"**Copy ID:** {copy_id or 'N/A'}")
            mms_id = record.get('MMS Id', 'N/A')
            st.markdown(f"**MMS ID:** {mms_id or 'N/A'}")
            barcode = record.get('Barcode', 'N/A')
            st.markdown(f"**Barcode:** {barcode or 'N/A'}")
            isbn = record.get('ISBN', 'N/A')
            st.markdown(f"**ISBN:** {isbn or 'N/A'}")
            isbn_norm = record.get('ISBN (Normalized)')
            if isbn_norm and isbn_norm != isbn:
                st.markdown(f"*Normalized ISBN:* {isbn_norm}")
            issn = record.get('ISSN', 'N/A')
            st.markdown(f"**ISSN:** {issn or 'N/A'}")
            issn_norm = record.get('ISSN (Normalized)')
            if issn_norm and issn_norm != issn:
                st.markdown(f"*Normalized ISSN:* {issn_norm}")
            oclc = record.get('OCLC Control Number (035a)', 'N/A')
            st.markdown(f"**OCLC Control Number (035a):** {oclc or 'N/A'}")
            language = record.get('Language', 'N/A')
            st.markdown(f"**Language:** {language or 'N/A'}")

        st.divider()

        # Summary Holdings and Coverage
        st.markdown("**Holdings & Coverage**")
        summary_holdings = record.get('Summary Holdings', 'N/A')
        st.markdown(f"**Summary Holdings:** {summary_holdings or 'N/A'}")
        hold_begin = record.get('Summary Holdings Begin Year')
        hold_end = record.get('Summary Holdings End Year')
        if hold_begin is not None and hold_end is not None:
            st.markdown(f"**Holdings Span:** {hold_begin} – {hold_end}")
        pub_begin = record.get('Publication Year Start')
        pub_end = record.get('Publication Year End')
        if pub_begin is not None and pub_end is not None:
            st.markdown(f"**Publication Span:** {pub_begin} – {pub_end}")
        # Compute coverage
        cov = _compute_coverage(pd.Series(record))
        if cov is not None:
            st.markdown(f"**Coverage:** {cov:.1f}%")

        st.divider()

        # Subjects
        subjects_field = record.get('Subjects')
        if subjects_field:
            st.markdown("**Subjects**")
            from utils.cleaners import parse_subjects
            subjects = parse_subjects(subjects_field)
            for subject in subjects:
                st.markdown(f"- {subject}")

        st.divider()

        # Usage and Holdings
        usage_col1, usage_col2, usage_col3 = st.columns(3)
        with usage_col1:
            loans_pre = record.get('Num of Loans Including Pre-Migration (In House + Not In House)', 0)
            st.metric("Loans (Including Pre-Migration)", loans_pre)
        with usage_col2:
            loans_actual = record.get('Loans (In House + Not In House)', 0)
            st.metric("Loans (Actual)", loans_actual)
        with usage_col3:
            requests = record.get('Num of Requests (Total)', 0)
            st.metric("Requests (Total)", requests)

        last_loan = record.get('Last Loan Date', 'N/A')
        st.metric("Last Loan Date", last_loan or 'N/A')

        st.markdown("**Electronic & Access**")
        e_copy = "Yes" if record.get('E-copy?', False) else "No"
        st.markdown(f"**E-copy?:** {e_copy}")
        e_overlap_coll = record.get('E-overlap collection', 'N/A')
        st.markdown(f"**E-overlap collection:** {e_overlap_coll or 'N/A'}")
        e_overlap_inter = record.get('E-overlap interface', 'N/A')
        st.markdown(f"**E-overlap interface:** {e_overlap_inter or 'N/A'}")
        open_access = "Yes" if record.get('Open Access', False) else "No"
        st.markdown(f"**Open Access:** {open_access}")

        st.divider()

        # Holdings
        hold_col1, hold_col2 = st.columns(2)
        with hold_col1:
            oclc_holdings = record.get('OCLC Holdings')
            if oclc_holdings is not None:
                st.metric("OCLC Holdings", f"{oclc_holdings} libraries")
        with hold_col2:
            palci_holdings = record.get('PALCI Holdings')
            if palci_holdings is not None:
                st.metric("PALCI Holdings", f"{palci_holdings} libraries")

        # Close button
        if st.button("Close"):
            if 'selected_record_idx' in st.session_state:
                del st.session_state['selected_record_idx']
            st.rerun()

    show_dialog()


def render_detail_view(record: Dict[str, Any]) -> None:
    """
    Render a detailed view of a single bibliographic record.
    (Kept for backward compatibility; may not be used now.)
    """
    st.markdown("### Item Details")

    # Create visualization section for OCLC holdings, PALCI holdings, and circulation usage
    st.markdown("#### Holdings & Usage Visualization")

    # Create simple visualizations using Streamlit's built-in charting or metrics
    viz_col1, viz_col2, viz_col3 = st.columns(3)

    with viz_col1:
        oclc_holdings = record.get('OCLC Holdings', 0) or 0
        st.metric("OCLC Holdings", f"{oclc_holdings} libraries")
        # Simple progress bar representation (normalized to a reasonable max)
        if oclc_holdings > 0:
            # Normalize to a max of 100 for display purposes
            normalized_oclc = min(oclc_holdings / 100.0, 1.0) if oclc_holdings < 100 else 1.0
            st.progress(normalized_oclc)

    with viz_col2:
        palci_holdings = record.get('PALCI Holdings', 0) or 0
        st.metric("PALCI Holdings", f"{palci_holdings} libraries")
        if palci_holdings > 0:
            normalized_palci = min(palci_holdings / 50.0, 1.0) if palci_holdings < 50 else 1.0
            st.progress(normalized_palci)

    with viz_col3:
        num_loans = record.get('Num of Loans Including Pre-Migration (In House + Not In House)', 0) or 0
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
        st.markdown(f"**Title:** {record.get('Title', 'N/A')}")
        st.markdown(f"**Author:** {record.get('Author', 'N/A') or 'N/A'}")
        if record.get('Author (contributor)'):
            st.markdown(f"**Contributor:** {record.get('Author (contributor)')}")
        st.markdown(f"**Publisher:** {record.get('Publisher', 'N/A') or 'N/A'}")
        st.markdown(f"**Publication Date:** {record.get('Publication Date', 'N/A') or 'N/A'}")
        if record.get('Edition'):
            st.markdown(f"**Edition:** {record.get('Edition')}")
        if record.get('Series'):
            st.markdown(f"**Series:** {record.get('Series')}")

    with col2:
        st.markdown("#### Item Information")
        st.markdown(f"**Library:** {record.get('Library Name', 'N/A') or 'N/A'}")
        st.markdown(f"**Location:** {record.get('Location Name', 'N/A') or 'N/A'}")
        st.markdown(f"**Material Type:** {record.get('Material Type', 'N/A') or 'N/A'}")
        st.markdown(f"**Call Number:** {record.get('Permanent Call Number', 'N/A') or 'N/A'}")
        if record.get('Permanent Call Number Type'):
            st.markdown(f"**Call Number Type:** {record.get('Permanent Call Number Type')}")
        if record.get('Item Copy Id'):
            st.markdown(f"**Copy ID:** {record.get('Item Copy Id')}")

    # Identifiers section
    st.markdown("#### Identifiers")
    id_cols = st.columns(4)
    with id_cols[0]:
        st.markdown(f"**MMS ID:** {record.get('MMS Id', 'N/A') or 'N/A'}")
    with id_cols[1]:
        st.markdown(f"**Barcode:** {record.get('Barcode', 'N/A') or 'N/A'}")
    with id_cols[2]:
        st.markdown(f"**ISBN:** {record.get('ISBN', 'N/A') or 'N/A'}")
        # Also show normalized ISBN if different
        isbn_norm = record.get('ISBN (Normalized)')
        if isbn_norm and isbn_norm != record.get('ISBN'):
            st.markdown(f"*Normalized:* {isbn_norm}")
    with id_cols[3]:
        st.markdown(f"**ISSN:** {record.get('ISSN', 'N/A') or 'N/A'}")
        # Also show normalized ISSN if different
        issn_norm = record.get('ISSN (Normalized)')
        if issn_norm and issn_norm != record.get('ISSN'):
            st.markdown(f"*Normalized:* {issn_norm}")

    if record.get('OCLC Control Number (035a)'):
        st.markdown(f"**OCLC Control Number (035a):** {record.get('OCLC Control Number (035a)')}")

    # Usage section
    st.markdown("#### Usage Statistics")
    usage_cols = st.columns(3)
    with usage_cols[0]:
        st.metric("Total Loans", record.get('Num of Loans Including Pre-Migration (In House + Not In House)', 0))
    with usage_cols[1]:
        st.metric("Creation Date", record.get('Creation Date', 'N/A') or 'N/A')
    with usage_cols[2]:
        st.metric("Last Loan Date", record.get('Last Loan Date', 'N/A') or 'N/A')

    # Additional info
    st.markdown("#### Additional Information")
    info_cols = st.columns(3)
    with info_cols[0]:
        open_access = "Yes" if record.get('Open Access', False) else "No"
        st.markdown(f"**Open Access:** {open_access}")
    with info_cols[1]:
        e_copy = "Yes" if record.get('E-copy?', False) else "No"
        st.markdown(f"**E-copy?:** {e_copy}")
    with info_cols[2]:
        retain = "Yes" if record.get('Has Committed To Retain', False) else "No"
        st.markdown(f"**Committed to Retain:** {retain}")

    # Holdings info
    holdings_cols = st.columns(2)
    with holdings_cols[0]:
        if record.get('OCLC Holdings') is not None:
            st.markdown(f"**OCLC Holdings:** {record.get('OCLC Holdings')} libraries")
    with holdings_cols[1]:
        if record.get('PALCI Holdings') is not None:
            st.markdown(f"**PALCI Holdings:** {record.get('PALCI Holdings')} libraries")

    # Subjects
    if record.get('Subjects'):
        st.markdown("#### Subjects")
        from utils.cleaners import parse_subjects
        subjects = parse_subjects(record.get('Subjects', ''))
        for subject in subjects:
            st.markdown(f"- {subject}")

    # Call number classification details
    if record.get('Call Number Classification'):
        st.markdown("#### Call Number Classification")
        st.markdown(f"**Classification System:** {record.get('Call Number Classification')}")
        if record.get('call_number_class'):
            st.markdown(f"**Class:** {record.get('call_number_class')}")
        if record.get('Permanent LC Classification Top Line'):
            st.markdown(f"**Subclass:** {record.get('Permanent LC Classification Top Line')}")


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