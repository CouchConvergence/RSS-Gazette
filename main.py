import feedparser
from newspaper import Article

URL = 'https://mada38.appspot.com/www.madamasr.com/feed'

feed = feedparser.parse(URL)

urls = [entry.link for entry in feed.entries if 'link' in entry]

article = Article(urls[0])

article.download()

article.parse()

print("Title:", article.title)
print("Authors:", ', '.join(article.authors))
print("Published Date:", article.publish_date)
print("Content:", article.text)