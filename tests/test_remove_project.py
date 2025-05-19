"""Tests for project removal functionality."""

import os
import pytest
import tempfile
import uuid
import shutil
import sqlite3
import logging

from pms.project.manager import ProjectManager
from pms.storage.database import Database
from pms.storage.jsonl import JSONLStorage

# Set up logging for tests
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


class TestProjectRemoval:
    """Test cases for project removal functionality."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Set up testing environment."""
        # Create temporary directory for all test files
        self.temp_dir = tempfile.mkdtemp()
        logger.debug(f"Created temp directory: {self.temp_dir}")

        # Create paths for temporary database and data directory
        self.db_path = os.path.join(self.temp_dir, "test.db")
        self.data_dir = os.path.join(self.temp_dir, "data")
        os.makedirs(self.data_dir, exist_ok=True)
        logger.debug(f"Database path: {self.db_path}")
        logger.debug(f"Data directory: {self.data_dir}")

        yield

        # Clean up
        if hasattr(self, "db") and self.db.conn:
            self.db.close()

        logger.debug(f"Removing temp directory: {self.temp_dir}")
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_direct_database_operations(self):
        """Test direct database operations to verify the database works correctly."""
        # Create database directly
        self.db = Database(self.db_path)

        # Create a project directly in the database
        project_id = "test-direct-db"
        project_name = "Test Direct DB"
        result = self.db.create_project(project_id, project_name, "Test description")
        assert result is True, "Failed to create project directly in database"

        # Verify project exists
        project = self.db.get_project(project_id)
        assert project is not None, "Project not found after direct creation"
        assert project[0] == project_id, "Project ID mismatch"
        assert project[1] == project_name, "Project name mismatch"

        logger.debug(f"Successfully created and retrieved project: {project}")

        # List all projects
        projects = self.db.list_projects()
        logger.debug(f"All projects in database: {projects}")
        assert len(projects) > 0, "No projects found in database"

        # Close the database connection
        self.db.close()

    def test_remove_project(self):
        """Test removing a project using ProjectManager."""
        # Create database and storage
        self.db = Database(self.db_path)
        storage = JSONLStorage(self.data_dir)

        # Create a project directly in the database for simplicity
        project_id = "test-removal"
        project_name = "Test Project for Removal"
        self.db.create_project(project_id, project_name, "Test description")

        # Verify project exists in database
        project = self.db.get_project(project_id)
        assert project is not None, "Project not found after direct creation"
        assert project[1] == project_name, "Project name mismatch"

        # Create project directory
        project_dir = os.path.join(self.data_dir, project_id)
        os.makedirs(project_dir, exist_ok=True)

        # Create a dummy file in the project directory
        with open(os.path.join(project_dir, "config.json"), "w") as f:
            f.write("{}")

        # Verify directory exists
        assert os.path.exists(project_dir), "Project directory was not created"

        # Now create a project manager and use it to remove the project
        manager = ProjectManager()
        manager.db = self.db  # Use our test database
        manager.storage = storage  # Use our test storage

        # Remove the project
        success = manager.remove_project(project_id)
        assert success is True, "Failed to remove project"

        # Verify project no longer exists in database
        project = self.db.get_project(project_id)
        assert project is None, "Project still exists in database after removal"

        # Verify project directory was removed
        assert not os.path.exists(project_dir), "Project directory still exists after removal"

        # Clean up
        manager.close()

    def test_remove_nonexistent_project(self):
        """Test removing a project that doesn't exist."""
        # Create database and storage
        self.db = Database(self.db_path)
        storage = JSONLStorage(self.data_dir)

        # Create project manager with our test database and storage
        manager = ProjectManager()
        manager.db = self.db
        manager.storage = storage

        # Try to remove a non-existent project
        non_existent_id = "non-existent-id"
        success = manager.remove_project(non_existent_id)
        assert success is False, "Removing non-existent project should return False"

        # Clean up
        manager.close()
