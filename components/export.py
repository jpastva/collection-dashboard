"""
Export functionality for bibliographic data and reports.
"""

import pandas as pd
import io
from typing import Optional, Dict, Any, List


def export_to_csv(df: pd.DataFrame, include_columns: Optional[List[str]] = None) -> bytes:
    """
    Export DataFrame to CSV format.

    Args:
        df: DataFrame to export
        include_columns: Optional list of columns to include

    Returns:
        CSV data as bytes
    """
    if df.empty:
        return b""

    # Select columns if specified
    if include_columns:
        available_cols = [col for col in include_columns if col in df.columns]
        export_df = df[available_cols]
    else:
        export_df = df

    # Convert to CSV
    csv_buffer = io.StringIO()
    export_df.to_csv(csv_buffer, index=False, encoding='utf-8-sig')

    return csv_buffer.getvalue().encode('utf-8')


def export_to_excel(
    df: pd.DataFrame,
    include_columns: Optional[List[str]] = None,
    sheet_name: str = "Data"
) -> bytes:
    """
    Export DataFrame to Excel format.

    Args:
        df: DataFrame to export
        include_columns: Optional list of columns to include
        sheet_name: Name of the Excel sheet

    Returns:
        Excel file as bytes
    """
    if df.empty:
        return b""

    # Select columns if specified
    if include_columns:
        available_cols = [col for col in include_columns if col in df.columns]
        export_df = df[available_cols]
    else:
        export_df = df

    # Create Excel file in memory
    output = io.BytesIO()

    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        export_df.to_excel(writer, sheet_name=sheet_name, index=False)

        # Get the xlsxwriter workbook and worksheet
        workbook = writer.book
        worksheet = writer.sheets[sheet_name]

        # Add formats
        header_format = workbook.add_format({
            'bold': True,
            'bg_color': '#B4436C',
            'font_color': 'white',
            'border': 1,
            'align': 'left',
            'valign': 'vcenter',
        })

        cell_format = workbook.add_format({
            'border': 1,
            'align': 'left',
            'valign': 'vcenter',
            'text_wrap': True,
        })

        # Apply header format
        for col_num, value in enumerate(export_df.columns.values):
            worksheet.write(0, col_num, value, header_format)

        # Auto-adjust column widths
        for i, col in enumerate(export_df.columns):
            # Calculate max width based on column content
            max_width = max(
                len(str(col)),
                export_df[col].astype(str).apply(len).max() if len(export_df) > 0 else 0
            )
            # Limit max width to 50
            max_width = min(max_width, 50)
            worksheet.set_column(i, i, max_width + 2, cell_format)

    output.seek(0)
    return output.read()


def create_summary_report(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Create a summary report of the bibliographic data.

    Args:
        df: DataFrame with bibliographic records

    Returns:
        Dictionary containing summary statistics and data
    """
    from datetime import datetime

    if df.empty:
        return {
            'generated_at': datetime.now().isoformat(),
            'total_items': 0,
            'summary': {},
        }

    current_year = datetime.now().year

    # Basic counts
    total_items = len(df)
    unique_titles = df['title'].nunique() if 'title' in df.columns else 0
    unique_authors = df['author'].nunique() if 'author' in df.columns and df['author'].notna().any() else 0

    # Usage statistics
    total_loans = int(df['num_loans'].sum()) if 'num_loans' in df.columns else 0
    avg_loans = float(df['num_loans'].mean()) if 'num_loans' in df.columns and len(df) > 0 else 0
    max_loans = int(df['num_loans'].max()) if 'num_loans' in df.columns else 0

    # Publication statistics
    pub_stats = {}
    if 'publication_year_start' in df.columns:
        valid_years = df[df['publication_year_start'].notna()]['publication_year_start']
        if len(valid_years) > 0:
            pub_stats = {
                'earliest_year': int(valid_years.min()),
                'latest_year': int(valid_years.max()),
                'mean_year': float(valid_years.mean()),
                'median_year': float(valid_years.median()),
            }

    # Material type distribution
    material_dist = {}
    if 'material_type' in df.columns:
        material_dist = df['material_type'].value_counts().head(10).to_dict()

    # LC Class distribution
    lc_dist = {}
    if 'call_number_classification' in df.columns:
        lc_df = df[df['call_number_classification'] == 'LC']
        if len(lc_df) > 0:
            lc_dist = lc_df['call_number_class'].value_counts().head(10).to_dict()

    # Subject distribution
    subject_dist = {}
    if 'subjects' in df.columns:
        from utils.cleaners import parse_subjects
        all_subjects = {}
        for subjects_str in df['subjects'].dropna():
            subjects = parse_subjects(subjects_str)
            for subject in subjects:
                all_subjects[subject] = all_subjects.get(subject, 0) + 1
        subject_dist = dict(sorted(all_subjects.items(), key=lambda x: -x[1])[:20])

    # Retention stats
    retention_stats = {}
    if 'has_committed_to_retain' in df.columns:
        committed_count = int(df['has_committed_to_retain'].sum())
        retention_stats = {
            'committed_to_retain': committed_count,
            'not_committed': total_items - committed_count,
        }

    # Open access stats
    access_stats = {}
    if 'open_access' in df.columns:
        open_count = int(df['open_access'].sum())
        access_stats = {
            'open_access': open_count,
            'restricted': total_items - open_count,
        }

    return {
        'generated_at': datetime.now().isoformat(),
        'total_items': total_items,
        'unique_titles': unique_titles,
        'unique_authors': unique_authors,
        'total_loans': total_loans,
        'average_loans': round(avg_loans, 2),
        'max_loans': max_loans,
        'publication_stats': pub_stats,
        'material_distribution': material_dist,
        'lc_class_distribution': lc_dist,
        'subject_distribution': subject_dist,
        'retention_stats': retention_stats,
        'access_stats': access_stats,
    }


def export_report_to_excel(
    df: pd.DataFrame,
    report_data: Dict[str, Any]
) -> bytes:
    """
    Export a comprehensive report to Excel with multiple sheets.

    Args:
        df: DataFrame with bibliographic records
        report_data: Summary report data

    Returns:
        Excel file as bytes
    """
    output = io.BytesIO()

    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        # Sheet 1: Summary
        summary_df = pd.DataFrame({
            'Metric': [
                'Total Items',
                'Unique Titles',
                'Unique Authors',
                'Total Loans',
                'Average Loans',
                'Max Loans',
            ],
            'Value': [
                report_data.get('total_items', 0),
                report_data.get('unique_titles', 0),
                report_data.get('unique_authors', 0),
                report_data.get('total_loans', 0),
                report_data.get('average_loans', 0),
                report_data.get('max_loans', 0),
            ]
        })
        summary_df.to_excel(writer, sheet_name='Summary', index=False)

        # Sheet 2: Material Types
        material_df = pd.DataFrame(
            list(report_data.get('material_distribution', {}).items()),
            columns=['Material Type', 'Count']
        )
        material_df.to_excel(writer, sheet_name='Material Types', index=False)

        # Sheet 3: LC Classes
        lc_df = pd.DataFrame(
            list(report_data.get('lc_class_distribution', {}).items()),
            columns=['LC Class', 'Count']
        )
        lc_df.to_excel(writer, sheet_name='LC Classes', index=False)

        # Sheet 4: Subjects
        subject_df = pd.DataFrame(
            list(report_data.get('subject_distribution', {}).items()),
            columns=['Subject', 'Count']
        )
        subject_df.to_excel(writer, sheet_name='Top Subjects', index=False)

        # Sheet 5: Full Data
        df.to_excel(writer, sheet_name='Full Data', index=False)

        # Format sheets
        workbook = writer.book
        header_format = workbook.add_format({
            'bold': True,
            'bg_color': '#B4436C',
            'font_color': 'white',
            'border': 1,
        })

        for sheet_name in writer.sheets:
            worksheet = writer.sheets[sheet_name]
            for col_num in range(len(df.columns) if sheet_name == 'Full Data' else 2):
                worksheet.write(0, col_num,
                    summary_df.columns[col_num] if sheet_name == 'Summary' else
                    material_df.columns[col_num] if sheet_name == 'Material Types' else
                    lc_df.columns[col_num] if sheet_name == 'LC Classes' else
                    subject_df.columns[col_num] if sheet_name == 'Top Subjects' else
                    df.columns[col_num],
                    header_format)

    output.seek(0)
    return output.read()
