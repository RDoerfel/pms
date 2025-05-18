"""PubMed API client for fetching articles."""

import logging
import time
from typing import List, Dict, Optional, Any, Set, Tuple
from datetime import datetime
import xml.etree.ElementTree as ET
import urllib.request
import urllib.parse
import urllib.error
import json

from pms.api.rate_limiter import RateLimiter
from pms.models import Article, Author
from pms.config import config

logger = logging.getLogger(__name__)


class PubMedClient:
    """Client for interacting with the PubMed E-utilities API."""

    BASE_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"

    def __init__(self) -> None:
        """Initialize the PubMed client with configuration."""
        self.email = config.get("api", "email")
        self.tool = config.get("api", "tool") or "pms"
        self.api_key = config.get("api", "api_key")
        self.max_retries = config.get("api", "max_retries") or 3
        self.retry_delay = config.get("api", "retry_delay") or 5

        # Set up rate limiter
        requests_per_second = config.get("api", "requests_per_second") or 3
        if self.api_key:
            # With API key, we can make more requests
            requests_per_second = 10

        self.rate_limiter = RateLimiter(requests_per_second)

        if not self.email:
            logger.warning(
                "No email configured for PubMed API. "
                "This is required by NCBI. Set it with: "
                "`pms config set api email your.email@example.com`"
            )

    def _build_request_url(self, endpoint: str, params: Dict[str, Any]) -> str:
        """Build a request URL with the given parameters.

        Args:
            endpoint: API endpoint (e.g., 'esearch', 'efetch')
            params: Query parameters

        Returns:
            Complete URL for the request
        """
        # Add common parameters
        params["tool"] = self.tool
        params["email"] = self.email

        if self.api_key:
            params["api_key"] = self.api_key

        # Build the URL
        url = f"{self.BASE_URL}/{endpoint}.fcgi?{urllib.parse.urlencode(params)}"
        return url

    def _make_request(self, url: str) -> Optional[str]:
        """Make a request to the PubMed API with rate limiting and retries.

        Args:
            url: URL to request

        Returns:
            Response content or None if failed
        """
        retries = 0
        while retries <= self.max_retries:
            try:
                # Apply rate limiting
                self.rate_limiter.wait()

                logger.debug(f"Making request to {url}")
                with urllib.request.urlopen(url) as response:
                    content = response.read().decode("utf-8")
                    return content
            except urllib.error.HTTPError as e:
                if e.code == 429:  # Too Many Requests
                    wait_time = self.retry_delay * (2**retries)
                    logger.warning(f"Rate limit exceeded, waiting {wait_time}s")
                    time.sleep(wait_time)
                    retries += 1
                else:
                    logger.error(f"HTTP error: {e.code} - {e.reason}")
                    break
            except Exception as e:
                logger.error(f"Request error: {str(e)}")
                break

        return None

    def search(
        self, query: str, max_results: int = 100, date_range: Optional[Tuple[str, str]] = None, retmode: str = "json"
    ) -> List[str]:
        """Search PubMed for articles matching the query.

        Args:
            query: PubMed search query
            max_results: Maximum number of results to return
            date_range: Optional tuple of (start_date, end_date) in YYYY/MM/DD format
            retmode: Return mode, either "json" or "xml"

        Returns:
            List of PMIDs
        """
        params = {
            "db": "pubmed",
            "term": query,
            "retmax": max_results,
            "usehistory": "y",
            "retmode": retmode,
        }

        # Add date range if provided
        if date_range:
            start_date, end_date = date_range
            params["datetype"] = "pdat"  # Publication date
            params["mindate"] = start_date
            params["maxdate"] = end_date

        url = self._build_request_url("esearch", params)
        content = self._make_request(url)

        if not content:
            logger.error("Failed to search PubMed")
            return []

        try:
            if retmode == "json":
                # Parse JSON response
                data = json.loads(content)
                pmids = data.get("esearchresult", {}).get("idlist", [])
                return pmids
            else:
                # Parse XML response
                root = ET.fromstring(content)
                id_list = root.find("IdList")
                if id_list is not None:
                    return [id_elem.text for id_elem in id_list.findall("Id")]
                return []
        except Exception as e:
            logger.error(f"Error parsing search results: {str(e)}")
            return []

    def fetch_articles(self, pmids: List[str], batch_size: int = 100) -> List[Article]:
        """Fetch articles by their PMIDs.

        Args:
            pmids: List of PMIDs to fetch
            batch_size: Number of articles to fetch per request

        Returns:
            List of Article objects
        """
        if not pmids:
            return []

        articles = []
        # Process in batches to avoid large requests
        for i in range(0, len(pmids), batch_size):
            batch_pmids = pmids[i : i + batch_size]
            batch_articles = self._fetch_batch(batch_pmids)
            articles.extend(batch_articles)

            logger.info(f"Fetched {len(batch_articles)} articles (batch {i//batch_size + 1})")

        return articles

    def _fetch_batch(self, pmids: List[str]) -> List[Article]:
        """Fetch a batch of articles by their PMIDs.

        Args:
            pmids: List of PMIDs to fetch

        Returns:
            List of Article objects
        """
        params = {
            "db": "pubmed",
            "id": ",".join(pmids),
            "retmode": "xml",
            "rettype": "abstract",
        }

        url = self._build_request_url("efetch", params)
        content = self._make_request(url)

        if not content:
            logger.error("Failed to fetch articles")
            return []

        try:
            return self._parse_articles_xml(content)
        except Exception as e:
            logger.error(f"Error parsing article results: {str(e)}")
            return []

    def _parse_articles_xml(self, xml_content: str) -> List[Article]:
        """Parse XML content into Article objects.

        Args:
            xml_content: XML content from PubMed

        Returns:
            List of Article objects
        """
        root = ET.fromstring(xml_content)
        articles = []

        # Find all PubmedArticle elements
        for pubmed_article in root.findall(".//PubmedArticle"):
            try:
                # Extract PMID
                pmid_elem = pubmed_article.find(".//PMID")
                if pmid_elem is None or not pmid_elem.text:
                    continue
                pmid = pmid_elem.text

                # Extract article data
                article_elem = pubmed_article.find(".//Article")
                if article_elem is None:
                    continue

                # Extract title
                title_elem = article_elem.find("ArticleTitle")
                title = title_elem.text if title_elem is not None and title_elem.text else ""

                # Extract abstract
                abstract_elem = article_elem.find(".//AbstractText")
                abstract = abstract_elem.text if abstract_elem is not None and abstract_elem.text else ""

                # Handle multiple abstract sections
                abstract_sections = article_elem.findall(".//Abstract/AbstractText")
                if len(abstract_sections) > 1:
                    abstract_parts = []
                    for section in abstract_sections:
                        label = section.get("Label", "")
                        text = section.text or ""
                        if label:
                            abstract_parts.append(f"{label}: {text}")
                        else:
                            abstract_parts.append(text)
                    abstract = " ".join(abstract_parts)

                # Extract authors
                authors = []
                author_list = article_elem.find(".//AuthorList")
                if author_list is not None:
                    for author_elem in author_list.findall("Author"):
                        last_name_elem = author_elem.find("LastName")
                        fore_name_elem = author_elem.find("ForeName")
                        initials_elem = author_elem.find("Initials")

                        if last_name_elem is not None and last_name_elem.text:
                            # Extract affiliations
                            affiliations = []
                            for affiliation in author_elem.findall(".//Affiliation"):
                                if affiliation.text:
                                    affiliations.append(affiliation.text)

                            author = Author(
                                last_name=last_name_elem.text,
                                fore_name=fore_name_elem.text if fore_name_elem is not None else None,
                                initials=initials_elem.text if initials_elem is not None else None,
                                affiliations=affiliations,
                            )
                            authors.append(author)

                # Extract publication date
                pub_date = None
                pub_date_elem = pubmed_article.find(".//PubDate")
                if pub_date_elem is not None:
                    year_elem = pub_date_elem.find("Year")
                    month_elem = pub_date_elem.find("Month")
                    day_elem = pub_date_elem.find("Day")

                    year = year_elem.text if year_elem is not None and year_elem.text else None
                    month = month_elem.text if month_elem is not None and month_elem.text else "1"
                    day = day_elem.text if day_elem is not None and day_elem.text else "1"

                    if year:
                        # Convert month name to number if needed
                        try:
                            if month.isalpha():
                                datetime_obj = datetime.strptime(month, "%b")
                                month = str(datetime_obj.month)
                        except ValueError:
                            month = "1"

                        try:
                            pub_date_str = f"{year}-{month}-{day}"
                            pub_date = datetime.strptime(pub_date_str, "%Y-%m-%d")
                        except ValueError:
                            logger.warning(f"Invalid publication date for article {pmid}: {year}-{month}-{day}")

                # Extract DOI
                doi = None
                article_id_list = pubmed_article.find(".//ArticleIdList")
                if article_id_list is not None:
                    for id_elem in article_id_list.findall("ArticleId"):
                        if id_elem.get("IdType") == "doi" and id_elem.text:
                            doi = id_elem.text
                            break

                # Extract journal
                journal = None
                journal_elem = article_elem.find(".//Journal/Title")
                if journal_elem is not None and journal_elem.text:
                    journal = journal_elem.text

                # Extract keywords
                keywords = []
                keyword_list = pubmed_article.find(".//KeywordList")
                if keyword_list is not None:
                    for keyword_elem in keyword_list.findall("Keyword"):
                        if keyword_elem.text:
                            keywords.append(keyword_elem.text)

                # Create Article object
                article = Article(
                    pmid=pmid,
                    title=title,
                    abstract=abstract,
                    authors=authors,
                    keywords=keywords,
                    publication_date=pub_date,
                    doi=doi,
                    journal=journal,
                )

                articles.append(article)
            except Exception as e:
                logger.error(f"Error parsing article: {str(e)}")
                continue

        return articles
