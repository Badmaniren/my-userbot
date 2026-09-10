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
            status = getattr(response, 'status', None)
            if status is None:
                status = response.getcode()
            if not isinstance(status, int):
                status = getattr(response, 'status', None)
            if not isinstance(status, int):
                status = 500

            headers = dict(response.headers.items())
            return {
                "status": status,
                "headers": headers
            }
    except socket.timeout:
        return {"status": 408, "error": "timeout"}
    except urllib.error.HTTPError as e:
        return {"status": e.code, "error": str(e)}
    except urllib.error.URLError as e:
        if isinstance(e.reason, socket.timeout):
            return {"status": 408, "error": "timeout"}
        return {"status": 503, "error": str(e)}
    except (TypeError, ValueError) as e:
        raise e
    except Exception as e:
        return {"status": 500, "error": str(e)}