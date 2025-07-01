"""JSONL storage for articles."""

import os
import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional

from pms.config import config
from pms.models import Article

logger = logging.getLogger(__name__)


class JSONLStorage:
    """JSONL storage for articles."""

    def __init__(self, base_dir: Optional[str] = None) -> None:
        """Initialize the JSONL storage.

        Args:
            base_dir: Base directory for storage. If None, uses the path from config.
        """
        self.base_dir = os.path.expanduser(
            base_dir
            or config.get("storage", "data_dir")
            or "~/.local/share/pms/data"
        )

        # Ensure the directory exists
        Path(self.base_dir).mkdir(parents=True, exist_ok=True)

    def get_project_path(self, project_id: str) -> str:
        """Get the path to the project directory.

        Args:
            project_id: Project identifier

        Returns:
            Path to the project directory
        """
        project_dir = os.path.join(self.base_dir, project_id)
        Path(project_dir).mkdir(exist_ok=True)
        return project_dir

    def store_article(self, project_id: str, article: Article) -> bool:
        """Store an article in the project's JSONL file.

        Args:
            project_id: Project identifier
            article: Article to store

        Returns:
            True if successful, False otherwise
        """
        try:
            project_dir = self.get_project_path(project_id)
            articles_file = os.path.join(project_dir, "articles.jsonl")

            with open(articles_file, "a") as f:
                json.dump(article.to_dict(), f)
                f.write("\n")

            logger.debug(
                f"Stored article {article.pmid} in project {project_id}"
            )
            return True
        except Exception as e:
            logger.error(
                f"Error storing article {article.pmid} in project {project_id}: {e}"
            )
            return False

    def store_articles(self, project_id: str, articles: List[Article]) -> int:
        """Store multiple articles in the project's JSONL file.

        Args:
            project_id: Project identifier
            articles: Articles to store

        Returns:
            Number of articles successfully stored
        """
        if not articles:
            return 0

        try:
            project_dir = self.get_project_path(project_id)
            articles_file = os.path.join(project_dir, "articles.jsonl")

            count = 0
            with open(articles_file, "a") as f:
                for article in articles:
                    json.dump(article.to_dict(), f)
                    f.write("\n")
                    count += 1

            logger.info(f"Stored {count} articles in project {project_id}")
            return count
        except Exception as e:
            logger.error(
                f"Error storing articles in project {project_id}: {e}"
            )
            return 0

    def get_article(self, project_id: str, pmid: str) -> Optional[Article]:
        """Get an article from the project's JSONL file.

        Args:
            project_id: Project identifier
            pmid: PubMed ID of the article

        Returns:
            Article if found, None otherwise
        """
        project_dir = self.get_project_path(project_id)
        articles_file = os.path.join(project_dir, "articles.jsonl")

        if not os.path.exists(articles_file):
            return None

        try:
            with open(articles_file, "r") as f:
                for line in f:
                    article_data = json.loads(line)
                    if article_data.get("pmid") == pmid:
                        return Article.from_dict(article_data)

            return None
        except Exception as e:
            logger.error(
                f"Error retrieving article {pmid} from project {project_id}: {e}"
            )
            return None

    def get_articles(self, project_id: str) -> List[Article]:
        """Get all articles from the project's JSONL file.

        Args:
            project_id: Project identifier

        Returns:
            List of articles
        """
        project_dir = self.get_project_path(project_id)
        articles_file = os.path.join(project_dir, "articles.jsonl")

        if not os.path.exists(articles_file):
            return []

        articles = []
        try:
            with open(articles_file, "r") as f:
                for line in f:
                    try:
                        article_data = json.loads(line)
                        articles.append(Article.from_dict(article_data))
                    except json.JSONDecodeError:
                        logger.warning(f"Invalid JSON line in {articles_file}")
                        continue

            return articles
        except Exception as e:
            logger.error(
                f"Error retrieving articles from project {project_id}: {e}"
            )
            return []
