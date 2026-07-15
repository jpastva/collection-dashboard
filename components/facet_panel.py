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
    key_suffix: Optional[str] = None,
    session: Optional[Any] = None
) -> Dict[str, Any]:
    """
    Render the facet filtering side panel.

    Args:
        df: DataFrame with bibliographic records
        key_suffix: Optional suffix to append to element keys to avoid duplicates
        session: Optional SQLAlchemy session for database-backed facets

    Returns:
        Dictionary of active filters
    """
    filters = {}

    with st.sidebar:
        st.markdown("### Filters")

        # Clear filters button
        clear_button_key = f"clear_all_filters{key_suffix}" if key_suffix else "clear_all_filters"
        if st.button("Clear All Filters", width='stretch', key=clear_button_key):
            # Reset all filter-related session state keys (shared across tabs)
            keys_to_clear = [
                'filter_item_policy',
                'filter_material_type',
                'filter_lc_class',
                'filter_decade',
                'filter_usage',
                'filter_subjects',
                'filter_decision',
                'filter_access',
                'subject_search',
            ]
            for key in keys_to_clear:
                if key in st.session_state:
                    del st.session_state[key]
            # Also reset the active_filters (though unused)
            st.session_state['active_filters'] = {}
            st.rerun()

        st.divider()

        # Item Policy filter
        st.markdown("#### Item Policy")
        if 'Item Policy' in df.columns:
            item_policies = df['Item Policy'].dropna().unique()
            item_policies = [p for p in item_policies if p and str(p).strip()]
            item_policy_widget_key = f"item_policy_filter{key_suffix}" if key_suffix else "item_policy_filter"
            item_policy_filter = st.multiselect(
                "Select item policies",
                options=sorted(item_policies),
                default=st.session_state.get('filter_item_policy', []),
                key=item_policy_widget_key
            )
            if item_policy_filter:
                filters['Item Policy'] = item_policy_filter
                st.session_state['filter_item_policy'] = item_policy_filter

        st.divider()

        # Material Type filter
        st.markdown("#### Material Type")
        material_types = df['Material Type'].dropna().unique()
        material_types = [m for m in material_types if m and str(m).strip()]
        material_type_widget_key = f"material_type_filter{key_suffix}" if key_suffix else "material_type_filter"
        material_type_filter = st.multiselect(
            "Select material types",
            options=sorted(material_types),
            default=st.session_state.get('filter_material_type', []),
            key=material_type_widget_key
        )
        if material_type_filter:
            filters['Material Type'] = material_type_filter
            st.session_state['filter_material_type'] = material_type_filter

        st.divider()

        # LC Class filter
        st.markdown("#### LC Classification")
        if 'call_number_classification' in df.columns and 'Permanent LC Classification Top Line' in df.columns:
            lc_df = df[df['call_number_classification'] == 'LC']
            if not lc_df.empty:
                lc_classes = lc_df['Permanent LC Classification Top Line'].dropna().unique()
                lc_classes = [c for c in lc_classes if c and str(c).strip()]

                # Add descriptions
                from utils.call_number_parser import get_lc_class_description
                lc_options = {f"{c} - {get_lc_class_description(c)}": c for c in sorted(lc_classes)}

                lc_widget_key = f"lc_class_filter{key_suffix}" if key_suffix else "lc_class_filter"
                lc_display = st.multiselect(
                    "Select LC classes",
                    options=list(lc_options.keys()),
                    format_func=lambda x: x,
                    default=[k for k, v in lc_options.items() if v in st.session_state.get('filter_lc_class', [])],
                    key=lc_widget_key
                )
                lc_filter = [lc_options[d] for d in lc_display] if lc_display else []
                if lc_filter:
                    filters['Permanent LC Classification Top Line'] = lc_filter
                    st.session_state['filter_lc_class'] = lc_filter

        st.divider()

        # Publication decade filter
        st.markdown("#### Publication Period")
        if 'Publication Year Start' in df.columns:
            valid_years = df[df['Publication Year Start'].notna()]['Publication Year Start']
            if len(valid_years) > 0:
                min_year = int(valid_years.min())
                max_year = int(valid_years.max())

                # Create decade options
                decades = list(range((min_year // 10) * 10, ((max_year // 10) + 1) * 10, 10))
                decade_options = {f"{d}s": d for d in decades}

                decade_widget_key = f"decade_filter{key_suffix}" if key_suffix else "decade_filter"
                selected_decades = st.multiselect(
                    "Select decades",
                    options=list(decade_options.keys()),
                    default=[k for k, v in decade_options.items() if v // 10 in st.session_state.get('filter_decade', [])],
                    key=decade_widget_key
                )

                if selected_decades:
                    selected_years = [decade_options[d] for d in selected_decades]
                    # Convert to year range filter
                    year_min = min(selected_years)
                    year_max = max(selected_years) + 9
                    filters['Publication Year Start'] = (year_min, year_max)
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

        usage_widget_key = f"usage_filter{key_suffix}" if key_suffix else "usage_filter"
        selected_usage = st.multiselect(
            "Select usage levels",
            options=list(usage_options.keys()),
            default=[k for k, v in usage_options.items() if v in st.session_state.get('filter_usage', [])],
            key=usage_widget_key
        )

        if selected_usage:
            # This is a bit complex - we'll handle it in the filter application
            st.session_state['filter_usage'] = selected_usage
            filters['_usage_ranges'] = [usage_options[u] for u in selected_usage]

        st.divider()

        # Subject filter
        st.markdown("#### Subjects")
        if 'Subjects' in df.columns:
            # Parse all subjects
            all_subjects = {}
            for subjects_str in df['Subjects'].dropna():
                subjects = parse_subjects(subjects_str)
                for subject in subjects:
                    all_subjects[subject] = all_subjects.get(subject, 0) + 1

            # Sort by count
            sorted_subjects = sorted(all_subjects.items(), key=lambda x: -x[1])

            # Show top subjects with search
            subject_search_widget_key = f"subject_search{key_suffix}" if key_suffix else "subject_search"
            subject_search = st.text_input("Search subjects", key=subject_search_widget_key)

            if subject_search:
                filtered_subjects = [s for s, _ in sorted_subjects if subject_search.lower() in s.lower()][:50]
            else:
                filtered_subjects = [s for s, _ in sorted_subjects[:50]]

            subject_filter_widget_key = f"subject_filter{key_suffix}" if key_suffix else "subject_filter"
            subject_filter = st.multiselect(
                "Select subjects",
                options=sorted(filtered_subjects),
                default=st.session_state.get('filter_subjects', []),
                key=subject_filter_widget_key
            )

            if subject_filter:
                filters['Subjects'] = subject_filter
                st.session_state['filter_subjects'] = subject_filter

        st.divider()


        st.divider()

        # Open Access filter
        st.markdown("#### Access Status")
        access_widget_key = f"access_filter{key_suffix}" if key_suffix else "access_filter"
        access_filter = st.radio(
            "Open Access",
            options=["All", "Yes", "No"],
            index=0,
            key=access_widget_key
        )

        if access_filter != "All":
            filters['Open Access'] = (access_filter == "Yes")
            st.session_state['filter_access'] = access_filter

        # OCLC Holdings filter
        if 'OCLC Holdings' in df.columns:
            oclc_widget_key = f"oclc_holdings_filter{key_suffix}" if key_suffix else "oclc_holdings_filter"
            oclc_holdings_filter = st.number_input(
                "Minimum OCLC Holdings",
                min_value=0,
                value=st.session_state.get('filter_oclc_holdings', 0),
                step=1,
                key=oclc_widget_key
            )
            if oclc_holdings_filter > 0:
                filters['OCLC Holdings'] = oclc_holdings_filter
                st.session_state['filter_oclc_holdings'] = oclc_holdings_filter

        # PALCI Holdings filter
        if 'PALCI Holdings' in df.columns:
            palci_widget_key = f"palci_holdings_filter{key_suffix}" if key_suffix else "palci_holdings_filter"
            palci_holdings_filter = st.number_input(
                "Minimum PALCI Holdings",
                min_value=0,
                value=st.session_state.get('filter_palci_holdings', 0),
                step=1,
                key=palci_widget_key
            )
            if palci_holdings_filter > 0:
                filters['PALCI Holdings'] = palci_holdings_filter
                st.session_state['filter_palci_holdings'] = palci_holdings_filter

        # E-copy? filter
        if 'E-copy?' in df.columns:
            ecopy_widget_key = f"ecopy_filter{key_suffix}" if key_suffix else "ecopy_filter"
            ecopy_filter = st.radio(
                "E-copy Available",
                options=["All", "Yes", "No"],
                index=0,
                key=ecopy_widget_key
            )

            if ecopy_filter != "All":
                filters['E-copy?'] = (ecopy_filter == "Yes")
                st.session_state['filter_ecopy'] = ecopy_filter

        # HathiTrust filter
        if 'HathiTrust' in df.columns:
            hathi_widget_key = f"hathitrust_filter{key_suffix}" if key_suffix else "hathitrust_filter"
            hathitrust_filter = st.checkbox(
                "Has HathiTrust Copy",
                value=st.session_state.get('filter_hathitrust', False),
                key=hathi_widget_key
            )
            if hathitrust_filter:
                filters['HathiTrust'] = True
                st.session_state['filter_hathitrust'] = hathitrust_filter

        # Item ID filter (MMS Id)
        if 'MMS Id' in df.columns:
            item_id_widget_key = f"item_id_filter{key_suffix}" if key_suffix else "item_id_filter"
            item_id_filter = st.text_input(
                "Item ID (MMS ID)",
                value=st.session_state.get('filter_item_id', ""),
                key=item_id_widget_key
            )
            if item_id_filter:
                filters['MMS Id'] = item_id_filter
                st.session_state['filter_item_id'] = item_id_filter

        # Decision filter
        if 'Decision' in df.columns:
            decision_widget_key = f"decision_filter{key_suffix}" if key_suffix else "decision_filter"
            decision_filter = st.radio(
                "Decision",
                options=["All", "Blank", "KEEP", "DISCARD"],
                index=0 if st.session_state.get('filter_decision', "All") == "All" else (1 if st.session_state.get('filter_decision') == "Blank" else (2 if st.session_state.get('filter_decision') == "KEEP" else 3)),
                key=decision_widget_key
            )
            if decision_filter != "All":
                if decision_filter == "Blank":
                    # Filter for empty/null values
                    filters['Decision'] = ""
                else:
                    filters['Decision'] = decision_filter
                st.session_state['filter_decision'] = decision_filter

        # Selector filter
        if 'Selector' in df.columns:
            selector_widget_key = f"selector_filter{key_suffix}" if key_suffix else "selector_filter"
            # Get unique non-null values for the selector column
            selector_vals = df['Selector'].dropna().astype(str).unique()
            selector_vals = [v for v in selector_vals if v and v.strip()]
            selector_options = ["All"] + sorted(selector_vals)
            selector_default = st.session_state.get('filter_selector', "All")
            if selector_default not in selector_options:
                selector_default = "All"
            selector_index = selector_options.index(selector_default)
            selector_filter = st.selectbox(
                "Selector",
                options=selector_options,
                index=selector_index,
                key=selector_widget_key
            )
            if selector_filter != "All":
                filters['Selector'] = selector_filter
                st.session_state['filter_selector'] = selector_filter

        # Notes filter (Retention Note)
        if 'Retention Note' in df.columns:
            notes_widget_key = f"notes_filter{key_suffix}" if key_suffix else "notes_filter"
            notes_filter = st.text_input(
                "Notes",
                value=st.session_state.get('filter_notes', ""),
                key=notes_widget_key
            )
            if notes_filter:
                filters['Retention Note'] = notes_filter
                st.session_state['filter_notes'] = notes_filter

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
                # Use the actual column name from the dataframe (Google Sheet format)
                loans_column = 'Num of Loans Including Pre-Migration (In House + Not In House)' if 'Num of Loans Including Pre-Migration (In House + Not In House)' in result_df.columns else 'Loans Including Pre-Migration (In House + Not In House)'
                mask = pd.Series(False, index=result_df.index, dtype=bool)
                for min_val, max_val in value:
                    if max_val == float('inf'):
                        mask |= (result_df[loans_column] >= min_val)
                    else:
                        mask |= (result_df[loans_column] >= min_val) & (result_df[loans_column] <= max_val)
                result_df = result_df[mask]
            continue

        if column == 'Subjects':
            # Subject filter - parse and check each record
            def has_matching_subject(subjects_str):
                if pd.isna(subjects_str):
                    return False
                subjects = parse_subjects(subjects_str)
                return any(s in value for s in subjects)

            mask = result_df['Subjects'].apply(has_matching_subject)
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
            # Exact match filter (including empty string for blanks)
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