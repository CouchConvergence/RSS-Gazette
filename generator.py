"""
Document generation module.
"""
from datetime import date
from typing import List
from ebooklib import epub

from logger import _setup_logger
from feedhandler import FeedConfig, FeedHandler


class EpubGenerator:
    """Generates EPUB files from a list of articles."""

    def __init__(self):
        """Initialize the EpubGenerator with logging."""
        self.logger = _setup_logger("EpubGenerator")
        self.logger.info("EpubGenerator Initialized. ")

    def generate_epub(self,
                    feeds: List[FeedConfig],
                    handler: FeedHandler,
                    output_file: str,
                    article_type: str) -> None:
        """
        Generate an EPUB file from a list of articles.

        Args:
            feeds: List of FeedConfig objects.
            handler: A FeedHandler instance to manage parsing.
            output_file: Path to the output EPUB file.
            article_type: Decides whether to generate using full articles, or summaries.
        """
        if not feeds:
            self.logger.warning(
                "No feeds provided. EPUB file will not be generated.")
            return

        if not output_file:
            self.logger.error("Output file path is not provided.")
            return

        self.logger.info("Starting EPUB generation...")

        # Create a new EPUB book
        book = epub.EpubBook()
        book.set_title(f"{date.today().isoformat()} Newspaper")
        book.set_language("en")
        book.add_author("Epistle")

        # Define CSS styles
        style = """
        @namespace html url(http://www.w3.org/1999/xhtml);
        body { line-height: 1.6; }
        h1, h2 { margin-bottom: 0.5em; }
        a { text-decoration: underline; }
        hr { border: none; }
        """
        nav_css = epub.EpubItem(uid="style_nav", file_name="style/nav.css",
                                media_type="text/css", content=style)
        book.add_item(nav_css)

        # List to store chapters and articles
        chapters = []
        toc = []

        for feed in feeds:
            self.logger.info(
                "Processing feed '%s' with URL: %s", feed.name, feed.url)

            # Parse feed
            try:
                articles = handler.parse_feed(feed)
            # pylint: disable=broad-exception-caught
            except Exception as e:
                self.logger.error(
                    "Failed to parse feed '%s': %s", feed.name, e)
                continue

            if not articles:
                self.logger.warning(
                    "No articles found in feed '%s'. Skipping...", feed.name)
                continue

            # Create a single chapter for the entire feed
            feed_title = feed.name or f"Feed_{feed.url}"
            feed_content = f"<h1>{feed.name or 'Unnamed Feed'}</h1>"
            feed_chapter = epub.EpubHtml(
                title=feed_title,
                file_name=f"{feed_title.replace(' ', '_')}.xhtml",
                content=feed_content,
            )

            # List to store article links for the TOC
            feed_toc = []

            for article in articles:
                if not article.title:
                    self.logger.warning(
                        "Skipping article with missing title in feed '%s'.", feed.name)
                    continue

                self.logger.info(
                    "Adding article '%s' from feed '%s'", article.title, feed.name)
                article_title = article.title or "Unnamed Article"
                article_id = article_title.replace(' ', '_')
                article_content = f"""
                <h2 id="{article_id}">{article_title}</h2>
                <p><strong>Author:</strong> {article.author or 'Unknown Author'}</p>
                <p><strong>Published:</strong> {article.published or 'Unknown Date'}</p>
                <p><a href="{article.link}">Read original article</a></p>
                <hr>
                <p>
                    {article.text if article_type == "Full" else (
                        article.summary or 'No content available.'
                        )}
                </p>
                """
                feed_chapter.content += article_content

                # Add article to TOC only if article_type is "Full"
                if article_type == "Full":
                    article_link = epub.Link(
                        href=f"{feed_title.replace(' ', '_')}.xhtml#{article_id}",
                        title=article_title,
                        uid=article_id
                    )
                    feed_toc.append(article_link)

            # Add the feed chapter to the book
            book.add_item(feed_chapter)
            chapters.append(feed_chapter)

            # Add the feed and its articles to the TOC
            if feed_toc:
                toc.append((epub.Section(feed_title), feed_toc))
            else:
                toc.append(epub.Section(feed_title))

        # Add navigation and spine
        self.logger.info("Adding navigation and styling...")

        try:
            book.toc = toc
            book.add_item(epub.EpubNcx())
            book.add_item(epub.EpubNav())

            book.spine = ["nav"] + chapters
        # pylint: disable=broad-exception-caught
        except Exception as e:
            self.logger.error(
                "Failed to configure navigation and styling: %s", e)
            return

        # Write the book to a file
        try:
            epub.write_epub(output_file, book)
            self.logger.info(
                "EPUB file successfully saved to %s.", output_file)
        # pylint: disable=broad-exception-caught
        except Exception as e:
            self.logger.error("Failed to save EPUB file: %s", e)

        self.logger.info("EPUB generation completed successfully.")
