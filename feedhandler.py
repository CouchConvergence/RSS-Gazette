"""
Feed handler module.

Classes: 
    FeedConfig: A dataclass to store the information for each feed. 
    FeedHanndler: A class to define the main operations we'd want to perform on our feeds.
    Such as adding, removing, editing, parsing, and so on.
"""
import os
import json
from dataclasses import dataclass, asdict

import feedparser
from newspaper import Article as FullText
from logger import _setup_logger

@dataclass
class FeedConfig:
    """Configuration for a single RSS feed."""
    url: str
    name: str | None
    num_articles: int = 5

@dataclass
class Article:
    """Configuration for a single article."""
    title: str
    link: str
    summary: str
    published: str
    author: str | None
    text: str | None # Full text obtained by Newspaper4k

class FeedHandler:
    """
    The class responsible for handling and managing RSS feeds.

    This class provides the methods to load, save, add, remove, and update feed configurations.
    It also includes methods to parse RSS feeds and retrieve articles from them.

    Attributes:
        json_path (str): The path to the JSON file that stores feed configurations.
        feeds_data (list[FeedConfig]): A list of feed configurations.
        logger (Logger): A logger instance to keep track of what's happening.

    Methods:
        __init__(json_path: str):
            Initializes the FeedHandler with the provided JSON configuration file path.
        
        load_feeds() -> None:
            Loads and validates feed configurations from the JSON file.
            If the file doesn't exist, it creates an empty file and logs the necessary information.
        
        save_feeds() -> None:
            Saves the current feed configurations back to the JSON file.
        
        add_feed(feed_config: FeedConfig) -> None:
            Adds a new feed to the internal list and updates the JSON file.
        
        remove_feed(url: str) -> None:
            Removes a feed from the list based on the provided URL and updates the JSON file.
        
        update_feed(url: str, feed_config: FeedConfig) -> None:
            Updates an existing feed by URL and saves the changes to the JSON file.
        
        parse_feed(feed_config: FeedConfig) -> list[Article]:
            Parses an RSS feed using the provided feed configuration and returns a list of articles.
            Handles potential feed parsing errors and logs warnings or errors accordingly.
"""
    def __init__(self, json_path: str):
        """Initialize the FeedHandler with a path to the feeds configuration file.

        Args:
            json_path: Path to the JSON file containing feed configurations.
        """
        self.json_path = json_path
        self.feeds_data: list[FeedConfig] = []
        self.logger = _setup_logger("FeedHandler")
        self.logger.info("FeedHandler Initialised. ")
        self.load_feeds()

    def load_feeds(self) -> None:
        """Load and validate RSS feed metadata from the JSON file."""

        # Ensure the directory exists
        directory = os.path.dirname(self.json_path)
        if not os.path.exists(directory):
            os.makedirs(directory)
            self.logger.info("Created directory: %s", directory)

        # Ensure the JSON file exists
        if not os.path.isfile(self.json_path):
            with open(self.json_path, 'w', encoding='utf-8') as file:
                json.dump([], file, ensure_ascii=False, indent=4)
            self.logger.info("Created empty JSON file: %s", self.json_path)
            self.feeds_data = []
            return

        try:
            with open(self.json_path, 'r', encoding='utf-8') as file:
                raw_data = json.load(file)
                self.feeds_data = [
                    FeedConfig(**feed_data) for feed_data in raw_data
                ]
            self.logger.info("Successfully loaded %d feeds",
                            len(self.feeds_data))
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
        else:
            self.logger.info("No feed with specified URL Nothing was updated")
        self.save_feeds()

    def parse_feed(self, feed_config: FeedConfig) -> list[Article]:
        """Parse an RSS feed and return a list of articles.

        Args:
            feed_config: Configuration for the feed to parse.

        Returns:
            List of parsed articles.
        """

        articles = []

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
                    title=entry.get("title", "No Title"),
                    link=entry.get("link", ""),
                    summary=entry.get("summary"),
                    published=published,
                    author=author,
                    text=text
                )
                articles.append(article)
            except AttributeError as e:
                self.logger.warning(
                    "Error parsing entry in %s: %s", feed_config.url, e)
                continue

        self.logger.info("Parsed %d articles from feed %s",
                        len(articles), feed_config.url)

        return articles
