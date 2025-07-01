"""Database management for PMS."""

import os
import sqlite3
import logging
from typing import List, Optional, Set, Tuple
from pathlib import Path

from pms.config import config


logger = logging.getLogger(__name__)


class Database:
    """SQLite database for tracking articles and projects."""

    def __init__(self, db_path: Optional[str] = None) -> None:
        """Initialize the database.

        Args:
            db_path: Path to the database file. If None, uses the path from config.
        """
        self.db_path = os.path.expanduser(
            db_path
            or config.get("storage", "database_path")
            or "~/.local/share/pms/pms.db"
        )

        # Ensure the directory exists
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)

        self.conn = None
        self._initialize_db()

    def _initialize_db(self) -> None:
        """Initialize the database with required tables."""
        try:
            self.conn = sqlite3.connect(self.db_path)
            cursor = self.conn.cursor()

            # Create projects table
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS projects (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    description TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """
            )

            # Create articles table
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS articles (
                    pmid TEXT PRIMARY KEY,
                    doi TEXT,
                    title TEXT,
                    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """
            )

            # Create project_articles table (many-to-many)
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS project_articles (
                    project_id TEXT,
                    pmid TEXT,
                    PRIMARY KEY (project_id, pmid),
                    FOREIGN KEY (project_id) REFERENCES projects (id) ON DELETE CASCADE,
                    FOREIGN KEY (pmid) REFERENCES articles (pmid) ON DELETE CASCADE
                )
            """
            )

            # Create index for faster lookups
            cursor.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_project_articles_pmid ON project_articles (pmid)
            """
            )
            cursor.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_project_articles_project_id ON project_articles (project_id)
            """
            )
            cursor.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_articles_doi ON articles (doi)
            """
            )

            self.conn.commit()
            logger.debug("Database initialized successfully")
        except sqlite3.Error as e:
            logger.error(f"Database initialization error: {e}")
            if self.conn:
                self.conn.close()
                self.conn = None
            raise

    def close(self) -> None:
        """Close the database connection."""
        if self.conn:
            self.conn.close()
            self.conn = None

    def __enter__(self) -> "Database":
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Context manager exit."""
        self.close()

    def create_project(
        self, project_id: str, name: str, description: Optional[str] = None
    ) -> bool:
        """Create a new project.

        Args:
            project_id: Unique project identifier
            name: Project name
            description: Project description

        Returns:
            True if successful, False otherwise
        """
        try:
            cursor = self.conn.cursor()
            cursor.execute(
                "INSERT INTO projects (id, name, description) VALUES (?, ?, ?)",
                (project_id, name, description),
            )
            self.conn.commit()
            logger.info(f"Created project: {project_id} - {name}")
            return True
        except sqlite3.Error as e:
            logger.error(f"Error creating project {project_id}: {e}")
            self.conn.rollback()
            return False

    def get_project(self, project_id: str) -> Optional[Tuple[str, str, str]]:
        """Get project details.

        Args:
            project_id: Project identifier

        Returns:
            Project details as (id, name, description) or None if not found
        """
        try:
            cursor = self.conn.cursor()
            cursor.execute(
                "SELECT id, name, description FROM projects WHERE id = ?",
                (project_id,),
            )
            result = cursor.fetchone()
            return result if result else None
        except sqlite3.Error as e:
            logger.error(f"Error retrieving project {project_id}: {e}")
            return None

    def list_projects(self) -> List[Tuple[str, str, str]]:
        """List all projects.

        Returns:
            List of (id, name, description) tuples
        """
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT id, name, description FROM projects")
            return cursor.fetchall()
        except sqlite3.Error as e:
            logger.error(f"Error listing projects: {e}")
            return []

    def add_article(
        self, pmid: str, doi: Optional[str] = None, title: Optional[str] = None
    ) -> bool:
        """Add an article to the database.

        Args:
            pmid: PubMed ID
            doi: Digital Object Identifier
            title: Article title

        Returns:
            True if successful, False otherwise
        """
        try:
            cursor = self.conn.cursor()
            cursor.execute(
                "INSERT OR REPLACE INTO articles (pmid, doi, title) VALUES (?, ?, ?)",
                (pmid, doi, title),
            )
            self.conn.commit()
            logger.debug(f"Added article: {pmid}")
            return True
        except sqlite3.Error as e:
            logger.error(f"Error adding article {pmid}: {e}")
            self.conn.rollback()
            return False

    def link_article_to_project(self, project_id: str, pmid: str) -> bool:
        """Link an article to a project.

        Args:
            project_id: Project identifier
            pmid: PubMed ID

        Returns:
            True if successful, False otherwise
        """
        try:
            cursor = self.conn.cursor()
            cursor.execute(
                "INSERT OR IGNORE INTO project_articles (project_id, pmid) VALUES (?, ?)",
                (project_id, pmid),
            )
            self.conn.commit()
            return True
        except sqlite3.Error as e:
            logger.error(
                f"Error linking article {pmid} to project {project_id}: {e}"
            )
            self.conn.rollback()
            return False

    def get_project_articles(self, project_id: str) -> List[str]:
        """Get all article PMIDs for a project.

        Args:
            project_id: Project identifier

        Returns:
            List of PMIDs
        """
        try:
            cursor = self.conn.cursor()
            cursor.execute(
                "SELECT pmid FROM project_articles WHERE project_id = ?",
                (project_id,),
            )
            return [row[0] for row in cursor.fetchall()]
        except sqlite3.Error as e:
            logger.error(
                f"Error retrieving articles for project {project_id}: {e}"
            )
            return []

    def filter_new_pmids(self, project_id: str, pmids: List[str]) -> List[str]:
        """Filter out PMIDs that are already in the project.

        Args:
            project_id: Project identifier
            pmids: List of PMIDs to check

        Returns:
            List of PMIDs that are not yet in the project
        """
        if not pmids:
            return []

        try:
            cursor = self.conn.cursor()
            # Get existing PMIDs for this project
            cursor.execute(
                "SELECT pmid FROM project_articles WHERE project_id = ? AND pmid IN ({})".format(
                    ",".join(["?"] * len(pmids))
                ),
                [project_id] + pmids,
            )
            existing_pmids = {row[0] for row in cursor.fetchall()}

            # Return only new PMIDs
            return [pmid for pmid in pmids if pmid not in existing_pmids]
        except sqlite3.Error as e:
            logger.error(
                f"Error filtering PMIDs for project {project_id}: {e}"
            )
            return []

    def count_project_articles(self, project_id: str) -> int:
        """Count the number of articles in a project.

        Args:
            project_id: Project identifier

        Returns:
            Number of articles
        """
        try:
            cursor = self.conn.cursor()
            cursor.execute(
                "SELECT COUNT(*) FROM project_articles WHERE project_id = ?",
                (project_id,),
            )
            return cursor.fetchone()[0]
        except sqlite3.Error as e:
            logger.error(
                f"Error counting articles for project {project_id}: {e}"
            )
            return 0
