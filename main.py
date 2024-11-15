import json
import feedparser

with open("feeds.json", "r") as file:
    raw_data = json.load(file)

urls = set()
for feed in raw_data['feeds']:
    urls.add(feed['url'])

for url in urls:
    feed = feedparser.parse(url)
    for entry in feed.entries:
        if 'content' in entry:
            fulltext = entry.content[0].value
        else:
            fulltext = entry.description
        print(fulltext)