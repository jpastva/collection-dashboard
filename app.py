"""
Library Dashboard Application

A Streamlit application for parsing, cleaning, normalizing, and visualizing
bibliographic records from library resources.
"""

import streamlit as st
import pandas as pd
import os
import sys

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from models.database import init_db
from utils.data_import import process_dataframe
from components.visualizations import (
    create_usage_chart,
    create_age_distribution_chart,
    create_subject_coverage_chart,
    create_lc_class_coverage_chart,
    create_oclc_holdings_chart,
    create_publication_timeline_chart,
    create_summary_cards,
)
from components.data_table import render_data_table, render_detail_view, render_summary_cards
from components.facet_panel import render_facet_panel, apply_filters_to_dataframe
from components.export import export_to_csv, export_to_excel, create_summary_report, export_report_to_excel
from components.reports import render_report_menu, generate_report, render_report_display


@st.cache_data(show_spinner="Loading data from Google Sheet…", ttl=600)
def load_data_from_google_sheet():
    """Load data from the public Google Sheet (cached)."""
    # Try multiple URLs that work for public sheets
    sheet_id = "1R-z7H9ciFaK_sNvTEKbk4S_k-SL7Xogxq2VG8Yo1Fz0"
    urls = [
        # Export CSV (no gid, defaults to first sheet)
        f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv",
        # Export CSV with gid=0 (explicit first sheet)
        f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv&gid=0",
        # Alternative gviz/tq endpoint (requires sheet to be published)
        f"https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv&sheet=Sheet1",
        # Published CSV export (if sheet published to web)
        f"https://docs.google.com/spreadsheets/d/{sheet_id}/pub?output=csv",
    ]
    last_error = None
    for url in urls:
        try:
            # Read the CSV data, ensuring all columns are read as strings to avoid type issues
            raw_df = pd.read_csv(url, dtype=str)
            # Process the data using the same function used for file uploads
            processed_df, _ = process_dataframe(raw_df)
            return processed_df
        except Exception as e:
            last_error = e
            continue
    # If all URLs failed
    st.error(f"Failed to load data from Google Sheet: {last_error}")
    return pd.DataFrame()


def initialize_session_state():
    """Initialize session state variables."""
    if 'data_loaded' not in st.session_state:
        st.session_state.data_loaded = False
    if 'data_df' not in st.session_state:
        st.session_state.data_df = pd.DataFrame()
    if 'import_stats' not in st.session_state:
        st.session_state.import_stats = {}
    if 'active_filters' not in st.session_state:
        st.session_state.active_filters = {}
    if 'selected_record' not in st.session_state:
        st.session_state.selected_record = None


def render_header():
    """Render the application header."""
    col1, col2 = st.columns([4, 1])
    with col1:
        st.title("📚 Library Dashboard")
        st.markdown("*Browse, filter, and analyze your library collection*")
    with col2:
        # Using a placeholder image since the OCLC URL may be unstable or blocked by some browsers/environments
        st.image("https://via.placeholder.com/150x50?text=Green+Glass+Logo", width=150)
    st.divider()


def render_main_dashboard(df: pd.DataFrame):
    """Render the main dashboard view."""
    # Sidebar: data management and filters
    with st.sidebar:
        st.markdown("### Data Management")
        st.metric("Total Records", len(df))

        if st.button("Refresh Data from Google Sheet", width='stretch'):
            # Clear cached data to force a fresh fetch
            load_data_from_google_sheet.clear()
            st.success("Cache cleared – fetching fresh data...")
            st.rerun()

        if st.button("Clear Data & Start Over", width='stretch'):
            st.session_state.data_loaded = False
            st.session_state.data_df = pd.DataFrame()
            st.session_state.import_stats = {}
            st.session_state.active_filters = {}
            # Also clear filter session state keys
            filter_keys = [
                'filter_item_policy',
                'filter_material_type',
                'filter_lc_class',
                'filter_decade',
                'filter_usage',
                'filter_subjects',
                'filter_retain',
                'filter_access',
                'subject_search',
                'selected_record_idx',
                'custom_report_columns',
                'custom_report_sort_column',
                'custom_report_sort_ascending',
                'filter_item_id',
                'filter_decision',
                'filter_selector',
                'filter_notes',
                'filter_oclc_holdings',
                'filter_palci_holdings',
                'filter_ecopy',
                'filter_hathitrust'
            ]
            for key in filter_keys:
                if key in st.session_state:
                    del st.session_state[key]
            st.rerun()

        st.divider()

        # Show import stats (if any)
        if st.session_state.import_stats:
            stats = st.session_state.import_stats
            st.markdown("#### Import Statistics")
            st.info(f"Records loaded: {stats.get('records_imported', 0)}")

        st.divider()
        st.markdown("### Filters")
        # Render facet panel in sidebar
        filters = render_facet_panel(df, key_suffix="sidebar")
        filtered_df = apply_filters_to_dataframe(df, filters)

    # Summary cards (show overall statistics, unfiltered)
    st.divider()
    render_summary_cards(df)

    # Main area: tabs
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📊 Data View",
        "📈 Visualizations",
        "📋 Reports",
        "📥 Export",
        "ℹ️ About"
    ])

    with tab1:
        render_data_view_tab(df, filtered_df)

    with tab2:
        render_visualizations_tab(df, filtered_df)

    with tab3:
        render_reports_tab(df, filtered_df)

    with tab4:
        render_export_tab(df, filtered_df)

    with tab5:
        render_about_tab()


def render_data_view_tab(df: pd.DataFrame, filtered_df: pd.DataFrame):
    """Render the data view tab."""
    st.markdown("### Browse Collection")

    # Show filter results count
    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown(f"Showing **{len(filtered_df):,}** of **{len(df):,}** items")
    with col2:
        # We could compute active filters count, but we already have it in facet panel; skip for now
        pass

    st.divider()

    # Data table with selection
    render_data_table(filtered_df)


def render_visualizations_tab(df: pd.DataFrame, filtered_df: pd.DataFrame):
    """Render the visualizations tab."""
    st.markdown("### Data Visualizations")

    # Chart selection
    chart_type = st.selectbox(
        "Select Visualization",
        options=[
            "Circulation Usage",
            "Material Age Distribution",
            "Subject Coverage",
            "LC Classification Coverage",
            "Publication Timeline",
            "OCLC Holdings",
            "Request Usage",
            "PALCI Holdings",
            "Last Loan Date",
            "LC Subclass Coverage",
            "E-Copy Availability",
        ]
    )

    st.divider()

    # Render selected chart
    if chart_type == "Circulation Usage":
        fig = create_usage_chart(filtered_df)
        st.plotly_chart(fig, width='stretch')

    elif chart_type == "Material Age Distribution":
        fig = create_age_distribution_chart(filtered_df)
        st.plotly_chart(fig, width='stretch')

    elif chart_type == "Subject Coverage":
        fig = create_subject_coverage_chart(filtered_df)
        st.plotly_chart(fig, width='stretch')

    elif chart_type == "LC Classification Coverage":
        fig = create_lc_class_coverage_chart(filtered_df)
        st.plotly_chart(fig, width='stretch')

    elif chart_type == "Publication Timeline":
        fig = create_publication_timeline_chart(filtered_df)
        st.plotly_chart(fig, width='stretch')

    elif chart_type == "OCLC Holdings":
        fig = create_oclc_holdings_chart(filtered_df)
        st.plotly_chart(fig, width='stretch')

    elif chart_type == "Request Usage":
        from components.visualizations import create_requests_chart
        fig = create_requests_chart(filtered_df)
        st.plotly_chart(fig, width='stretch')

    elif chart_type == "PALCI Holdings":
        from components.visualizations import create_palci_holdings_chart
        fig = create_palci_holdings_chart(filtered_df)
        st.plotly_chart(fig, width='stretch')

    elif chart_type == "Last Loan Date":
        from components.visualizations import create_last_loan_date_chart
        fig = create_last_loan_date_chart(filtered_df)
        st.plotly_chart(fig, width='stretch')

    elif chart_type == "LC Subclass Coverage":
        from components.visualizations import create_lc_subclass_chart
        fig = create_lc_subclass_chart(filtered_df)
        st.plotly_chart(fig, width='stretch')

    elif chart_type == "E-Copy Availability":
        from components.visualizations import create_ecopy_chart
        fig = create_ecopy_chart(filtered_df)
        st.plotly_chart(fig, width='stretch')

    # Show all charts option
    st.divider()
    if st.checkbox("Show All Visualizations"):
        st.markdown("#### Circulation Usage")
        st.plotly_chart(create_usage_chart(filtered_df), width='stretch', key='viz_usage_all')

        st.markdown("#### Material Age Distribution")
        st.plotly_chart(create_age_distribution_chart(filtered_df), width='stretch', key='viz_age_all')

        st.markdown("#### Subject Coverage")
        st.plotly_chart(create_subject_coverage_chart(filtered_df), width='stretch', key='viz_subject_all')

        st.markdown("#### LC Classification Coverage")
        st.plotly_chart(create_lc_class_coverage_chart(filtered_df), width='stretch', key='viz_lc_all')

        st.markdown("#### Publication Timeline")
        st.plotly_chart(create_publication_timeline_chart(filtered_df), width='stretch', key='viz_timeline_all')


def render_reports_tab(df: pd.DataFrame, filtered_df: pd.DataFrame):
    """Render the reports tab."""
    st.markdown("### Generate Reports")

    # Report generator
    report = render_report_menu(filtered_df)  # Pass filtered_df to report menu

    if report:
        st.divider()
        render_report_display(report)


def render_export_tab(df: pd.DataFrame, filtered_df: pd.DataFrame):
    """Render the export tab."""
    st.markdown("### Export Data")

    # Export format selection
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### Export Options")

        export_format = st.radio(
            "Select format",
            options=["CSV", "Excel"],
            horizontal=True
        )

        # Column selection
        available_columns = [
            'Title', 'Author', 'Publisher', 'Publication Date',
            'Material Type', 'Permanent Call Number', 'call_number_classification',
            'Num of Loans Including Pre-Migration (In House + Not In House)', 'ISBN (Normalized)', 'ISSN (Normalized)', 'OCLC Control Number (035a)',
            'MMS Id', 'Barcode', 'Subjects', 'Has Committed To Retain',
            'Open Access', 'Library Name', 'Location Name'
        ]
        available = [col for col in available_columns if col in filtered_df.columns]

        selected_columns = st.multiselect(
            "Select columns to export",
            options=available,
            default=available
        )

    with col2:
        st.markdown("#### Export Summary")
        st.metric("Records to export", len(filtered_df))
        if selected_columns:
            st.metric("Columns", len(selected_columns))

    st.divider()

    # Generate export
    if st.button("Download Export", type="primary", width='stretch'):
        if selected_columns:
            export_df = filtered_df[selected_columns]
        else:
            export_df = filtered_df

        if export_format == "CSV":
            csv_data = export_to_csv(export_df)
            st.download_button(
                label="Download CSV",
                data=csv_data,
                file_name="library_data_export.csv",
                mime="text/csv",
                width='stretch',
            )
        else:
            excel_data = export_to_excel(export_df)
            st.download_button(
                label="Download Excel",
                data=excel_data,
                file_name="library_data_export.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                width='stretch',
            )

    # Export summary report
    st.divider()
    st.markdown("#### Export Summary Report")

    if st.button("Generate & Download Summary Report"):
        report_data = create_summary_report(filtered_df)
        excel_data = export_report_to_excel(filtered_df, report_data)
        st.download_button(
            label="Download Summary Report (Excel)",
            data=excel_data,
            file_name="library_summary_report.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            width='stretch',
        )


def render_about_tab():
    """Render the about tab."""
    st.markdown("### About Library Dashboard")

    st.markdown("""
    Library Dashboard is a comprehensive application for managing and analyzing
    bibliographic records from library collections.

    #### Features

    - **Data Import**: Load data directly from a public Google Sheet
    - **Data Cleaning**: Automatic normalization of:
      - OCLC Control Numbers (removing prefixes and leading zeros)
      - ISBN, ISSN, Barcode, and MMS ID normalization
      - Title and author name cleanup
      - Publisher name normalization
      - Publication date parsing and normalization
      - Call number parsing using Library of Congress and Dewey Decimal systems
      - Subject parsing for faceted browsing

    - **Interactive Browsing**: Filter and search through your collection
    - **Visualizations**: Charts showing usage, age, subjects, and more
    - **Reports**: Generate custom reports for analysis
    - **Export**: Download cleaned data in CSV or Excel format

    #### Key Identifiers

    The application recognizes these key identifiers for matching:
    - MMS ID
    - Barcode
    - Permanent Call Number
    - ISBN
    - ISSN
    - OCLC Control Number

    #### Technology

    Built with Python and Streamlit, using:
    - **pandas** for data processing
    - **SQLAlchemy** for data storage (though currently loading directly from Google Sheet)
    - **Plotly** for interactive visualizations
    - **pycallnumber** for call number parsing

    #### Color Scheme

    The interface uses a vibrant palette with rose (#B4436C), teal (#4D9078),
    orange (#F78154), and gold (#F2C14E) as the primary colors, with sufficient
    contrast for readability.
    """)


def main():
    """Main application entry point."""
    initialize_session_state()
    init_db()  # Initialize database (though not used for data loading in this version)
    render_header()

    if not st.session_state.data_loaded:
        with st.spinner("Loading data from Google Sheet..."):
            df = load_data_from_google_sheet()
        if not df.empty:
            st.session_state.data_loaded = True
            st.session_state.data_df = df
            st.rerun()
        else:
            st.error("Failed to load data from the public Google Sheet.")
            if st.button("Retry Loading Data"):
                st.rerun()
    else:
        # Show main dashboard
        df = st.session_state.data_df
        render_main_dashboard(df)


if __name__ == "__main__":
    main()