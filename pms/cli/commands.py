"""Command-line interface for PMS."""

import argparse
import sys
import logging
import json
from typing import List, Optional, Dict, Any
import os
from datetime import datetime

from pms.config import config
from pms.utils import setup_logging
from pms.project import ProjectManager
from pms import __version__

logger = logging.getLogger(__name__)


def create_project(args: argparse.Namespace) -> int:
    """Create a new project.

    Args:
        args: Command-line arguments

    Returns:
        Exit code
    """
    setup_logging(args.log_level)

    try:
        with ProjectManager() as manager:
            project_id = manager.create_project(args.name, args.description, args.project_id)
            print(f"Created project '{args.name}' with ID: {project_id}")
        return 0
    except Exception as e:
        logger.error(f"Failed to create project: {str(e)}")
        return 1


def list_projects(args: argparse.Namespace) -> int:
    """List all projects.

    Args:
        args: Command-line arguments

    Returns:
        Exit code
    """
    setup_logging(args.log_level)

    try:
        with ProjectManager() as manager:
            projects = manager.list_projects()

            if not projects:
                print("No projects found.")
                return 0

            print(f"Found {len(projects)} projects:")
            for project_id, name, description in projects:
                desc = description or ""
                if len(desc) > 50:
                    desc = desc[:47] + "..."
                print(f"  {project_id}: {name} - {desc}")
        return 0
    except Exception as e:
        logger.error(f"Failed to list projects: {str(e)}")
        return 1


def search(args: argparse.Namespace) -> int:
    """Search PubMed and store articles.

    Args:
        args: Command-line arguments

    Returns:
        Exit code
    """
    setup_logging(args.log_level)

    try:
        # Parse date range if provided
        date_range = None
        if args.date_range:
            start_date, end_date = args.date_range.split(":")
            date_range = (start_date, end_date)

        with ProjectManager() as manager:
            # Check if project exists
            project = manager.get_project(args.project_id)
            if not project:
                print(f"Project not found: {args.project_id}")
                return 1

            print(f"Searching PubMed for project '{project[1]}' ({args.project_id})")
            print(f"Query: {args.query}")
            print(f"Maximum results: {args.max_results}")
            if date_range:
                print(f"Date range: {date_range[0]} to {date_range[1]}")

            # Search and store
            results = manager.search_and_store(
                args.project_id,
                args.query,
                max_results=args.max_results,
                date_range=date_range,
                batch_size=args.batch_size,
            )

            # Display results
            print("\nSearch results:")
            print(f"  Found: {results['found']} articles")
            print(f"  New: {results['new']} articles")
            print(f"  Fetched: {results['fetched']} articles")
            print(f"  Stored: {results['stored']} articles")

            # Display total articles in project
            total = manager.get_article_count(args.project_id)
            print(f"\nTotal articles in project: {total}")

        return 0
    except Exception as e:
        logger.error(f"Search failed: {str(e)}")
        return 1


def count(args: argparse.Namespace) -> int:
    """Count articles in a project.

    Args:
        args: Command-line arguments

    Returns:
        Exit code
    """
    setup_logging(args.log_level)

    try:
        with ProjectManager() as manager:
            # Check if project exists
            project = manager.get_project(args.project_id)
            if not project:
                print(f"Project not found: {args.project_id}")
                return 1

            count = manager.get_article_count(args.project_id)
            print(f"Project '{project[1]}' ({args.project_id}) has {count} articles.")
        return 0
    except Exception as e:
        logger.error(f"Failed to count articles: {str(e)}")
        return 1


def export(args: argparse.Namespace) -> int:
    """Export articles from a project.

    Args:
        args: Command-line arguments

    Returns:
        Exit code
    """
    setup_logging(args.log_level)

    try:
        with ProjectManager() as manager:
            # Check if project exists
            project = manager.get_project(args.project_id)
            if not project:
                print(f"Project not found: {args.project_id}")
                return 1

            articles = manager.get_articles(args.project_id)
            if not articles:
                print(f"No articles found in project '{project[1]}' ({args.project_id})")
                return 0

            print(f"Exporting {len(articles)} articles from project '{project[1]}' ({args.project_id})")

            # Export to file
            with open(args.output, "w") as f:
                if args.format == "jsonl":
                    # JSONL format (one JSON object per line)
                    for article in articles:
                        json.dump(article.to_dict(), f)
                        f.write("\n")
                elif args.format == "json":
                    # JSON format (array of objects)
                    json.dump([article.to_dict() for article in articles], f, indent=2)
                elif args.format == "csv":
                    # CSV format
                    import csv

                    writer = csv.writer(f)
                    # Write header
                    writer.writerow(
                        ["pmid", "title", "abstract", "doi", "publication_date", "journal", "authors", "keywords"]
                    )
                    # Write data
                    for article in articles:
                        writer.writerow(
                            [
                                article.pmid,
                                article.title,
                                article.abstract,
                                article.doi or "",
                                article.publication_date.isoformat() if article.publication_date else "",
                                article.journal or "",
                                "; ".join([f"{a.last_name}, {a.fore_name or ''}" for a in article.authors]),
                                "; ".join(article.keywords),
                            ]
                        )

            print(f"Exported to {args.output}")
        return 0
    except Exception as e:
        logger.error(f"Export failed: {str(e)}")
        return 1


def remove(args: argparse.Namespace) -> int:
    """Remove a project.

    Args:
        args: Command-line arguments

    Returns:
        Exit code
    """
    setup_logging(args.log_level)

    try:
        if not args.force:
            # Ask for confirmation
            project_id = args.project_id
            confirm = input(f"Are you sure you want to remove project {project_id}? This cannot be undone. (y/N): ")
            if confirm.lower() != "y":
                print("Operation cancelled.")
                return 0

        with ProjectManager() as manager:
            # Check if project exists
            project = manager.get_project(args.project_id)
            if not project:
                print(f"Project not found: {args.project_id}")
                return 1

            success = manager.remove_project(args.project_id)
            if success:
                print(f"Project '{project[1]}' ({args.project_id}) has been removed.")
            else:
                print(f"Failed to remove project {args.project_id}.")
                return 1
        return 0
    except Exception as e:
        logger.error(f"Failed to remove project: {str(e)}")
        return 1


def configure(args: argparse.Namespace) -> int:
    """Configure PMS settings.

    Args:
        args: Command-line arguments

    Returns:
        Exit code
    """
    setup_logging(args.log_level)

    try:
        if args.action == "get":
            # Get a configuration value
            value = config.get(args.section, args.key)
            print(f"{args.section}.{args.key} = {value}")
        elif args.action == "set":
            # Set a configuration value
            config.set(args.section, args.key, args.value)
            config.save()
            print(f"Set {args.section}.{args.key} = {args.value}")
        elif args.action == "list":
            # List all configuration values
            print("Current configuration:")
            for section, values in config.config.items():
                print(f"[{section}]")
                for key, value in values.items():
                    print(f"  {key} = {value}")
        return 0
    except Exception as e:
        logger.error(f"Configuration failed: {str(e)}")
        return 1


def main(args: Optional[List[str]] = None) -> int:
    """Main entry point for the CLI.

    Args:
        args: Command-line arguments

    Returns:
        Exit code
    """
    parser = argparse.ArgumentParser(description="PMS - PubMed Search Tool")
    parser.add_argument("--version", action="version", version=f"PMS {__version__}")
    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        default=None,
        help="Set the logging level",
    )

    # Create subparsers for commands
    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    subparsers.required = True

    # Create project command
    create_parser = subparsers.add_parser("create", help="Create a new project")
    create_parser.add_argument("name", help="Project name")
    create_parser.add_argument("--description", help="Project description")
    create_parser.add_argument("--project-id", help="Custom project ID (optional)")
    create_parser.set_defaults(func=create_project)

    # List projects command
    list_parser = subparsers.add_parser("list", help="List all projects")
    list_parser.set_defaults(func=list_projects)

    # Search command
    search_parser = subparsers.add_parser("search", help="Search PubMed and store articles")
    search_parser.add_argument("project_id", help="Project ID")
    search_parser.add_argument("query", help="PubMed search query")
    search_parser.add_argument("--max-results", type=int, default=100, help="Maximum number of results (default: 100)")
    search_parser.add_argument(
        "--date-range",
        help="Date range in format 'YYYY/MM/DD:YYYY/MM/DD'",
    )
    search_parser.add_argument(
        "--batch-size", type=int, default=100, help="Batch size for fetching articles (default: 100)"
    )
    search_parser.set_defaults(func=search)

    # Count command
    count_parser = subparsers.add_parser("count", help="Count articles in a project")
    count_parser.add_argument("project_id", help="Project ID")
    count_parser.set_defaults(func=count)

    # Export command
    export_parser = subparsers.add_parser("export", help="Export articles from a project")
    export_parser.add_argument("project_id", help="Project ID")
    export_parser.add_argument("output", help="Output file path")
    export_parser.add_argument(
        "--format",
        choices=["jsonl", "json", "csv"],
        default="jsonl",
        help="Output format (default: jsonl)",
    )
    export_parser.set_defaults(func=export)

    # Configure command
    config_parser = subparsers.add_parser("config", help="Configure PMS settings")
    config_parser.add_argument("action", choices=["get", "set", "list"], help="Configuration action")
    config_parser.add_argument("section", nargs="?", help="Configuration section (e.g., 'api', 'storage')")
    config_parser.add_argument("key", nargs="?", help="Configuration key")
    config_parser.add_argument("value", nargs="?", help="Configuration value (for 'set' action)")
    config_parser.set_defaults(func=configure)

    # Remove command
    remove_parser = subparsers.add_parser("remove", help="Remove a project")
    remove_parser.add_argument("project_id", help="Project ID")
    remove_parser.add_argument("--force", action="store_true", help="Remove without confirmation prompt")
    remove_parser.set_defaults(func=remove)

    # Parse arguments
    parsed_args = parser.parse_args(args)

    # Initialize configuration directories
    config.ensure_directories()

    # Run the command
    return parsed_args.func(parsed_args)


if __name__ == "__main__":
    sys.exit(main())
