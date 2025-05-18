"""Data models for PubMed articles."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional, Dict, Any


@dataclass
class Author:
    """Representation of an article author."""

    last_name: str
    fore_name: Optional[str] = None
    initials: Optional[str] = None
    affiliations: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary.

        Returns:
            Dictionary representation of the author
        """
        return {
            "last_name": self.last_name,
            "fore_name": self.fore_name,
            "initials": self.initials,
            "affiliations": self.affiliations,
        }


@dataclass
class Article:
    """Representation of a PubMed article."""

    pmid: str
    title: str
    abstract: str
    authors: List[Author] = field(default_factory=list)
    keywords: List[str] = field(default_factory=list)
    publication_date: Optional[datetime] = None
    doi: Optional[str] = None
    journal: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage.

        Returns:
            Dictionary representation of the article
        """
        return {
            "pmid": self.pmid,
            "title": self.title,
            "abstract": self.abstract,
            "authors": [author.to_dict() for author in self.authors],
            "keywords": self.keywords,
            "publication_date": self.publication_date.isoformat() if self.publication_date else None,
            "doi": self.doi,
            "journal": self.journal,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Article":
        """Create an Article from a dictionary.

        Args:
            data: Dictionary representation of an article

        Returns:
            Article instance
        """
        # Convert publication date string to datetime if present
        pub_date = data.get("publication_date")
        if isinstance(pub_date, str):
            try:
                pub_date = datetime.fromisoformat(pub_date)
            except ValueError:
                pub_date = None

        # Convert author dictionaries to Author objects
        authors = []
        for author_data in data.get("authors", []):
            authors.append(
                Author(
                    last_name=author_data.get("last_name", ""),
                    fore_name=author_data.get("fore_name"),
                    initials=author_data.get("initials"),
                    affiliations=author_data.get("affiliations", []),
                )
            )

        return cls(
            pmid=data.get("pmid", ""),
            title=data.get("title", ""),
            abstract=data.get("abstract", ""),
            authors=authors,
            keywords=data.get("keywords", []),
            publication_date=pub_date,
            doi=data.get("doi"),
            journal=data.get("journal"),
        )
