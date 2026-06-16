"""
Report generation module for creating custom reports from bibliographic data.
"""

import streamlit as st
import pandas as pd
from typing import Dict, Any, List, Optional
from datetime import datetime


def render_report_menu(df: pd.DataFrame) -> Optional[Dict[str, Any]]:
    """
    Render the report generation menu.

    Args:
        df: DataFrame with bibliographic records

    Returns:
        Generated report data or None
    """
    st.markdown("### Report Generator")

    # Initialize session state for report type if not exists
    if 'report_type' not in st.session_state:
        st.session_state.report_type = "Collection Summary Report"

    # Report type selection
    report_type = st.selectbox(
        "Select Report Type",
        options=[
            "Collection Summary Report",
            "Usage Analysis Report",
            "Subject Coverage Report",
            "Retention Status Report",
            "Publication Age Report",
            "Custom Report",
        ],
        index=["Collection Summary Report", "Usage Analysis Report", "Subject Coverage Report",
               "Retention Status Report", "Publication Age Report", "Custom Report"].index(st.session_state.report_type)
    )

    # Update session state when report type changes
    if report_type != st.session_state.report_type:
        st.session_state.report_type = report_type

    # Report options
    st.markdown("#### Report Options")

    # Date range filter for reports
    col1, col2 = st.columns(2)
    with col1:
        if 'publication_year_start' in df.columns:
            valid_years = df[df['publication_year_start'].notna()]['publication_year_start']
            if len(valid_years) > 0:
                min_year = int(valid_years.min())
                max_year = int(valid_years.max())
                year_range = st.slider(
                    "Publication Year Range",
                    min_value=min_year,
                    max_value=max_year,
                    value=(min_year, max_year)
                )
            else:
                year_range = None
        else:
            year_range = None

    with col2:
        material_filter = st.multiselect(
            "Material Types",
            options=sorted(df['material_type'].dropna().unique()) if 'material_type' in df.columns else [],
            default=[]
        )

    # Generate report button
    if st.button("Generate Report", type="primary", width='stretch', key="generate_report_button"):
        report_data = generate_report(
            df=df,
            report_type=st.session_state.report_type,
            year_range=year_range,
            material_filter=material_filter
        )
        return report_data

    return None


def generate_report(
    df: pd.DataFrame,
    report_type: str,
    year_range: Optional[tuple] = None,
    material_filter: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Generate a report based on selected options.

    Args:
        df: DataFrame with bibliographic records
        report_type: Type of report to generate
        year_range: Optional tuple of (min_year, max_year)
        material_filter: Optional list of material types to include

    Returns:
        Dictionary containing report data and metadata
    """
    # Apply filters
    filtered_df = df.copy()

    if year_range and 'publication_year_start' in filtered_df.columns:
        filtered_df = filtered_df[
            (filtered_df['publication_year_start'] >= year_range[0]) &
            (filtered_df['publication_year_start'] <= year_range[1])
        ]

    if material_filter and 'material_type' in filtered_df.columns:
        filtered_df = filtered_df[filtered_df['material_type'].isin(material_filter)]

    # Generate report based on type
    if report_type == "Collection Summary Report":
        return generate_collection_summary(filtered_df)
    elif report_type == "Usage Analysis Report":
        return generate_usage_report(filtered_df)
    elif report_type == "Subject Coverage Report":
        return generate_subject_report(filtered_df)
    elif report_type == "Retention Status Report":
        return generate_retention_report(filtered_df)
    elif report_type == "Publication Age Report":
        return generate_age_report(filtered_df)
    elif report_type == "Custom Report":
        return generate_custom_report(filtered_df)

    return {}


def generate_collection_summary(df: pd.DataFrame) -> Dict[str, Any]:
    """Generate a collection summary report."""

    report = {
        'title': 'Collection Summary Report',
        'generated_at': datetime.now().isoformat(),
        'filters_applied': [],
        'sections': [],
    }

    # Overview section
    overview = {
        'name': 'Collection Overview',
        'metrics': [
            {'label': 'Total Items', 'value': len(df)},
            {'label': 'Unique Titles', 'value': df['title'].nunique() if 'title' in df.columns else 0},
            {'label': 'Unique Authors', 'value': df['author'].nunique() if 'author' in df.columns and df['author'].notna().any() else 0},
            {'label': 'Unique Publishers', 'value': df['publisher'].nunique() if 'publisher' in df.columns and df['publisher'].notna().any() else 0},
        ]
    }
    report['sections'].append(overview)

    # Material types
    if 'material_type' in df.columns:
        material_section = {
            'name': 'Items by Material Type',
            'type': 'table',
            'data': df['material_type'].value_counts().reset_index()
        }
        material_section['data'].columns = ['Material Type', 'Count']
        report['sections'].append(material_section)

    # LC Classes
    if 'call_number_classification' in df.columns:
        lc_df = df[df['call_number_classification'] == 'LC']
        if len(lc_df) > 0:
            lc_section = {
                'name': 'Items by LC Class',
                'type': 'table',
                'data': lc_df['call_number_class'].value_counts().reset_index()
            }
            lc_section['data'].columns = ['LC Class', 'Count']
            report['sections'].append(lc_section)

    # Publication years
    if 'publication_year_start' in df.columns:
        valid_df = df[df['publication_year_start'].notna()]
        if len(valid_df) > 0:
            year_section = {
                'name': 'Items by Publication Decade',
                'type': 'table',
                'data': valid_df.copy()
            }
            year_section['data']['decade'] = (year_section['data']['publication_year_start'] // 10) * 10
            year_data = year_section['data'].groupby('decade').size().reset_index()
            year_data.columns = ['Decade', 'Count']
            report['sections'].append({
                'name': 'Items by Publication Decade',
                'type': 'table',
                'data': year_data
            })

    return report


def generate_usage_report(df: pd.DataFrame) -> Dict[str, Any]:
    """Generate a usage analysis report."""

    report = {
        'title': 'Usage Analysis Report',
        'generated_at': datetime.now().isoformat(),
        'sections': [],
    }

    if 'num_loans' not in df.columns:
        report['error'] = 'No usage data available'
        return report

    # Usage overview
    total_loans = int(df['num_loans'].sum())
    items_with_loans = len(df[df['num_loans'] > 0])
    avg_loans = df['num_loans'].mean()
    max_loans = int(df['num_loans'].max())

    overview = {
        'name': 'Usage Overview',
        'metrics': [
            {'label': 'Total Circulation', 'value': f"{total_loans:,}"},
            {'label': 'Items with Circulation', 'value': f"{items_with_loans:,}"},
            {'label': 'Average Loans per Item', 'value': f"{avg_loans:.2f}"},
            {'label': 'Maximum Loans', 'value': f"{max_loans:,}"},
        ]
    }
    report['sections'].append(overview)

    # Usage by material type
    if 'material_type' in df.columns:
        usage_by_material = df.groupby('material_type')['num_loans'].agg(['sum', 'mean', 'count']).reset_index()
        usage_by_material.columns = ['Material Type', 'Total Loans', 'Avg Loans', 'Item Count']
        report['sections'].append({
            'name': 'Usage by Material Type',
            'type': 'table',
            'data': usage_by_material.sort_values('Total Loans', ascending=False)
        })

    # Most circulated items
    top_items = df.nlargest(20, 'num_loans')[['title', 'author', 'num_loans', 'permanent_call_number']]
    report['sections'].append({
        'name': 'Top 20 Most Circulated Items',
        'type': 'table',
        'data': top_items
    })

    # Usage distribution
    bins = [0, 1, 5, 10, 25, 50, 100, float('inf')]
    labels = ['1', '2-5', '6-10', '11-25', '26-50', '51-100', '100+']
    df_copy = df.copy()
    df_copy['loan_range'] = pd.cut(df_copy['num_loans'], bins=bins, labels=labels, right=True)
    usage_dist = df_copy.groupby('loan_range', observed=True).size().reset_index()
    usage_dist.columns = ['Loan Range', 'Item Count']

    report['sections'].append({
        'name': 'Usage Distribution',
        'type': 'table',
        'data': usage_dist
    })

    return report


def generate_subject_report(df: pd.DataFrame) -> Dict[str, Any]:
    """Generate a subject coverage report."""

    from utils.cleaners import parse_subjects

    report = {
        'title': 'Subject Coverage Report',
        'generated_at': datetime.now().isoformat(),
        'sections': [],
    }

    if 'subjects' not in df.columns:
        report['error'] = 'No subject data available'
        return report

    # Parse all subjects
    all_subjects = {}
    for subjects_str in df['subjects'].dropna():
        subjects = parse_subjects(subjects_str)
        for subject in subjects:
            all_subjects[subject] = all_subjects.get(subject, 0) + 1

    # Overview
    overview = {
        'name': 'Subject Overview',
        'metrics': [
            {'label': 'Total Unique Subjects', 'value': len(all_subjects)},
            {'label': 'Items with Subjects', 'value': df['subjects'].notna().sum()},
        ]
    }
    report['sections'].append(overview)

    # Top subjects
    sorted_subjects = sorted(all_subjects.items(), key=lambda x: -x[1])
    top_subjects_df = pd.DataFrame(sorted_subjects[:50], columns=['Subject', 'Count'])

    report['sections'].append({
        'name': 'Top 50 Subjects',
        'type': 'table',
        'data': top_subjects_df
    })

    # Subjects by LC class (if available)
    if 'call_number_class' in df.columns:
        lc_subjects = df[df['call_number_classification'] == 'LC'].copy()
        if len(lc_subjects) > 0:
            # Parse subjects for LC items
            lc_subject_counts = {}
            for _, row in lc_subjects.iterrows():
                if row['subjects']:
                    subjects = parse_subjects(row['subjects'])
                    lc_class = row['call_number_class']
                    for subject in subjects:
                        key = f"{lc_class} - {subject}"
                        lc_subject_counts[key] = lc_subject_counts.get(key, 0) + 1

            lc_subject_df = pd.DataFrame(
                sorted(lc_subject_counts.items(), key=lambda x: -x[1])[:30],
                columns=['LC Class - Subject', 'Count']
            )

            report['sections'].append({
                'name': 'Top Subject-LC Class Combinations',
                'type': 'table',
                'data': lc_subject_df
            })

    return report


def generate_retention_report(df: pd.DataFrame) -> Dict[str, Any]:
    """Generate a retention status report."""

    report = {
        'title': 'Retention Status Report',
        'generated_at': datetime.now().isoformat(),
        'sections': [],
    }

    if 'has_committed_to_retain' not in df.columns:
        report['error'] = 'No retention data available'
        return report

    # Retention overview
    committed = df[df['has_committed_to_retain'] == True]
    not_committed = df[df['has_committed_to_retain'] != True]

    overview = {
        'name': 'Retention Overview',
        'metrics': [
            {'label': 'Total Items', 'value': len(df)},
            {'label': 'Committed to Retain', 'value': len(committed)},
            {'label': 'Not Committed', 'value': len(not_committed)},
            {'label': 'Retention Rate', 'value': f"{len(committed)/len(df)*100:.1f}%"},
        ]
    }
    report['sections'].append(overview)

    # Committed items by material type
    if 'material_type' in df.columns:
        committed_by_material = committed.groupby('material_type').size().reset_index()
        committed_by_material.columns = ['Material Type', 'Count']

        report['sections'].append({
            'name': 'Committed Items by Material Type',
            'type': 'table',
            'data': committed_by_material.sort_values('Count', ascending=False)
        })

    # Committed items by LC class
    if 'call_number_class' in df.columns:
        committed_lc = committed[committed['call_number_classification'] == 'LC']
        if len(committed_lc) > 0:
            committed_by_lc = committed_lc.groupby('call_number_class').size().reset_index()
            committed_by_lc.columns = ['LC Class', 'Count']

            report['sections'].append({
                'name': 'Committed Items by LC Class',
                'type': 'table',
                'data': committed_by_lc.sort_values('Count', ascending=False)
            })

    # List of committed items
    if len(committed) > 0:
        committed_list = committed[['title', 'author', 'permanent_call_number', 'material_type']].head(100)
        report['sections'].append({
            'name': 'Committed Items (Sample)',
            'type': 'table',
            'data': committed_list
        })

    return report


def generate_age_report(df: pd.DataFrame) -> Dict[str, Any]:
    """Generate a publication age report."""

    from datetime import datetime
    current_year = datetime.now().year

    report = {
        'title': 'Publication Age Report',
        'generated_at': datetime.now().isoformat(),
        'sections': [],
    }

    if 'publication_year_start' not in df.columns:
        report['error'] = 'No publication date data available'
        return report

    valid_df = df[df['publication_year_start'].notna()].copy()

    if len(valid_df) == 0:
        report['error'] = 'No valid publication dates found'
        return report

    # Calculate ages
    valid_df['age'] = current_year - valid_df['publication_year_start']
    valid_df['decade'] = (valid_df['publication_year_start'] // 10) * 10

    # Age overview
    overview = {
        'name': 'Age Overview',
        'metrics': [
            {'label': 'Items with Publication Dates', 'value': len(valid_df)},
            {'label': 'Oldest Item', 'value': int(valid_df['publication_year_start'].min())},
            {'label': 'Newest Item', 'value': int(valid_df['publication_year_start'].max())},
            {'label': 'Average Age', 'value': f"{valid_df['age'].mean():.1f} years"},
            {'label': 'Median Age', 'value': f"{int(valid_df['age'].median())} years"},
        ]
    }
    report['sections'].append(overview)

    # Age distribution
    age_bins = [0, 10, 25, 50, 75, 100, float('inf')]
    age_labels = ['0-10 years', '11-25 years', '26-50 years', '51-75 years', '76-100 years', '100+ years']
    valid_df['age_category'] = pd.cut(valid_df['age'], bins=age_bins, labels=age_labels, right=True)

    age_dist = valid_df.groupby('age_category', observed=True).size().reset_index()
    age_dist.columns = ['Age Range', 'Item Count']

    report['sections'].append({
        'name': 'Age Distribution',
        'type': 'table',
        'data': age_dist
    })

    # By decade
    decade_dist = valid_df.groupby('decade').size().reset_index()
    decade_dist.columns = ['Decade', 'Item Count']

    report['sections'].append({
        'name': 'Items by Publication Decade',
        'type': 'table',
        'data': decade_dist.sort_values('Decade', ascending=False)
    })

    return report


def generate_custom_report(df: pd.DataFrame) -> Dict[str, Any]:
    """Generate a custom report with user-selected fields."""

    # Initialize session state for custom report if not exists
    if 'custom_report_columns' not in st.session_state:
        st.session_state.custom_report_columns = []
    if 'custom_report_sort_column' not in st.session_state:
        st.session_state.custom_report_sort_column = ''
    if 'custom_report_sort_ascending' not in st.session_state:
        st.session_state.custom_report_sort_ascending = True

    report = {
        'title': 'Custom Report',
        'generated_at': datetime.now().isoformat(),
        'sections': [],
    }

    # Column selection
    available_columns = [
        'title', 'author', 'publisher', 'publication_date',
        'material_type', 'permanent_call_number', 'call_number_class',
        'num_loans', 'isbn_normalized', 'issn_normalized', 'oclc_control_number',
        'mms_id', 'barcode', 'subjects', 'has_committed_to_retain',
        'open_access', 'library_name', 'location_name'
    ]

    # Filter to available columns
    available = [col for col in available_columns if col in df.columns]

    # If no columns previously selected, default to first 5
    if not st.session_state.custom_report_columns and available:
        st.session_state.custom_report_columns = available[:5]

    selected_columns = st.multiselect(
        "Select columns to include",
        options=available,
        default=st.session_state.custom_report_columns,
        key="custom_report_columns_select"
    )

    # Update session state when columns change
    if selected_columns != st.session_state.custom_report_columns:
        st.session_state.custom_report_columns = selected_columns
        # Reset sort column if it's not in the new selection
        if st.session_state.custom_report_sort_column not in selected_columns:
            st.session_state.custom_report_sort_column = ''

    if selected_columns:
        # Sort options
        sort_column_options = [''] + selected_columns
        # Ensure current sort column is in options
        if st.session_state.custom_report_sort_column not in sort_column_options:
            st.session_state.custom_report_sort_column = ''

        sort_column = st.selectbox(
            "Sort by",
            options=sort_column_options,
            index=sort_column_options.index(st.session_state.custom_report_sort_column) if st.session_state.custom_report_sort_column in sort_column_options else 0,
            key="custom_report_sort_select"
        )

        # Update session state when sort column changes
        if sort_column != st.session_state.custom_report_sort_column:
            st.session_state.custom_report_sort_column = sort_column

        sort_ascending = st.radio(
            "Sort order",
            options=['Ascending', 'Descending'],
            index=0 if st.session_state.custom_report_sort_ascending else 1,
            key="custom_report_sort_order_radio"
        )

        # Update session state when sort order changes
        if sort_ascending == 'Ascending':
            st.session_state.custom_report_sort_ascending = True
        else:
            st.session_state.custom_report_sort_ascending = False

        if st.button("Generate Custom Report", key="generate_custom_report_button"):
            custom_df = df[selected_columns].copy()

            if sort_column and sort_column in custom_df.columns:
                custom_df = custom_df.sort_values(
                    sort_column,
                    ascending=st.session_state.custom_report_sort_ascending
                )

            report['sections'].append({
                'name': 'Custom Data',
                'type': 'table',
                'data': custom_df
            })

            report['selected_columns'] = selected_columns
        else:
            # Show a message prompting the user to click the button
            report['sections'].append({
                'name': 'Custom Data',
                'type': 'info',
                'data': {'message': 'Please select columns and click the "Generate Custom Report" button to generate the report.'}
            })
    else:
        # Show message when no columns selected
        report['sections'].append({
            'name': 'Custom Data',
            'type': 'info',
            'data': {'message': 'Please select at least one column to include in the report.'}
        })

    return report


def render_report_display(report: Dict[str, Any]) -> None:
    """
    Render a generated report for display.

    Args:
        report: Report data dictionary
    """
    if not report:
        st.info("No report generated.")
        return

    st.markdown(f"## {report.get('title', 'Report')}")
    st.markdown(f"*Generated: {report.get('generated_at', 'Unknown')}*")

    if 'error' in report:
        st.error(report['error'])
        return

    for section in report.get('sections', []):
        st.markdown(f"### {section['name']}")

        if 'metrics' in section:
            # Display metrics
            cols = st.columns(min(4, len(section['metrics'])))
            for i, metric in enumerate(section['metrics']):
                with cols[i % len(cols)]:
                    st.metric(metric['label'], metric['value'])

        elif section.get('type') == 'table':
            # Display data table
            data = section.get('data', pd.DataFrame())
            if isinstance(data, pd.DataFrame) and not data.empty:
                st.dataframe(data, width='stretch')
            else:
                st.info("No data for this section.")
        elif section.get('type') == 'info':
            # Display info message
            data = section.get('data', {})
            message = data.get('message', 'No information available.')
            st.info(message)

        st.divider()