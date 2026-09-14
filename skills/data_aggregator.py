from skills import rss_parser
from skills import clean_text


def aggregate_data(url, timeout=None):
    if not isinstance(url, str):
        raise TypeError("URL must be a string")
    
    try:
        if timeout is not None:
            raw_items = rss_parser.parse_feed(url, timeout=timeout)
        else:
            raw_items = rss_parser.parse_feed(url)
    except Exception:
        return []

    if not raw_items:
        return []

    aggregated = []
    for item in raw_items:
        cleaned_item = {}
        for key, value in item.items():
            if isinstance(value, str):
                cleaned_item[key] = clean_text.clean(value)
            else:
                cleaned_item[key] = value
        aggregated.append(cleaned_item)

    return aggregated