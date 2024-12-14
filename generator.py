"""
Handles the generation of EPUB files from a collection of articles.
"""

import os
from typing import List, Optional
from datetime import datetime
import logging
from dataclasses import dataclass

from ebooklib import epub

from feedhandler import Article


@dataclass
class EpubConfig:
    """Configuration for EPUB generation."""
    title: str
    author: str = "RSS Feed Collection"
    language: str = "en"
    description: Optional[str] = None
    cover_path: Optional[str] = None
    css_path: Optional[str] = None
    output_dir: str = "output"


class EpubGenerator:
    """Handles the generation of EPUB files from articles."""

    ENGLISH_CSS = """
        body { margin: 5%; text-align: left; }
        h1 { text-align: center; }
        h2 { text-align: left; margin-bottom: 0; }
        h3 { text-align: left; margin-bottom: 0; }
        h4 { text-align: left; margin-bottom: 0; }
        .article-meta { margin-top: 0; font-size: small; color: gray; }
        .category { font-style: italic; }
    """
    ARABIC_CSS = """
        body { margin: 5%; text-align: right; }
        h1 { text-align: center; }
        h2 { text-align: right; margin-bottom: 0; }
        h3 { text-align: right; margin-bottom: 0; }
        h4 { text-align: right; margin-bottom: 0; }
        .article-meta { margin-top: 0; font-size: small; color: gray; }
        .category { font-style: italic; }
    """

    def __init__(self, config: EpubConfig):
        """Initialize the EPUB generator with configuration.

        Args:
            config: Configuration for EPUB generation
        """
        self.config = config
        self.logger = self._setup_logger()
        self._setup_output_directory()

    def _setup_logger(self) -> logging.Logger:
        """Set up logging configuration."""
        logger = logging.getLogger('Generator')

        if not logger.handlers:
            # Log file
            file_handler = logging.FileHandler('logs/generator.log')
            file_formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            file_handler.setFormatter(file_formatter)
            logger.addHandler(file_handler)
            # Console log
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(file_formatter)
            logger.addHandler(console_handler)

            logger.setLevel(logging.INFO)
        return logger

    def _setup_output_directory(self) -> None:
        """Create output directory if it doesn't exist."""
        os.makedirs(self.config.output_dir, exist_ok=True)

    def _create_epub_book(self) -> epub.EpubBook:
        """Create and initialize a new EPUB book."""
        book = epub.EpubBook()
        book.set_title(self.config.title)
        book.set_language(self.config.language)
        book.add_author(self.config.author)

        if self.config.description:
            book.add_metadata('DC', 'description', self.config.description)

        if self.config.cover_path and os.path.exists(self.config.cover_path):
            with open(self.config.cover_path, 'rb') as cover_file:
                book.set_cover("cover.jpg", cover_file.read())

        # Add CSS
        css_content = self.ARABIC_CSS if self.config.language == 'ar' else self.ENGLISH_CSS
        if self.config.css_path and os.path.exists(self.config.css_path):
            with open(self.config.css_path, 'r', encoding="utf-8") as css_file:
                css_custom = css_file.read()
                css_content += css_custom

        nav_css = epub.EpubItem(
            uid="style_nav",
            file_name="style/nav.css",
            media_type="text/css",
            content=css_content
        )
        book.add_item(nav_css)

        return book

    def _create_chapter(self, article: Article, index: int) -> epub.EpubHtml:
        """Create an EPUB chapter from an article."""
        chapter = epub.EpubHtml(
            title=article.title,
            file_name=f'chapter_{index}.xhtml',
            lang=self.config.language
        )

        # Create HTML content with metadata
        content = f"""
            <h2>{article.title}</h2>
            <div class="article-meta">
                <p>From: {article.source_name} |
                   Published: {article.published} |
                   Category: <span class="category">{article.category}</span></p>
                <p>Original: <a href="{article.link}">{article.link}</a></p>
            </div>
            <div class="article-content">
                {article.summary}
            </div>
        """

        chapter.content = content
        chapter.add_item(epub.EpubItem(
            uid="style_nav", file_name="style/nav.css", media_type="text/css", content=self.ENGLISH_CSS))

        return chapter

    def generate_epub(self, articles: List[Article], filename: Optional[str] = None) -> str:
        """Generate an EPUB file from a list of articles.

        Args:
            articles: List of articles to include in the EPUB
            filename: Optional custom filename (without extension)

        Returns:
            Path to the generated EPUB file
        """
        if not articles:
            self.logger.warning("No articles provided for EPUB generation")
            return ""

        try:
            book = self._create_epub_book()
            chapters = []

            # Create chapters for each article
            for i, article in enumerate(articles, 1):
                chapter = self._create_chapter(article, i)
                book.add_item(chapter)
                chapters.append(chapter)

            # Create table of contents
            toc = [epub.Link('nav.xhtml', 'Table of Contents', 'toc')]
            for chapter in chapters:
                toc.append(chapter)
            book.toc = toc

            # Add default NCX and Nav file
            book.add_item(epub.EpubNcx())
            book.add_item(epub.EpubNav())

            # Create spine
            book.spine = ['nav'] + chapters

            # Generate filename if not provided
            if not filename:
                timestamp = datetime.now().strftime('%Y%m%d')
                filename = f"newspaper_{timestamp}"

            # Ensure .epub extension
            if not filename.endswith('.epub'):
                filename += '.epub'

            output_path = os.path.join(self.config.output_dir, filename)
            epub.write_epub(output_path, book)

            self.logger.info("Successfully generated EPUB: %s", output_path)
            return output_path

        except Exception as e:
            self.logger.error("Error generating EPUB: %s", e)
            raise

