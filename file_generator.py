from ebooklib import epub

def create_epub(articles, output_filename="generated.epub"):
    # Create a new EPUB book
    book = epub.EpubBook()

    # Set metadata (correct method)
    book.add_metadata('DC', 'title', "RSS Gazette")
    book.add_metadata('DC', 'creator', "Test")
    book.add_metadata('DC', 'language', "ar")

    # Create chapters for each article
    for i, article in enumerate(articles):
        chapter_title = article["title"]
        chapter_content = f"<h1>{chapter_title}</h1><p>{article['description']}</p><p><a href='{article['link']}'>Read more</a></p>"

        # Create an EpubItem for the chapter
        chapter = epub.EpubHtml(title=chapter_title, file_name=f"chapter_{i+1}.xhtml", lang="en")
        chapter.content = f'<?xml version="1.0" encoding="utf-8"?>' \
                          f'<html xmlns="http://www.w3.org/1999/xhtml"><body>{chapter_content}</body></html>'

        # Add the chapter to the book
        book.add_item(chapter)

        # Add the chapter to the spine (this tells the EPUB reader to display the chapter)
        book.spine.append(chapter)

    # Save the EPUB file
    epub.write_epub(output_filename, book)
    print(f"EPUB file created: {output_filename}")
