"""
Facet panel component for filtering bibliographic records.
"""

import streamlit as st
import pandas as pd
from typing import Dict, Any, List, Optional
from utils.data_import import get_subjects_facet, get_facet_values
from utils.cleaners import parse_subjects


def render_facet_panel(
    df: pd.DataFrame,
    session: Optional[Any] = None
) -> Dict[str, Any]:
    """
    Render the facet filtering side panel.

    Args:
        df: DataFrame with bibliographic records
        session: Optional SQLAlchemy session for database-backed facets

    Returns:
        Dictionary of active filters
    """
    filters = {}

    with st.sidebar:
        st.markdown("### Filters")

        # Clear filters button
        if st.button("Clear All Filters", width='stretch'):
            st.session_state['active_filters'] = {}
            st.rerun()

        st.divider()

        # Item Policy filter
        st.markdown("#### Item Policy")
        if 'item_policy' in df.columns:
            item_policies = df['item_policy'].dropna().unique()
            item_policies = [p for p in item_policies if p and str(p).strip()]
            item_policy_filter = st.multiselect(
                "Select item policies",
                options=sorted(item_policies),
                default=st.session_state.get('filter_item_policy', []),
                key="item_policy_filter"
            )
            if item_policy_filter:
                filters['item_policy'] = item_policy_filter
                st.session_state['filter_item_policy'] = item_policy_filter

        st.divider()

        # Material Type filter
        st.markdown("#### Material Type")
        material_types = df['material_type'].dropna().unique()
        material_types = [m for m in material_types if m and str(m).strip()]
        material_type_filter = st.multiselect(
            "Select material types",
            options=sorted(material_types),
            default=st.session_state.get('filter_material_type', []),
            key="material_type_filter"
        )
        if material_type_filter:
            filters['material_type'] = material_type_filter
            st.session_state['filter_material_type'] = material_type_filter

        st.divider()

        # LC Class filter
        st.markdown("#### LC Classification")
        if 'call_number_class' in df.columns:
            lc_classes = df[df['call_number_classification'] == 'LC']['call_number_class'].dropna().unique()
            lc_classes = [c for c in lc_classes if c and str(c).strip()]

            # Add descriptions
            from utils.call_number_parser import get_lc_class_description
            lc_options = {f"{c} - {get_lc_class_description(c)}": c for c in sorted(lc_classes)}

            lc_display = st.multiselect(
                "Select LC classes",
                options=list(lc_options.keys()),
                format_func=lambda x: x,
                default=[k for k, v in lc_options.items() if v in st.session_state.get('filter_lc_class', [])],
                key="lc_class_filter"
            )
            lc_filter = [lc_options[d] for d in lc_display] if lc_display else []
            if lc_filter:
                filters['call_number_class'] = lc_filter
                st.session_state['filter_lc_class'] = lc_filter

        st.divider()

        # Publication decade filter
        st.markdown("#### Publication Period")
        if 'publication_year_start' in df.columns:
            valid_years = df[df['publication_year_start'].notna()]['publication_year_start']
            if len(valid_years) > 0:
                min_year = int(valid_years.min())
                max_year = int(valid_years.max())

                # Create decade options
                decades = list(range((min_year // 10) * 10, ((max_year // 10) + 1) * 10, 10))
                decade_options = {f"{d}s": d for d in decades}

                selected_decades = st.multiselect(
                    "Select decades",
                    options=list(decade_options.keys()),
                    default=[k for k, v in decade_options.items() if v // 10 in st.session_state.get('filter_decade', [])],
                    key="decade_filter"
                )

                if selected_decades:
                    selected_years = [decade_options[d] for d in selected_decades]
                    # Convert to year range filter
                    year_min = min(selected_years)
                    year_max = max(selected_years) + 9
                    filters['publication_year_start'] = (year_min, year_max)
                    st.session_state['filter_decade'] = [y // 10 for y in selected_years]

        st.divider()

        # Usage filter
        st.markdown("#### Usage Level")
        usage_options = {
            'No circulation': (0, 0),
            'Low (1-10)': (1, 10),
            'Medium (11-50)': (11, 50),
            'High (51-100)': (51, 100),
            'Very High (100+)': (101, float('inf')),
        }

        selected_usage = st.multiselect(
            "Select usage levels",
            options=list(usage_options.keys()),
            default=[k for k, v in usage_options.items() if v in st.session_state.get('filter_usage', [])],
            key="usage_filter"
        )

        if selected_usage:
            # This is a bit complex - we'll handle it in the filter application
            st.session_state['filter_usage'] = selected_usage
            filters['_usage_ranges'] = [usage_options[u] for u in selected_usage]

        st.divider()

        # Subject filter
        st.markdown("#### Subjects")
        if 'subjects' in df.columns:
            # Parse all subjects
            all_subjects = {}
            for subjects_str in df['subjects'].dropna():
                subjects = parse_subjects(subjects_str)
                for subject in subjects:
                    all_subjects[subject] = all_subjects.get(subject, 0) + 1

            # Sort by count
            sorted_subjects = sorted(all_subjects.items(), key=lambda x: -x[1])

            # Show top subjects with search
            subject_search = st.text_input("Search subjects", key="subject_search")

            if subject_search:
                filtered_subjects = [s for s, _ in sorted_subjects if subject_search.lower() in s.lower()][:50]
            else:
                filtered_subjects = [s for s, _ in sorted_subjects[:50]]

            subject_filter = st.multiselect(
                "Select subjects",
                options=sorted(filtered_subjects),
                default=st.session_state.get('filter_subjects', []),
                key="subject_filter"
            )

            if subject_filter:
                filters['subjects'] = subject_filter
                st.session_state['filter_subjects'] = subject_filter

        st.divider()

        # Retention status filter
        st.markdown("#### Retention Status")
        retain_filter = st.radio(
            "Committed to Retain",
            options=["All", "Yes", "No"],
            index=0,
            key="retain_filter"
        )

        if retain_filter != "All":
            filters['has_committed_to_retain'] = (retain_filter == "Yes")
            st.session_state['filter_retain'] = retain_filter

        st.divider()

        # Open Access filter
        st.markdown("#### Access Status")
        access_filter = st.radio(
            "Open Access",
            options=["All", "Yes", "No"],
            index=0,
            key="access_filter"
        )

        if access_filter != "All":
            filters['open_access'] = (access_filter == "Yes")
            st.session_state['filter_access'] = access_filter

    return filters


def apply_filters_to_dataframe(
    df: pd.DataFrame,
    filters: Dict[str, Any]
) -> pd.DataFrame:
    """
    Apply filters to a pandas DataFrame.

    Args:
        df: DataFrame to filter
        filters: Dictionary of filters

    Returns:
        Filtered DataFrame
    """
    if not filters:
        return df

    result_df = df.copy()

    for column, value in filters.items():
        if column.startswith('_'):
            # Special filter
            if column == '_usage_ranges':
                # Usage range filter
                mask = pd.Series([False] * len(result_df))
                for min_val, max_val in value:
                    if max_val == float('inf'):
                        mask |= (result_df['num_loans'] >= min_val)
                    else:
                        mask |= (result_df['num_loans'] >= min_val) & (result_df['num_loans'] <= max_val)
                result_df = result_df[mask]
            continue

        if column == 'subjects':
            # Subject filter - parse and check each record
            def has_matching_subject(subjects_str):
                if pd.isna(subjects_str):
                    return False
                subjects = parse_subjects(subjects_str)
                return any(s in value for s in subjects)

            mask = result_df['subjects'].apply(has_matching_subject)
            result_df = result_df[mask]

        elif isinstance(value, tuple):
            # Range filter
            min_val, max_val = value
            mask = result_df[column] >= min_val
            if max_val != float('inf'):
                mask &= result_df[column] <= max_val
            result_df = result_df[mask]

        elif isinstance(value, list):
            # Multi-select filter
            result_df = result_df[result_df[column].isin(value)]

        elif isinstance(value, bool):
            # Boolean filter
            result_df = result_df[result_df[column] == value]

        else:
            # Exact match filter
            result_df = result_df[result_df[column] == value]

    return result_df


def get_facet_counts(df: pd.DataFrame) -> Dict[str, Dict[str, int]]:
    """
    Get facet counts for various columns.

    Args:
        df: DataFrame with bibliographic records

    Returns:
        Dictionary of column -> {value -> count}
    """
    facets = {}

    # Material type counts
    if 'material_type' in df.columns:
        facets['material_type'] = df['material_type'].value_counts().to_dict()

    # LC class counts
    if 'call_number_class' in df.columns:
        lc_df = df[df['call_number_classification'] == 'LC']
        facets['call_number_class'] = lc_df['call_number_class'].value_counts().to_dict()

    # Publication decade counts
    if 'publication_year_start' in df.columns:
        valid_df = df[df['publication_year_start'].notna()].copy()
        valid_df['decade'] = (valid_df['publication_year_start'] // 10) * 10
        facets['decade'] = valid_df['decade'].value_counts().to_dict()

    return facets
