"""
Configuration settings for the Library Dashboard application.
"""

import os

# Application settings
APP_NAME = "Library Dashboard"
APP_VERSION = "1.0.0"

# Database settings
DATA_DIR = os.path.join(os.path.dirname(__file__), 'data')
DATABASE_NAME = 'library.db'
DATABASE_PATH = os.path.join(DATA_DIR, DATABASE_NAME)
DATABASE_URL = f"sqlite:///{DATABASE_PATH}"

# Data processing settings
MAX_UPLOAD_SIZE_MB = 100
SUPPORTED_FORMATS = ['.csv', '.xlsx', '.xlsm', '.xls']

# OCLC control number settings
OCLC_PREFIXES = ['ocm', 'ocn', 'on']

# Call number settings
SUPPORTED_CLASSIFICATIONS = [
    'Library of Congress classification',
    'Dewey Decimal classification',
]

# Export settings
DEFAULT_EXPORT_COLUMNS = [
    'title',
    'author',
    'publisher',
    'publication_date',
    'material_type',
    'permanent_call_number',
    'isbn_normalized',
    'issn_normalized',
    'oclc_control_number',
    'mms_id',
    'barcode',
    'num_loans',
]

# Visualization settings
DEFAULT_CHART_HEIGHT = 400
DEFAULT_CHART_WIDTH = 800
TOP_N_DEFAULT = 20

# Color scheme (rose, teal, orange, gold)
COLOR_PALETTE = {
    'primary': '#B4436C',      # Dark rose - primary color
    'secondary': '#4D9078',    # Teal - secondary color
    'tertiary': '#F78154',     # Orange - tertiary color
    'accent': '#F2C14E',       # Gold - accent color
    'highlight': '#FEF9E7',    # Light gold background
    'neutral': '#4B5563',      # Gray for secondary text
    'background': '#FFFFFF',   # White background
}
