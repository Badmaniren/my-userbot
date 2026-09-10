from skills.file_cache import FileCache
from skills.http_ping import check_endpoint

def ping_and_cache(url, timeout=5):
    cache = FileCache()
    cached_result = cache.get(url)
    
    if cached_result is not None:
        return cached_result
    
    result = check_endpoint(url, timeout)
    cache.set(url, result)
    
    return result