"""
Data visualization components for the library dashboard.
Uses Plotly for interactive charts.
"""

import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
from typing import Optional, List, Dict, Any

# Color scheme with rose, teal, orange, and gold tones
COLOR_PALETTE = {
    'primary': '#B4436C',      # Dark rose - primary data color
    'secondary': '#4D9078',    # Teal - secondary data color
    'tertiary': '#F78154',     # Orange - tertiary data color
    'accent': '#F2C14E',       # Gold - accent/highlight color
    'text_dark': '#1F2937',    # Dark text for readability
    'text_light': '#4B5563',   # Secondary text
    'background': '#FFFFFF',   # White background
}


def create_usage_chart(df: pd.DataFrame) -> go.Figure:
    """
    Create a chart showing usage of materials based on Loans Including Pre-Migration (In House + Not In House).
    """
    if df.empty or 'Num of Loans Including Pre-Migration (In House + Not In House)' not in df.columns:
        return go.Figure().add_annotation(text="No usage data available", showarrow=False)

    # Include all items, including those with 0 usage
    usage_df = df.copy()

    if usage_df.empty:
        return go.Figure().add_annotation(
            text="No items found",
            showarrow=False
        )

    # Updated bins and labels to properly include 0 usage items
    bins = [-1, 0, 1, 5, 10, 25, 50, 100, float('inf')]
    labels = ['0', '1', '2-5', '6-10', '11-25', '26-50', '51-100', '100+']
    usage_df['Loan Range'] = pd.cut(usage_df['Num of Loans Including Pre-Migration (In House + Not In House)'], bins=bins, labels=labels, right=True)

    loan_counts = usage_df.groupby('Loan Range', observed=True).size().reset_index(name='Count')
    loan_counts = loan_counts.sort_values('Loan Range')

    fig = go.Figure(data=[
        go.Bar(
            x=loan_counts['Loan Range'].astype(str),
            y=loan_counts['Count'],
            marker_color=[COLOR_PALETTE['primary']] * len(loan_counts),
            hovertemplate='<b>%{x} loans</b><br>Items: %{y}<extra></extra>'
        )
    ])

    fig.update_layout(
        title={'text': 'Circulation Usage Distribution', 'font': {'size': 18, 'color': COLOR_PALETTE['primary']}},
        xaxis_title='Number of Loans',
        yaxis_title='Number of Items',
        plot_bgcolor='white',
        paper_bgcolor='white',
        font={'color': COLOR_PALETTE['text_dark']},
        showlegend=False,
        hovermode='x unified',
    )

    fig.update_xaxes(gridcolor='#E5E7EB', tickfont={'color': COLOR_PALETTE['text_dark']})
    fig.update_yaxes(gridcolor='#E5E7EB', tickfont={'color': COLOR_PALETTE['text_dark']})

    return fig


def create_age_distribution_chart(df: pd.DataFrame) -> go.Figure:
    """
    Create a chart showing age of materials based on Publication Date.
    """
    if df.empty or 'Publication Year Start' not in df.columns:
        return go.Figure().add_annotation(text="No publication date data available", showarrow=False)

    age_df = df[df['Publication Year Start'].notna()].copy()

    if age_df.empty:
        return go.Figure().add_annotation(
            text="No items with publication year data",
            showarrow=False
        )

    from datetime import datetime
    current_year = datetime.now().year
    age_df['Age'] = current_year - age_df['Publication Year Start']

    bins = list(range(0, 101, 10)) + [float('inf')]
    labels = [f'{i}-{i+9}' for i in range(0, 100, 10)] + ['100+']
    age_df['Age Decade'] = pd.cut(age_df['Age'], bins=bins, labels=labels, right=False)

    age_counts = age_df.groupby('Age Decade', observed=True).size().reset_index(name='Count')
    age_counts = age_counts.sort_values('Age Decade')

    fig = go.Figure(data=[
        go.Bar(
            x=age_counts['Age Decade'].astype(str),
            y=age_counts['Count'],
            marker_color=[COLOR_PALETTE['primary']] * len(age_counts),
            hovertemplate='<b>%{x} years</b><br>Items: %{y}<extra></extra>'
        )
    ])

    fig.update_layout(
        title={'text': 'Material Age Distribution', 'font': {'size': 18, 'color': COLOR_PALETTE['primary']}},
        xaxis_title='Age (Years)',
        yaxis_title='Number of Items',
        plot_bgcolor='white',
        paper_bgcolor='white',
        font={'color': COLOR_PALETTE['text_dark']},
        showlegend=False,
        hovermode='x unified',
    )

    fig.update_xaxes(gridcolor='#E5E7EB', tickangle=45, tickfont={'color': COLOR_PALETTE['text_dark']})
    fig.update_yaxes(gridcolor='#E5E7EB', tickfont={'color': COLOR_PALETTE['text_dark']})

    return fig


def create_subject_coverage_chart(df: pd.DataFrame, top_n: int = 20) -> go.Figure:
    """
    Create a chart showing subject coverage.
    """
    if df.empty:
        return go.Figure().add_annotation(text="No data available", showarrow=False)

    from utils.cleaners import parse_subjects

    subject_counts = {}
    # Terms to filter out
    filter_terms = {"Periodical.", "Periodical", "Periodicals", "Periodicals.", "periodicals.", "United States.", "Zeitschrift", "Electronic journals", "Periodiques"}

    for subjects_str in df['Subjects'].dropna():
        subjects = parse_subjects(subjects_str)
        for subject in subjects:
            # Skip filtered terms
            if subject in filter_terms:
                continue
            subject_counts[subject] = subject_counts.get(subject, 0) + 1

    if not subject_counts:
        return go.Figure().add_annotation(
            text="No subject data available",
            showarrow=False
        )

    sorted_subjects = sorted(subject_counts.items(), key=lambda x: -x[1])[:top_n]
    subjects = [s[0] for s in sorted_subjects]
    counts = [c[1] for c in sorted_subjects]

    fig = go.Figure(data=[
        go.Bar(
            x=counts,
            y=subjects,
            orientation='h',
            marker_color=COLOR_PALETTE['primary'],
            hovertemplate='<b>%{y}</b><br>Items: %{x}<extra></extra>'
        )
    ])

    fig.update_layout(
        title={'text': f'Top {top_n} Subjects', 'font': {'size': 18, 'color': COLOR_PALETTE['primary']}},
        xaxis_title='Number of Items',
        yaxis_title='Subject',
        plot_bgcolor='white',
        paper_bgcolor='white',
        font={'color': COLOR_PALETTE['text_dark'], 'size': 10},
        showlegend=False,
        height=max(400, len(subjects) * 25),
        margin={'l': 200, 'r': 50, 't': 80, 'b': 50},
    )

    fig.update_xaxes(gridcolor='#E5E7EB', tickfont={'color': COLOR_PALETTE['text_dark']})
    fig.update_yaxes(gridcolor='#E5E7EB', tickfont={'color': COLOR_PALETTE['text_dark']})

    return fig


def create_lc_class_coverage_chart(df: pd.DataFrame) -> go.Figure:
    """
    Create a chart showing coverage by Library of Congress Classification classes.
    Uses only Permanent LC Classification Top Line column, excludes Unknown values, and limits to top 25.
    """
    if df.empty:
        return go.Figure().add_annotation(text="No data available", showarrow=False)

    # Use only Permanent LC Classification Top Line column
    lc_class_column = 'Permanent LC Classification Top Line'

    if lc_class_column not in df.columns:
        return go.Figure().add_annotation(text="No LC classification data available", showarrow=False)

    # Filter for Library of Congress classification
    lc_df = df[df[lc_class_column].notna()].copy()

    # Additional filter: only include entries that look like LC classification (start with letters)
    lc_df = lc_df[lc_df[lc_class_column].str.match(r'^[A-Z]', na=False)].copy()

    # Exclude "Unknown" values
    lc_df = lc_df[lc_df[lc_class_column] != "Unknown"].copy()

    if lc_df.empty:
        return go.Figure().add_annotation(
            text="No items with LC classification",
            showarrow=False
        )

    class_counts = lc_df.groupby(lc_class_column).size().reset_index(name='Count')
    class_counts = class_counts.sort_values('Count', ascending=False)

    # Limit to top 25 values
    class_counts = class_counts.head(25)

    from utils.call_number_parser import get_lc_class_description
    class_counts['Description'] = class_counts[lc_class_column].apply(get_lc_class_description)

    fig = go.Figure(data=[
        go.Bar(
            x=class_counts['Count'],
            y=class_counts[lc_class_column],
            orientation='h',
            marker_color=COLOR_PALETTE['primary'],
            hovertemplate='<b>%{y}</b><br>%{text}<br>Items: %{x}<extra></extra>',
            text=class_counts['Description']
        )
    ])

    fig.update_layout(
        title={'text': 'Library of Congress Classification Coverage (Top 25)', 'font': {'size': 18, 'color': COLOR_PALETTE['primary']}},
        xaxis_title='Number of Items',
        yaxis_title='LC Class',
        plot_bgcolor='white',
        paper_bgcolor='white',
        font={'color': COLOR_PALETTE['text_dark']},
        showlegend=False,
        height=max(400, len(class_counts) * 30),
        margin={'l': 80, 'r': 50, 't': 80, 'b': 50},
    )

    fig.update_xaxes(gridcolor='#E5E7EB', tickfont={'color': COLOR_PALETTE['text_dark']})
    fig.update_yaxes(gridcolor='#E5E7EB', tickfont={'color': COLOR_PALETTE['text_dark']})

    return fig


def create_oclc_holdings_chart(df: pd.DataFrame) -> go.Figure:
    """
    Create a chart showing the number of items held by other OCLC libraries.
    """
    if df.empty or 'OCLC Holdings' not in df.columns:
        return go.Figure().add_annotation(text="No OCLC holdings data available", showarrow=False)

    holdings_df = df[df['OCLC Holdings'].notna()].copy()

    if holdings_df.empty:
        return go.Figure().add_annotation(
            text="No OCLC holdings data available",
            showarrow=False
        )

    bins = [0, 10, 50, 100, 500, 1000, 5000, float('inf')]
    labels = ['1-10', '11-50', '51-100', '101-500', '501-1000', '1001-5000', '5000+']
    holdings_df['Holdings Range'] = pd.cut(
        holdings_df['OCLC Holdings'],
        bins=bins,
        labels=labels,
        right=True
    )

    holdings_counts = holdings_df.groupby('Holdings Range', observed=True).size().reset_index(name='Count')
    holdings_counts = holdings_counts.sort_values('Holdings Range')

    fig = go.Figure(data=[
        go.Bar(
            x=holdings_counts['Holdings Range'].astype(str),
            y=holdings_counts['Count'],
            marker_color=[COLOR_PALETTE['primary']] * len(holdings_counts),
            hovertemplate='<b>%{x} libraries</b><br>Items: %{y}<extra></extra>'
        )
    ])

    fig.update_layout(
        title={'text': 'OCLC Library Holdings Distribution', 'font': {'size': 18, 'color': COLOR_PALETTE['primary']}},
        xaxis_title='Number of OCLC Libraries Holding',
        yaxis_title='Number of Items',
        plot_bgcolor='white',
        paper_bgcolor='white',
        font={'color': '#374151'},
        showlegend=False,
        hovermode='x unified',
    )

    fig.update_xaxes(gridcolor='#E5E7EB', tickangle=45)
    fig.update_yaxes(gridcolor='#E5E7EB')

    return fig



def create_publication_timeline_chart(df: pd.DataFrame) -> go.Figure:
    """
    Create a timeline chart showing publications by year.
    """
    if df.empty or 'Publication Year Start' not in df.columns:
        return go.Figure().add_annotation(text="No publication date data available", showarrow=False)

    timeline_df = df[df['Publication Year Start'].notna()].copy()

    if timeline_df.empty:
        return go.Figure().add_annotation(
            text="No items with publication year data",
            showarrow=False
        )

    year_counts = timeline_df.groupby('Publication Year Start').size().reset_index(name='Count')
    year_counts = year_counts.sort_values('Publication Year Start')

    fig = go.Figure(data=[
        go.Scatter(
            x=year_counts['Publication Year Start'],
            y=year_counts['Count'],
            mode='lines+markers',
            line={'color': COLOR_PALETTE['primary'], 'width': 2},
            marker={'size': 6},
            hovertemplate='<b>%{x}</b><br>Items: %{y}<extra></extra>'
        )
    ])

    fig.update_layout(
        title={'text': 'Publication Timeline', 'font': {'size': 18, 'color': COLOR_PALETTE['primary']}},
        xaxis_title='Publication Year',
        yaxis_title='Number of Items',
        plot_bgcolor='white',
        paper_bgcolor='white',
        font={'color': COLOR_PALETTE['text_dark']},
        showlegend=False,
        hovermode='x unified',
    )

    fig.update_xaxes(gridcolor='#E5E7EB', tickfont={'color': COLOR_PALETTE['text_dark']})
    fig.update_yaxes(gridcolor='#E5E7EB', tickfont={'color': COLOR_PALETTE['text_dark']})

    return fig


def create_requests_chart(df: pd.DataFrame) -> go.Figure:
    """
    Create a chart showing requests distribution.
    """
    if df.empty or 'Num of Requests (Total)' not in df.columns:
        return go.Figure().add_annotation(text="No request data available", showarrow=False)

    req_df = df[df['Num of Requests (Total)'] > 0].copy()

    if req_df.empty:
        return go.Figure().add_annotation(
            text="No items with request records",
            showarrow=False
        )

    bins = [0, 1, 5, 10, 25, 50, 100, float('inf')]
    labels = ['1', '2-5', '6-10', '11-25', '26-50', '51-100', '100+']
    req_df['Request Range'] = pd.cut(req_df['Num of Requests (Total)'], bins=bins, labels=labels, right=True)

    req_counts = req_df.groupby('Request Range', observed=True).size().reset_index(name='Count')
    req_counts = req_counts.sort_values('Request Range')

    fig = go.Figure(data=[
        go.Bar(
            x=req_counts['Request Range'].astype(str),
            y=req_counts['Count'],
            marker_color=COLOR_PALETTE['secondary'],
            hovertemplate='<b>%{x} requests</b><br>Items: %{y}<extra></extra>'
        )
    ])

    fig.update_layout(
        title={'text': 'Request Usage Distribution', 'font': {'size': 18, 'color': COLOR_PALETTE['primary']}},
        xaxis_title='Number of Requests',
        yaxis_title='Number of Items',
        plot_bgcolor='white',
        paper_bgcolor='white',
        font={'color': COLOR_PALETTE['text_dark']},
        showlegend=False,
        hovermode='x unified',
    )

    fig.update_xaxes(gridcolor='#E5E7EB', tickfont={'color': COLOR_PALETTE['text_dark']})
    fig.update_yaxes(gridcolor='#E5E7EB', tickfont={'color': COLOR_PALETTE['text_dark']})

    return fig


def create_palci_holdings_chart(df: pd.DataFrame) -> go.Figure:
    """
    Create a chart showing PALCI holdings distribution.
    """
    if df.empty or 'PALCI Holdings' not in df.columns:
        return go.Figure().add_annotation(text="No PALCI holdings data available", showarrow=False)

    holdings_df = df[df['PALCI Holdings'].notna()].copy()

    if holdings_df.empty:
        return go.Figure().add_annotation(
            text="No PALCI holdings data available",
            showarrow=False
        )

    bins = [0, 1, 5, 10, 25, 50, 100, float('inf')]
    labels = ['1', '2-5', '6-10', '11-25', '26-50', '51-100', '100+']
    holdings_df['PALCI Range'] = pd.cut(holdings_df['PALCI Holdings'], bins=bins, labels=labels, right=True)

    counts = holdings_df.groupby('PALCI Range', observed=True).size().reset_index(name='Count')
    counts = counts.sort_values('PALCI Range')

    fig = go.Figure(data=[
        go.Bar(
            x=counts['PALCI Range'].astype(str),
            y=counts['Count'],
            marker_color=COLOR_PALETTE['tertiary'],
            hovertemplate='<b>%{x} libraries</b><br>Items: %{y}<extra></extra>'
        )
    ])

    fig.update_layout(
        title={'text': 'PALCI Library Holdings Distribution', 'font': {'size': 18, 'color': COLOR_PALETTE['primary']}},
        xaxis_title='Number of PALCI Libraries Holding',
        yaxis_title='Number of Items',
        plot_bgcolor='white',
        paper_bgcolor='white',
        font={'color': COLOR_PALETTE['text_dark']},
        showlegend=False,
        hovermode='x unified',
    )

    fig.update_xaxes(gridcolor='#E5E7EB', tickfont={'color': COLOR_PALETTE['text_dark']})
    fig.update_yaxes(gridcolor='#E5E7EB', tickfont={'color': COLOR_PALETTE['text_dark']})

    return fig


def create_last_loan_date_chart(df: pd.DataFrame) -> go.Figure:
    """
    Create a chart showing the distribution of last loan dates.
    """
    if df.empty or 'Last Loan Date' not in df.columns:
        return go.Figure().add_annotation(text="No last loan date data available", showarrow=False)

    loan_df = df[df['Last Loan Date'].notna()].copy()

    if loan_df.empty:
        return go.Figure().add_annotation(
            text="No items with last loan date data",
            showarrow=False
        )

    try:
        loan_df['Last Loan Date'] = pd.to_datetime(loan_df['Last Loan Date'], errors='coerce')
        loan_df = loan_df.dropna(subset=['Last Loan Date'])
    except Exception:
        return go.Figure().add_annotation(text="Error parsing loan dates", showarrow=False)

    if len(loan_df) == 0:
        return go.Figure().add_annotation(text="No valid date data available", showarrow=False)

    year_counts = loan_df['Last Loan Date'].dt.year.value_counts().sort_index().reset_index()
    year_counts.columns = ['Year', 'Count']

    fig = go.Figure(data=[
        go.Bar(
            x=year_counts['Year'],
            y=year_counts['Count'],
            marker_color=COLOR_PALETTE['accent'],
            hovertemplate='<b>%{x}</b><br>Items: %{y}<extra></extra>'
        )
    ])

    fig.update_layout(
        title={'text': 'Last Loan Date Distribution', 'font': {'size': 18, 'color': COLOR_PALETTE['primary']}},
        xaxis_title='Year',
        yaxis_title='Number of Items',
        plot_bgcolor='white',
        paper_bgcolor='white',
        font={'color': COLOR_PALETTE['text_dark']},
        showlegend=False,
        hovermode='x unified',
    )

    fig.update_xaxes(gridcolor='#E5E7EB', tickfont={'color': COLOR_PALETTE['text_dark']})
    fig.update_yaxes(gridcolor='#E5E7EB', tickfont={'color': COLOR_PALETTE['text_dark']})

    return fig


def create_lc_subclass_chart(df: pd.DataFrame, top_n: int = 30) -> go.Figure:
    """
    Create a chart showing coverage by LC subclass.
    """
    if df.empty or 'Permanent LC Classification Top Line' not in df.columns:
        return go.Figure().add_annotation(text="No LC subclass data available", showarrow=False)

    subclass_counts = df['Permanent LC Classification Top Line'].value_counts().reset_index()
    subclass_counts.columns = ['Subclass', 'Count']
    subclass_counts = subclass_counts.head(top_n)

    if subclass_counts.empty:
        return go.Figure().add_annotation(
            text="No LC subclass data available",
            showarrow=False
        )

    fig = go.Figure(data=[
        go.Bar(
            x=subclass_counts['Count'],
            y=subclass_counts['Subclass'],
            orientation='h',
            marker_color=COLOR_PALETTE['primary'],
            hovertemplate='<b>%{y}</b><br>Items: %{x}<extra></extra>'
        )
    ])

    fig.update_layout(
        title={'text': f'Top {top_n} LC Subclasses', 'font': {'size': 18, 'color': COLOR_PALETTE['primary']}},
        xaxis_title='Number of Items',
        yaxis_title='LC Subclass',
        plot_bgcolor='white',
        paper_bgcolor='white',
        font={'color': COLOR_PALETTE['text_dark'], 'size': 10},
        showlegend=False,
        height=max(400, len(subclass_counts) * 25),
        margin={'l': 100, 'r': 50, 't': 80, 'b': 50},
    )

    fig.update_xaxes(gridcolor='#E5E7EB', tickfont={'color': COLOR_PALETTE['text_dark']})
    fig.update_yaxes(gridcolor='#E5E7EB', tickfont={'color': COLOR_PALETTE['text_dark']})

    return fig


def create_ecopy_chart(df: pd.DataFrame) -> go.Figure:
    """
    Create a pie chart showing E-copy distribution.
    """
    if df.empty or 'E-copy?' not in df.columns:
        return go.Figure().add_annotation(text="No E-copy data available", showarrow=False)

    counts = df['E-copy?'].value_counts().reset_index()
    counts.columns = ['Status', 'Count']
    # Convert boolean values to strings for better display
    counts['Status'] = counts['Status'].map({True: 'Has E-copy', False: 'No E-copy'})

    if len(counts) == 0:
        return go.Figure().add_annotation(
            text="No E-copy data available",
            showarrow=False
        )

    fig = go.Figure(data=[
        go.Pie(
            labels=counts['Status'],
            values=counts['Count'],
            marker_colors=[COLOR_PALETTE['primary'], COLOR_PALETTE['secondary']],
            hole=0.4,
            hovertemplate='<b>%{label}</b><br>Items: %{value}<extra></extra>'
        )
    ])

    fig.update_layout(
        title={'text': 'E-Copy Availability', 'font': {'size': 18, 'color': COLOR_PALETTE['primary']}},
        plot_bgcolor='white',
        paper_bgcolor='white',
        font={'color': COLOR_PALETTE['text_dark']},
        showlegend=True,
    )

    return fig


def create_summary_cards(df: pd.DataFrame) -> List[Dict[str, Any]]:
    """
    Create summary statistics for the dashboard.
    """
    if df.empty:
        return []

    from datetime import datetime
    current_year = datetime.now().year

    cards = [
        {
            'title': 'Total Items',
            'value': f"{len(df):,}",
            'icon': '📚'
        },
    ]

    if 'Title' in df.columns:
        unique_titles = df['Title'].nunique()
        cards.append({
            'title': 'Unique Titles',
            'value': f"{unique_titles:,}",
            'icon': '📖'
        })

    if 'Num of Loans Including Pre-Migration (In House + Not In House)' in df.columns:
        total_loans = df['Num of Loans Including Pre-Migration (In House + Not In House)'].sum()
        cards.append({
            'title': 'Total Circulation',
            'value': f"{total_loans:,}",
            'icon': '🔄'
        })

    if 'Publication Year Start' in df.columns:
        valid_years = df[df['Publication Year Start'].notna()]['Publication Year Start']
        if len(valid_years) > 0:
            avg_year = valid_years.mean()
            avg_age = current_year - avg_year
            cards.append({
                'title': 'Average Age',
                'value': f"{avg_age:.1f} years",
                'icon': '📅'
            })

    if 'call_number_classification' in df.columns:
        lc_count = (df['call_number_classification'] == 'Library of Congress classification').sum()
        cards.append({
            'title': 'LC Classified',
            'value': f"{lc_count:,}",
            'icon': '🔤'
        })

    if 'Has Committed To Retain' in df.columns:
        retain_count = df['Has Committed To Retain'].sum()
        cards.append({
            'title': 'Committed to Retain',
            'value': f"{retain_count:,}",
            'icon': '✅'
        })

    return cards
