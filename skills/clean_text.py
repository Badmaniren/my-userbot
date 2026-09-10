import re
from html import unescape

def clean(text: str) -> str:
    if not isinstance(text, str):
        raise TypeError("Input must be a string")
    
    text = re.sub(r'<script.*?>.*?</script>', '', text, flags=re.IGNORECASE | re.DOTALL)
    text = re.sub(r'<[^>]+>', '', text)
    text = unescape(text)
    
    unprintable_chars = ''.join(chr(i) for i in range(32) if i not in (9, 10, 13)) + ''.join(chr(i) for i in range(127, 160))
    translation_table = str.maketrans('', '', unprintable_chars)
    text = text.translate(translation_table)
    
    text = re.sub(r'\s+', ' ', text)
    
    return text.strip()