"""
Feed handler module.
"""
import json
from dataclasses import dataclass, asdict
from typing import List, Optional

import feedparser
from newspaper import Article as FullText

from logger import _setup_logger

@dataclass
class FeedConfig:
    """Configuration for a single RSS feed."""
    url: str
    num_articles: int = 5
    name: Optional[str] = None


@dataclass
class Article:
    """
    Represents a single article from an RSS feed.
    The reason for having the two date attributes below rather than a single attribute is that 
    different feeds might have different data formats, which is annoying to sort through.
    published is also usually human readable, while published_parsed is for the script to deal with.
    """
    title: str
    link: str
    summary: str
    published: str
    author: Optional[str] = None
    text: Optional[str] = None

class FeedHandler:
    """Handles the parsing and management of multiple RSS feeds."""

    def __init__(self, json_path: str):
        """Initialize the FeedHandler with a path to the feeds configuration file.

        Args:
            json_path: Path to the JSON file containing feed configurations.
        """
        self.json_path = json_path
        self.feeds_data: List[FeedConfig] = []
        self.logger = _setup_logger("FeedHandler")
        self.logger.info("FeedHandler Initialised. ")
        self.load_feeds()


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
        articles = []

        try:
            parsed_feed = feedparser.parse(feed_config.url)

            # Check if we get a 200
            if hasattr(parsed_feed, 'status') and parsed_feed.status != 200:
                self.logger.warning(
                    "Feed %s returned status %d. Possible issue with the feed URL.", 
                    feed_config.url, parsed_feed.status)
                return articles

            # Check if feed format is funky
            if parsed_feed.bozo:
                self.logger.warning(
                    "Feed %s has possible invalid format: %s. Bozo flag set.", 
                    feed_config.url, parsed_feed.bozo_exception)
                return articles

            for entry in parsed_feed.entries[:feed_config.num_articles]:
                try:
                    # Fetch publication date if possible
                    published = entry.get("published", "No Date")

                    # Fetch article author if possible
                    author = entry.get("author", "Unknown Author")

                    # Fetch full article text
                    full_article = None
                    text = None
                    try:
                        full_article = FullText(entry.link)
                        full_article.download()
                        body = full_article.parse()
                        text = body.text

                    # pylint: disable=broad-exception-caught
                    except Exception as e:
                        self.logger.warning(
                            "Newspaper library Error parsing full article for URL %s: %s",
                             entry.link, e)
                        text = "Error parsing full article content."

                    article = Article(
                        title = entry.get("title", "No Title"),
                        link = entry.get("link", ""),
                        summary = entry.get("summary"),
                        published = published,
                        author = author,
                        text = text
                    )
                    articles.append(article)
                except AttributeError as e:
                    self.logger.warning(
                        "Error parsing entry in %s: %s", feed_config.url, e)
                    continue

            self.logger.info("Parsed %d articles from feed %s", len(articles), feed_config.url)

            return articles

        # pylint: disable=broad-exception-caught
        except Exception as e:
            self.logger.error("Error parsing feed %s: %s", feed_config.url, e)
            return []
