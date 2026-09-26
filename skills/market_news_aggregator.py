import market_parser
import db_storage

def aggregate_news(source_url):
    client = market_parser.ParserClient()
    stream = client.fetch_feed(source_url)
    content = stream.read().decode('utf-8')
    db = db_storage.DatabaseConnection()
    article_id = db.save_article(content)
    return {"id": article_id, "source": source_url}

def process_raw_stream(url):
    parser = market_parser.ParserClient()
    stream = parser.fetch_raw_stream(url)
    data = stream.read()
    if not data:
        raise ValueError("Empty stream")
    return len(data)

def aggregate_and_filter_news(parsed_items):
    filtered_items = []
    for item in parsed_items:
        if item and isinstance(item, dict):
            filtered_items.append(item)
    return filtered_items