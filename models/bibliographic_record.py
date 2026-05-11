"""
SQLAlchemy model for bibliographic records.
"""

from sqlalchemy import Column, Integer, String, Text, Boolean, Float, ForeignKey, Index
from sqlalchemy.orm import relationship
from .database import Base


class BibliographicRecord(Base):
    """
    Model representing a bibliographic record for a library resource.
    """
    __tablename__ = 'bibliographic_records'

    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)

    # Key identifiers (for matching)
    mms_id = Column(String(100), index=True)
    barcode = Column(String(100), index=True)
    permanent_call_number = Column(String(255), index=True)
    isbn = Column(String(50), index=True)
    issn = Column(String(20), index=True)
    oclc_control_number = Column(String(50), index=True)

    # Basic bibliographic info
    library_name = Column(String(255))
    location_name = Column(String(255))
    title = Column(Text)
    author = Column(String(500))
    author_contributor = Column(String(500))
    publisher = Column(String(255))
    publication_date = Column(String(50))
    publication_year_start = Column(Integer)
    publication_year_end = Column(Integer)
    edition = Column(String(255))
    series = Column(String(500))

    # Item-specific info
    item_policy = Column(String(100))
    item_copy_id = Column(String(100))
    material_type = Column(String(100))
    call_number_type = Column(String(100))
    permanent_call_number_original = Column(String(255))
    normalized_call_number = Column(String(255))
    retention_note = Column(String(500))

    # Call number parsing results (LC or Dewey)
    call_number_classification = Column(String(50))  # 'LC' or 'DEWEY'
    call_number_class = Column(String(50))
    call_number_subclass = Column(String(50))
    call_number_sortable = Column(String(255))

    # Usage stats
    num_loans = Column(Integer, default=0)
    num_requests = Column(Integer, default=0)

    # Additional info
    open_access = Column(Boolean, default=False)
    e_copy = Column(Boolean, default=False)
    electronic_access_type = Column(String(255))
    e_overlap_collection = Column(String(500))
    has_committed_to_retain = Column(Boolean, default=False)
    creation_date = Column(String(50))
    last_loan_date = Column(String(50), index=True)

    # Bibliographic details
    publication_place = Column(String(255))
    isbn_normalized = Column(String(50), index=True)
    issn_normalized = Column(String(20), index=True)
    oclc_number_raw = Column(String(50), index=True)

    # Subjects (stored as semicolon-delimited string, parsed for faceting)
    subjects = Column(Text)

    # Holdings
    oclc_holdings = Column(Integer)
    palci_holdings = Column(Integer)

    # Metadata
    created_at = Column(String(50))
    updated_at = Column(String(50))

    # Indexes for common queries
    __table_args__ = (
        Index('ix_title', 'title', postgresql_using='gin'),
        Index('ix_author', 'author', postgresql_using='gin'),
        Index('ix_subjects', 'subjects', postgresql_using='gin'),
        Index('ix_publication_year', 'publication_year_start'),
        Index('ix_num_loans', 'num_loans'),
    )

    def to_dict(self):
        """Convert record to dictionary."""
        return {
            'id': self.id,
            'mms_id': self.mms_id,
            'barcode': self.barcode,
            'permanent_call_number': self.permanent_call_number,
            'isbn': self.isbn,
            'issn': self.issn,
            'oclc_control_number': self.oclc_control_number,
            'library_name': self.library_name,
            'location_name': self.location_name,
            'title': self.title,
            'author': self.author,
            'author_contributor': self.author_contributor,
            'publisher': self.publisher,
            'publication_date': self.publication_date,
            'publication_year_start': self.publication_year_start,
            'publication_year_end': self.publication_year_end,
            'edition': self.edition,
            'series': self.series,
            'item_policy': self.item_policy,
            'item_copy_id': self.item_copy_id,
            'material_type': self.material_type,
            'call_number_type': self.call_number_type,
            'permanent_call_number_original': self.permanent_call_number_original,
            'normalized_call_number': self.normalized_call_number,
            'call_number_classification': self.call_number_classification,
            'call_number_class': self.call_number_class,
            'call_number_subclass': self.call_number_subclass,
            'call_number_sortable': self.call_number_sortable,
            'num_loans': self.num_loans,
            'num_requests': self.num_requests,
            'open_access': self.open_access,
            'e_copy': self.e_copy,
            'electronic_access_type': self.electronic_access_type,
            'e_overlap_collection': self.e_overlap_collection,
            'has_committed_to_retain': self.has_committed_to_retain,
            'creation_date': self.creation_date,
            'last_loan_date': self.last_loan_date,
            'publication_place': self.publication_place,
            'isbn_normalized': self.isbn_normalized,
            'issn_normalized': self.issn_normalized,
            'oclc_number_raw': self.oclc_number_raw,
            'palci_holdings': self.palci_holdings,
            'subjects': self.subjects,
            'oclc_holdings': self.oclc_holdings,
            'retention_note': self.retention_note,
        }

    def __repr__(self):
        return f"<BibliographicRecord(id={self.id}, title='{self.title[:50]}...')>"
