import xml.etree.ElementTree as ET
import urllib.error
from skills import cached_ping

def parse_feed(url, timeout: int = 5) -> list:
    url_for_error = "unknown_source"

    if isinstance(url, str) and (url.strip().startswith('http://') or url.strip().startswith('https://')):
        url_for_error = url
        response = cached_ping.ping_and_cache(url, timeout=timeout)
    else:
        response = url
    
    if response is None:
        raise ValueError("Payload is None")

    status_code = 200
    if hasattr(response, 'status_code'):
        status_code = response.status_code
    elif hasattr(response, 'status'):
        status_code = response.status
    elif isinstance(response, dict):
        status_code = response.get('status_code', response.get('status', 200))

    if isinstance(status_code, int) and status_code >= 400:
        raise urllib.error.HTTPError(url_for_error, status_code, "Bad Status Code", {}, None)
        
    raw_data = None
    if hasattr(response, 'read') and callable(response.read):
        raw_data = response.read()
    elif isinstance(response, (str, bytes)):
        raw_data = response
    elif isinstance(response, dict):
        for key in ('data', 'content', 'text', 'body', 'raw'):
            if key in response:
                raw_data = response[key]
                break

    if raw_data is None:
        raise ValueError("Payload read returned None")

    if not raw_data or (isinstance(raw_data, (str, bytes)) and not raw_data.strip()):
        return []
        
    try:
        root = ET.fromstring(raw_data)
    except Exception as e:
        raise ET.ParseError(f"Malformed XML: {e}")

    targets = []
    
    tag_lower = root.tag.lower()
    
    # RSS 2.0
    if 'rss' in tag_lower or root.find('.//item') is not None:
        for item in root.findall('.//item'):
            title_elem = item.find('title')
            link_elem = item.find('link')
            desc_elem = item.find('description')
            pub_elem = item.find('pubDate')
            
            targets.append({
                'title': title_elem.text if title_elem is not None and title_elem.text else '',
                'link': link_elem.text if link_elem is not None and link_elem.text else '',
                'description': desc_elem.text if desc_elem is not None and desc_elem.text else '',
                'pubDate': pub_elem.text if pub_elem is not None and pub_elem.text else ''
            })
            
    # Atom Feed
    elif 'feed' in tag_lower or root.find('{http://www.w3.org/2005/Atom}entry') is not None or root.find('entry') is not None:
        entries = root.findall('{http://www.w3.org/2005/Atom}entry')
        if not entries:
            entries = root.findall('entry')
            
        for entry in entries:
            title_elem = entry.find('{http://www.w3.org/2005/Atom}title')
            if title_elem is None:
                title_elem = entry.find('title')
                
            link_elem = entry.find('{http://www.w3.org/2005/Atom}link')
            if link_elem is None:
                link_elem = entry.find('link')
                
            summary_elem = entry.find('{http://www.w3.org/2005/Atom}summary')
            if summary_elem is None:
                summary_elem = entry.find('summary')
            if summary_elem is None:
                summary_elem = entry.find('{http://www.w3.org/2005/Atom}content')
            if summary_elem is None:
                summary_elem = entry.find('content')
                
            updated_elem = entry.find('{http://www.w3.org/2005/Atom}updated')
            if updated_elem is None:
                updated_elem = entry.find('updated')

            link_href = ''
            if link_elem is not None:
                link_href = link_elem.attrib.get('href', '')
                if not link_href and link_elem.text:
                    link_href = link_elem.text

            targets.append({
                'title': title_elem.text if title_elem is not None and title_elem.text else '',
                'link': link_href,
                'description': summary_elem.text if summary_elem is not None and summary_elem.text else '',
                'pubDate': updated_elem.text if updated_elem is not None and updated_elem.text else ''
            })
            
    return targets