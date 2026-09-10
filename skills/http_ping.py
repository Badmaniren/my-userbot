import urllib.request
import urllib.error
import socket

def check_endpoint(url, timeout=5):
    if not isinstance(url, str):
        raise TypeError("URL must be a string")
    if not url:
        raise ValueError("URL cannot be empty")

    try:
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=timeout) as response:
            headers = dict(response.headers.items())
            return {
                "status": response.getcode(),
                "headers": headers
            }
    except socket.timeout:
        return {"status": 408, "error": "timeout"}
    except (urllib.error.URLError, ValueError) as e:
        raise e