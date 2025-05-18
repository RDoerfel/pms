"""Project management functionality."""

import logging
import uuid
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime

from pms.api import PubMedClient
from pms.storage import Database, JSONLStorage
from pms.models import Article

logger = logging.getLogger(__name__)


class ProjectManager:
    """Manager for PubMed search projects."""

    def __init__(self) -> None:
        """Initialize the project manager."""
        self.db = Database()
        self.storage = JSONLStorage()
        self.client = PubMedClient()

    def close(self) -> None:
        """Close database connections."""
        self.db.close()

    def __enter__(self) -> "ProjectManager":
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Context manager exit."""
        self.close()

    def create_project(self, name: str, description: Optional[str] = None, project_id: Optional[str] = None) -> str:
        """Create a new project.

        Args:
            name: Project name
            description: Project description
            project_id: Optional project ID. If None, a UUID will be generated.

        Returns:
            Project ID
        """
        if project_id is None:
            project_id = str(uuid.uuid4())

        success = self.db.create_project(project_id, name, description)
        if not success:
            raise ValueError(f"Failed to create project: {name}")

        logger.info(f"Created project {project_id}: {name}")
        return project_id

    def get_project(self, project_id: str) -> Optional[Tuple[str, str, str]]:
        """Get project details.

        Args:
            project_id: Project ID

        Returns:
            Tuple of (id, name, description) or None if not found
        """
        return self.db.get_project(project_id)

    def list_projects(self) -> List[Tuple[str, str, str]]:
        """List all projects.

        Returns:
            List of (id, name, description) tuples
        """
        return self.db.list_projects()

    def search_and_store(
        self,
        project_id: str,
        query: str,
        max_results: int = 100,
        date_range: Optional[Tuple[str, str]] = None,
        batch_size: int = 100,
    ) -> Dict[str, int]:
        """Search PubMed and store articles for a project.

        Args:
            project_id: Project ID
            query: PubMed search query
            max_results: Maximum number of results to return
            date_range: Optional tuple of (start_date, end_date) in YYYY/MM/DD format
            batch_size: Batch size for fetching articles

        Returns:
            Dictionary with search statistics
        """
        # Check if project exists
        project = self.db.get_project(project_id)
        if not project:
            raise ValueError(f"Project not found: {project_id}")

        # Search PubMed
        logger.info(f"Searching PubMed: {query}")
        pmids = self.client.search(query, max_results, date_range)
        logger.info(f"Found {len(pmids)} articles")

        if not pmids:
            return {
                "found": 0,
                "new": 0,
                "fetched": 0,
                "stored": 0,
            }

        # Filter out PMIDs that are already in the project
        new_pmids = self.db.filter_new_pmids(project_id, pmids)
        logger.info(f"{len(new_pmids)} new articles to fetch")

        if not new_pmids:
            return {
                "found": len(pmids),
                "new": 0,
                "fetched": 0,
                "stored": 0,
            }

        # Fetch articles in batches
        results = {
            "found": len(pmids),
            "new": len(new_pmids),
            "fetched": 0,
            "stored": 0,
        }

        for i in range(0, len(new_pmids), batch_size):
            batch_pmids = new_pmids[i : i + batch_size]
            logger.info(f"Fetching batch {i//batch_size + 1}/{(len(new_pmids) + batch_size - 1)//batch_size}")

            # Fetch articles
            articles = self.client.fetch_articles(batch_pmids)
            results["fetched"] += len(articles)

            # Store articles
            if articles:
                # Add articles to database tracking
                for article in articles:
                    self.db.add_article(article.pmid, article.doi, article.title)
                    self.db.link_article_to_project(project_id, article.pmid)

                # Store articles in JSONL
                stored = self.storage.store_articles(project_id, articles)
                results["stored"] += stored

        logger.info(
            f"Search results: found={results['found']}, new={results['new']}, "
            f"fetched={results['fetched']}, stored={results['stored']}"
        )
        return results

    def get_articles(self, project_id: str) -> List[Article]:
        """Get all articles for a project.

        Args:
            project_id: Project ID

        Returns:
            List of articles
        """
        # Check if project exists
        project = self.db.get_project(project_id)
        if not project:
            raise ValueError(f"Project not found: {project_id}")

        return self.storage.get_articles(project_id)

    def get_article_count(self, project_id: str) -> int:
        """Get the number of articles in a project.

        Args:
            project_id: Project ID

        Returns:
            Number of articles
        """
        return self.db.count_project_articles(project_id)
