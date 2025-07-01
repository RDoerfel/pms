"""Tests for article model."""

import pytest
from datetime import datetime

from pms.models import Article, Author


def test_article_creation():
    """Test that articles can be created correctly."""
    # Create an author
    author = Author(
        last_name="Smith",
        fore_name="John",
        initials="J",
        affiliations=["University of Example"],
    )

    # Create an article
    article = Article(
        pmid="12345",
        title="Test Article",
        abstract="This is a test abstract.",
        authors=[author],
        keywords=["test", "example"],
        publication_date=datetime(2020, 1, 1),
        doi="10.1234/test",
        journal="Test Journal",
    )

    # Check basic properties
    assert article.pmid == "12345"
    assert article.title == "Test Article"
    assert article.abstract == "This is a test abstract."
    assert len(article.authors) == 1
    assert article.authors[0].last_name == "Smith"
    assert article.keywords == ["test", "example"]
    assert article.publication_date == datetime(2020, 1, 1)
    assert article.doi == "10.1234/test"
    assert article.journal == "Test Journal"


def test_article_to_from_dict():
    """Test article conversion to/from dictionary."""
    # Create an article
    article = Article(
        pmid="12345",
        title="Test Article",
        abstract="This is a test abstract.",
        authors=[
            Author(
                last_name="Smith",
                fore_name="John",
                initials="J",
                affiliations=["University of Example"],
            )
        ],
        keywords=["test", "example"],
        publication_date=datetime(2020, 1, 1),
        doi="10.1234/test",
        journal="Test Journal",
    )

    # Convert to dictionary
    article_dict = article.to_dict()

    # Check dictionary contents
    assert article_dict["pmid"] == "12345"
    assert article_dict["title"] == "Test Article"
    assert article_dict["abstract"] == "This is a test abstract."
    assert len(article_dict["authors"]) == 1
    assert article_dict["authors"][0]["last_name"] == "Smith"
    assert article_dict["keywords"] == ["test", "example"]
    assert article_dict["publication_date"] == "2020-01-01T00:00:00"
    assert article_dict["doi"] == "10.1234/test"
    assert article_dict["journal"] == "Test Journal"

    # Convert back to article
    new_article = Article.from_dict(article_dict)

    # Check reconstituted article
    assert new_article.pmid == article.pmid
    assert new_article.title == article.title
    assert new_article.abstract == article.abstract
    assert len(new_article.authors) == len(article.authors)
    assert new_article.authors[0].last_name == article.authors[0].last_name
    assert new_article.keywords == article.keywords
    assert new_article.publication_date == article.publication_date
    assert new_article.doi == article.doi
    assert new_article.journal == article.journal
