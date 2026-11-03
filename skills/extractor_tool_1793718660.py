import re
from bs4 import BeautifulSoup


class MetadataExtractor:
    def __init__(self, markup=None):
        if isinstance(markup, bytes):
            markup = markup.decode('utf-8', errors='ignore')
        self.markup = markup

    def _get_text(self):
        if not self.markup:
            return ""
        if isinstance(self.markup, bytes):
            return self.markup.decode('utf-8', errors='ignore')
        return str(self.markup)

    def extract_meta(self):
        text = self._get_text()
        if not text:
            return {}
        soup = BeautifulSoup(text, 'html.parser')
        meta_data = {}
        for tag in soup.find_all('meta'):
            key = tag.get('name') or tag.get('property')
            val = tag.get('content')
            if key and val:
                meta_data[key] = val
        return meta_data

    def extract_title(self):
        text = self._get_text()
        if not text:
            return None
        soup = BeautifulSoup(text, 'html.parser')
        title_tag = soup.find('title')
        return title_tag.string if (title_tag and title_tag.string) else None

    def extract_from_text(self, text):
        if isinstance(text, bytes):
            text = text.decode('utf-8', errors='ignore')
        if not text:
            return {}

        result = {}
        match = re.match(r'^---\s*\n(.*?)\n---\s*', text, re.DOTALL)
        if match:
            lines = match.group(1).strip().split('\n')
            for line in lines:
                if ':' in line:
                    k, v = line.split(':', 1)
                    result[k.strip()] = v.strip()

        result.update(self.extract_meta_from_html_comment(text))
        return result

    def extract_meta_from_html_comment(self, text):
        if isinstance(text, bytes):
            text = text.decode('utf-8', errors='ignore')
        if not text:
            return {}

        comment_match = re.search(r'<!--(.*?)-->', text, re.DOTALL)
        if comment_match:
            lines = comment_match.group(1).strip().split('\n')
            data = {}
            for line in lines:
                if ':' in line:
                    k, v = line.split(':', 1)
                    data[k.strip()] = v.strip()
            return data
        return {}

    def extract(self):
        text = self._get_text()
        if not text:
            return {}

        data = {}
        data.update(self.extract_from_text(text))
        data.update(self.extract_meta())

        title = self.extract_title()
        if title:
            data['title'] = title

        return data

    def extract_from_file(self, file_path):
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        if isinstance(content, bytes):
            content = content.decode('utf-8', errors='ignore')
        self.markup = content
        return self.extract()

    @classmethod
    def from_file(cls, file_path):
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        if isinstance(content, bytes):
            content = content.decode('utf-8', errors='ignore')
        return cls(content)


def extract_metadata(markup):
    return MetadataExtractor(markup).extract()


def extract_meta_tags(markup):
    return MetadataExtractor(markup).extract_meta()


def extract_title(markup):
    return MetadataExtractor(markup).extract_title()


def extract_from_file(file_path):
    return MetadataExtractor().extract_from_file(file_path)


def parse(markup):
    return MetadataExtractor(markup).extract()