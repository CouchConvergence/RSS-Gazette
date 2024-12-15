"""
This file handles the parsing of RSS feeds, manages feed configurations,
and collects articles from various parsed feeds.

It includes the following components:
- FeedConfig: Defines the configuration for each feed.
- Article: Represents a single article parsed from an RSS feed.
- FeedHandler: Handles the management of multiple RSS feeds, including loading
  configurations, parsing feeds, and collecting articles.
"""
import json
import logging
from datetime import datetime
from dataclasses import dataclass, asdict
from typing import List, Optional

import feedparser


@dataclass
class FeedConfig:
    """Configuration for a single RSS feed."""
    url: str
    num_articles: int = 5
    category: Optional[str] = None
    name: Optional[str] = None


@dataclass
class Article:
    """
    Represents a single article from an RSS feed.
    The reason for having the two date attributes below rather than a single attribute is that 
    different feeds might have different data formats, which is annoying to sort through.
    published is also usually human readable, while publishedparsed is for the script to deal with.
    """
    title: str
    link: str
    published: str
    published_parsed: Optional[datetime] = None


class FeedHandler:
    """Handles the parsing and management of multiple RSS feeds."""

    def __init__(self, json_path: str):
        """Initialize the FeedHandler with a path to the feeds configuration file.

        Args:
            json_path: Path to the JSON file containing feed configurations.
        """
        self.json_path = json_path
        self.feeds_data: List[FeedConfig] = []
        self.logger = self._setup_logger()
        self.load_feeds()

    @staticmethod
    def _setup_logger() -> logging.Logger:
        """Set up logging configuration."""
        logger = logging.getLogger('FeedHandler')
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)
        return logger

    def load_feeds(self) -> None:
        """Load and validate RSS feed metadata from the JSON file."""
        try:
            with open(self.json_path, 'r', encoding='utf-8') as file:
                raw_data = json.load(file)
                self.feeds_data = [
                    FeedConfig(**feed_data) for feed_data in raw_data
                ]
            self.logger.info("Successfully loaded %d feeds",
                             len(self.feeds_data))
        except FileNotFoundError:
            self.logger.error(
                "Feed configuration file not found: %s", self.json_path)
            raise
        except json.JSONDecodeError as e:
            self.logger.error("Invalid JSON in configuration file: %s", e)
            raise
        except TypeError as e:
            self.logger.error("Invalid feed configuration format: %s", e)
            raise

    def save_feeds(self) -> None:
        """Save the current feed configurations to the JSON file."""
        try:
            with open(self.json_path, 'w', encoding='utf-8') as file:
                json.dump([asdict(feed)
                          for feed in self.feeds_data], file, indent=4)
            self.logger.info("Successfully saved %d feeds",
                             len(self.feeds_data))
        except IOError as e:
            self.logger.error("Failed to save feeds: %s", e)
            raise

    def add_feed(self, feed_config: FeedConfig) -> None:
        """Add a new feed configuration."""
        self.feeds_data.append(feed_config)
        self.save_feeds()

    def remove_feed(self, url: str) -> None:
        """Remove a feed configuration by URL."""
        self.feeds_data = [feed for feed in self.feeds_data if feed.url != url]
        self.save_feeds()

    def update_feed(self, url: str, feed_config: FeedConfig) -> None:
        """Update an existing feed configuration by URL."""
        for i, feed in enumerate(self.feeds_data):
            if feed.url == url:
                self.feeds_data[i] = feed_config
                break
        self.save_feeds()

    def parse_feed(self, feed_config: FeedConfig) -> List[Article]:
        """Parse an RSS feed and return a list of articles.

        Args:
            feed_config: Configuration for the feed to parse.

        Returns:
            List of parsed articles.
        """
        try:
            parsed_feed = feedparser.parse(feed_config.url)

            if hasattr(parsed_feed, 'status') and parsed_feed.status != 200:
                self.logger.warning(
                    "Feed %s returned status %d", feed_config.url, parsed_feed.status)
                return []

            if parsed_feed.bozo:
                self.logger.warning(
                    "Feed %s has invalid format: %s", feed_config.url, parsed_feed.bozo_exception)
                return []

            articles = []
            for entry in parsed_feed.entries[:feed_config.num_articles]:
                try:
                    published_parsed = None
                    if 'published_parsed' in entry:
                        published_parsed = datetime(
                            *entry.published_parsed[:6])

                    article = Article(
                        title=entry.get("title", "No Title"),
                        link=entry.get("link", ""),
                        published=entry.get("published", "No Date"),
                        published_parsed=published_parsed
                    )
                    articles.append(article)
                except AttributeError as e:
                    self.logger.warning(
                        "Error parsing entry in %s: %s", feed_config.url, e)
                    continue

            self.logger.info("Successfully parsed %d articles from %s", len(
                articles), feed_config.url)
            return articles

        # pylint: disable=broad-exception-caught
        except Exception as e:
            self.logger.error("Error parsing feed %s: %s", feed_config.url, e)
            return []

    def collect_articles(self, sort_by_date: bool = True) -> List[Article]:
        """Collect and optionally sort articles from all configured feeds.

        Args:
            sort_by_date: Whether to sort articles by publication date.

        Returns:
            List of articles from all feeds.
        """
        all_articles = []

        for feed_config in self.feeds_data:
            articles = self.parse_feed(feed_config)
            all_articles.extend(articles)

        if sort_by_date and all_articles:
            all_articles.sort(
                key=lambda x: x.published_parsed or datetime.min,
                reverse=True
            )

        self.logger.info("Collected total of %d articles", len(all_articles))
        return all_articles
