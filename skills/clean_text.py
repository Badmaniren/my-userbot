import re
from html.parser import HTMLParser

class _HTMLFilter(HTMLParser):
    def __init__(self):
        super().__init__()
        self.reset()
        self.strict = False
        self.convert_charrefs = True
        self.text = []

    def handle_data(self, d):
        self.text.append(d)

    def handle_entityref(self, name):
        self.text.append(f'&{name};')

    def handle_charref(self, name):
        self.text.append(f'&#{name};')

def clean(text: str) -> str:
    if not isinstance(text, str):
        raise TypeError("Input must be a string")
    
    parser = _HTMLFilter()
    parser.feed(text)
    parser.close()
    raw_text = "".join(parser.text)
    
    cleaned_chars = []
    for char in raw_text:
        cat = ord(char)
        if cat < 32 and char not in ('\n', '\r', '\t'):
            continue
        if cat == 127:
            continue
        cleaned_chars.append(char)
        
    res = "".join(cleaned_chars)
    res = res.replace('\n', ' ').replace('\r', ' ').replace('\t', ' ')
    res = re.sub(r'\s+', ' ', res)
    return res.strip()