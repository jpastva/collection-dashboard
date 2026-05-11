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

from models.database import init_db, get_session_direct
from utils.data_import import import_file, get_records_as_dataframe, apply_filters
from components.visualizations import (
    create_usage_chart,
    create_age_distribution_chart,
    create_subject_coverage_chart,
    create_lc_class_coverage_chart,
    create_oclc_holdings_chart,
    create_material_type_chart,
    create_publication_timeline_chart,
    create_summary_cards,
)
from components.data_table import render_data_table, render_detail_view, render_summary_cards
from components.facet_panel import render_facet_panel, apply_filters_to_dataframe
from components.export import export_to_csv, export_to_excel, create_summary_report, export_report_to_excel
from components.reports import render_report_menu, generate_report, render_report_display

# Page configuration
st.set_page_config(
    page_title="Library Dashboard",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS for Green Glass-inspired theme
st.markdown("""
<style>
    /* Main theme colors - Rose, Teal, Orange, Gold palette */
    :root {
        --primary-rose: #B4436C;
        --secondary-teal: #4D9078;
        --accent-orange: #F78154;
        --accent-gold: #F2C14E;
        --highlight: #FEF9E7;
        --text-dark: #1F2937;
        --text-light: #4B5563;
    }

    /* Header styling */
    .stApp > header {
        background-color: var(--primary-rose);
    }

    /* Sidebar styling */
    section[data-testid="stSidebar"] {
        background-color: var(--highlight);
    }

    /* Metric cards */
    div[data-testid="stMetricValue"] {
        color: var(--primary-rose);
    }

    /* Button styling */
    .stButton > button {
        background-color: var(--secondary-teal);
        color: white;
        border: none;
        border-radius: 4px;
    }
    .stButton > button:hover {
        background-color: var(--primary-rose);
    }

    /* Tabs styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    .stTabs [data-baseweb="tab"] {
        background-color: var(--accent-gold);
        color: var(--text-dark);
        font-weight: 600;
        border-radius: 4px;
    }
    .stTabs [aria-selected="true"] {
        background-color: var(--primary-rose);
        color: white;
    }

    /* Hide default footer */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)


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


def render_data_upload():
    """Render the data upload section."""
    st.markdown("### Import Data")

    uploaded_file = st.file_uploader(
        "Upload a CSV or Excel file containing bibliographic records",
        type=['csv', 'xlsx', 'xlsm', 'xls'],
        help="Files should contain columns like: Library Name, Location Name, Title, Author, Publisher, Publication Date, ISBN, ISSN, OCLC Control Number, etc."
    )

    if uploaded_file is not None:
        # Save to temporary location
        temp_path = os.path.join("data", "temp_import" + os.path.splitext(uploaded_file.name)[1])
        os.makedirs("data", exist_ok=True)

        with open(temp_path, "wb") as f:
            f.write(uploaded_file.getbuffer())

        # Process the file
        with st.spinner("Processing data..."):
            session = get_session_direct()
            try:
                result = import_file(temp_path, session)
                session.close()

                if result['success']:
                    st.session_state.data_loaded = True
                    st.session_state.import_stats = result
                    st.success(f"Successfully imported {result['records_imported']} records!")

                    # Load data into session state
                    st.session_state.data_df = get_records_as_dataframe(get_session_direct())

                    # Clean up temp file
                    if os.path.exists(temp_path):
                        os.remove(temp_path)

                    st.rerun()
                else:
                    st.error(f"Import failed: {result.get('error', 'Unknown error')}")
            except Exception as e:
                st.error(f"Import error: {str(e)}")
            finally:
                session.close()


def render_main_dashboard(df: pd.DataFrame):
    """Render the main dashboard view."""

    # Dashboard Type Selection
    st.markdown("### Dashboard View")
    dashboard_type = st.radio(
        "Select Resource Group",
        options=["All Resources", "Serials", "Monographs"],
        horizontal=True,
        index=0
    )

    # Filter data based on dashboard type
    if dashboard_type == "Serials":
        # Serials: Item Policy is JOURNAL or SERIAL
        filtered_df = df[df['item_policy'].isin(['JOURNAL', 'SERIAL'])].copy()
    elif dashboard_type == "Monographs":
        # Monographs: Everything else
        filtered_df = df[~df['item_policy'].isin(['JOURNAL', 'SERIAL'])].copy()
    else:
        filtered_df = df.copy()

    # Summary cards
    render_summary_cards(filtered_df)

    st.divider()

    # Main tabs
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📊 Data View",
        "📈 Visualizations",
        "📋 Reports",
        "📥 Export",
        "ℹ️ About"
    ])

    with tab1:
        render_data_view_tab(filtered_df)

    with tab2:
        render_visualizations_tab(filtered_df)

    with tab3:
        render_reports_tab(filtered_df)

    with tab4:
        render_export_tab(filtered_df)

    with tab5:
        render_about_tab()


def render_data_view_tab(df: pd.DataFrame):
    """Render the data view tab."""
    st.markdown("### Browse Collection")

    # Apply facet filters
    filters = render_facet_panel(df)
    filtered_df = apply_filters_to_dataframe(df, filters)

    # Show filter results count
    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown(f"Showing **{len(filtered_df):,}** of **{len(df):,}** items")
    with col2:
        if filters:
            st.info(f"{len(filters)} filters active")

    st.divider()

    # Data table with selection
    selected_idx = render_data_table(filtered_df)

    # Show detail view if a record is selected
    if selected_idx is not None and selected_idx < len(filtered_df):
        record = filtered_df.iloc[selected_idx].to_dict()
        st.divider()
        render_detail_view(record)


def render_visualizations_tab(df: pd.DataFrame):
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
            "Material Type Distribution",
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
        fig = create_usage_chart(df)
        st.plotly_chart(fig, width='stretch')

    elif chart_type == "Material Age Distribution":
        fig = create_age_distribution_chart(df)
        st.plotly_chart(fig, width='stretch')

    elif chart_type == "Subject Coverage":
        fig = create_subject_coverage_chart(df)
        st.plotly_chart(fig, width='stretch')

    elif chart_type == "LC Classification Coverage":
        fig = create_lc_class_coverage_chart(df)
        st.plotly_chart(fig, width='stretch')

    elif chart_type == "Material Type Distribution":
        fig = create_material_type_chart(df)
        st.plotly_chart(fig, width='stretch')

    elif chart_type == "Publication Timeline":
        fig = create_publication_timeline_chart(df)
        st.plotly_chart(fig, width='stretch')

    elif chart_type == "OCLC Holdings":
        fig = create_oclc_holdings_chart(df)
        st.plotly_chart(fig, width='stretch')

    elif chart_type == "Request Usage":
        from components.visualizations import create_requests_chart
        fig = create_requests_chart(df)
        st.plotly_chart(fig, width='stretch')

    elif chart_type == "PALCI Holdings":
        from components.visualizations import create_palci_holdings_chart
        fig = create_palci_holdings_chart(df)
        st.plotly_chart(fig, width='stretch')

    elif chart_type == "Last Loan Date":
        from components.visualizations import create_last_loan_date_chart
        fig = create_last_loan_date_chart(df)
        st.plotly_chart(fig, width='stretch')

    elif chart_type == "LC Subclass Coverage":
        from components.visualizations import create_lc_subclass_chart
        fig = create_lc_subclass_chart(df)
        st.plotly_chart(fig, width='stretch')

    elif chart_type == "E-Copy Availability":
        from components.visualizations import create_ecopy_chart
        fig = create_ecopy_chart(df)
        st.plotly_chart(fig, width='stretch')

    # Show all charts option
    st.divider()
    if st.checkbox("Show All Visualizations"):
        st.markdown("#### Circulation Usage")
        st.plotly_chart(create_usage_chart(df), width='stretch', key='viz_usage_all')

        st.markdown("#### Material Age Distribution")
        st.plotly_chart(create_age_distribution_chart(df), width='stretch', key='viz_age_all')

        st.markdown("#### Subject Coverage")
        st.plotly_chart(create_subject_coverage_chart(df), width='stretch', key='viz_subject_all')

        st.markdown("#### LC Classification Coverage")
        st.plotly_chart(create_lc_class_coverage_chart(df), width='stretch', key='viz_lc_all')

        st.markdown("#### Material Type Distribution")
        st.plotly_chart(create_material_type_chart(df), width='stretch', key='viz_material_all')

        st.markdown("#### Publication Timeline")
        st.plotly_chart(create_publication_timeline_chart(df), width='stretch', key='viz_timeline_all')


def render_reports_tab(df: pd.DataFrame):
    """Render the reports tab."""
    st.markdown("### Generate Reports")

    # Report generator
    report = render_report_menu(df)

    if report:
        st.divider()
        render_report_display(report)


def render_export_tab(df: pd.DataFrame):
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
            'title', 'author', 'publisher', 'publication_date',
            'material_type', 'permanent_call_number', 'call_number_class',
            'num_loans', 'isbn_normalized', 'issn_normalized', 'oclc_control_number',
            'mms_id', 'barcode', 'subjects', 'has_committed_to_retain',
            'open_access', 'library_name', 'location_name',
        ]
        available = [col for col in available_columns if col in df.columns]

        selected_columns = st.multiselect(
            "Select columns to export",
            options=available,
            default=available
        )

    with col2:
        st.markdown("#### Export Summary")
        st.metric("Records to export", len(df))
        if selected_columns:
            st.metric("Columns", len(selected_columns))

    st.divider()

    # Generate export
    if st.button("Download Export", type="primary", width='stretch'):
        if selected_columns:
            export_df = df[selected_columns]
        else:
            export_df = df

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
        report_data = create_summary_report(df)
        excel_data = export_report_to_excel(df, report_data)
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

    - **Data Import**: Upload CSV or Excel files containing bibliographic records
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
    - **SQLAlchemy** for data storage
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
    render_header()

    # Initialize database
    init_db()

    if not st.session_state.data_loaded:
        # Show upload screen
        render_data_upload()

        # Show sample data info
        st.divider()
        st.markdown("### Getting Started")
        st.markdown("""
        To begin using Library Dashboard:

        1. **Prepare your data**: Ensure your CSV or Excel file contains bibliographic records
           with columns such as Title, Author, Publisher, Publication Date, ISBN, etc.

        2. **Upload your file**: Use the file uploader above to import your data.

        3. **Explore your collection**: Once imported, you can:
           - Browse items in the Data View tab
           - Filter by material type, LC class, subject, and more
           - View visualizations of your collection
           - Generate custom reports
           - Export cleaned data

        The application will automatically clean and normalize your data during import,
        including OCLC numbers, ISBNs, call numbers, and more.
        """)
    else:
        # Show main dashboard
        df = st.session_state.data_df

        # Data management in sidebar
        with st.sidebar:
            st.markdown("### Data Management")

            st.metric("Total Records", len(df))

            if st.button("Clear Data & Start Over", width='stretch'):
                st.session_state.data_loaded = False
                st.session_state.data_df = pd.DataFrame()
                st.session_state.import_stats = {}
                st.session_state.active_filters = {}
                st.rerun()

            if st.button("Refresh Data", width='stretch'):
                st.session_state.data_df = get_records_as_dataframe(get_session_direct())
                st.rerun()

            st.divider()

            # Show import stats
            if st.session_state.import_stats:
                stats = st.session_state.import_stats
                st.markdown("#### Import Statistics")
                st.info(f"Rows imported: {stats.get('records_imported', 0)}")

                if stats.get('processing_stats', {}).get('errors'):
                    with st.expander("View Import Errors"):
                        for error in stats['processing_stats']['errors'][:10]:
                            st.warning(error)

        render_main_dashboard(df)


if __name__ == "__main__":
    main()
