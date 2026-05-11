# Library Dashboard Application

A Python application to parse, clean, normalize, and store tabular data from bibliographic records representing print library resources.

## Features

- **Data Import**: Parse CSV and Excel files containing bibliographic records
- **Data Cleaning**: Normalize and clean various data fields including:
  - OCLC Control Numbers (removing prefixes like "ocm", "ocn", "on" and leading zeros)
  - ISBN, ISSN, Barcode, MMS ID normalization
  - Title punctuation cleanup
  - Author name normalization (Library of Congress names)
  - Publisher name cleanup
  - Publication date normalization
  - Call number parsing using pycallnumber
  - Subject parsing and normalization
- **Interactive Dashboards**: View cleaned data in tabular format with filtering
- **Visualizations**: Charts for usage, age, subject coverage, and OCLC holdings
- **Report Generation**: Create and export interactive reports
- **Data Export**: Export cleaned data as CSV or Excel files

## Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Run the application:
```bash
streamlit run app.py
```

## Usage

1. Upload your bibliographic data file (CSV or Excel format)
2. The application will automatically clean and normalize the data
3. Browse the data in tabular or detailed view
4. Use facet filters to narrow down results
5. Generate reports and visualizations
6. Export data in your preferred format

## Data Columns

The application expects the following columns:
- Library Name
- Location Name
- Permanent Call Number Type
- Permanent Call Number
- Item Copy Id
- Material Type
- Barcode
- Retention Note
- Title
- Author
- Author (Contributor)
- Publisher
- Publication Date
- Edition
- Series
- MMS Id
- Num of Loans Including Pre-Migration (In House + Not In House)
- ISBN
- ISSN
- OCLC Control Number (035a)
- Subjects
- Creation Date
- Last Loan Date
- Normalized Call Number
- Open Access
- Has Committed To Retain

## Key Identifiers

The following columns serve as match points:
- MMS Id (text)
- Barcode (text)
- Permanent Call Number
- ISBN
- ISSN
- OCLC Control Number (035a) - cleaned to numeric only
