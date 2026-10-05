"""Public issue reports through the Worker only; never attach logs or identities."""
from __future__ import annotations

import json
import logging
import platform
import threading
from urllib.error import HTTPError, URLError
from urllib.request import HTTPRedirectHandler, Request, build_opener

from . import __version__

REPORT_ENDPOINT = 'https://bug-report.kralsefo123.workers.dev'
REPORT_TIMEOUT = 10
log = logging.getLogger(__name__)


class _NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None  # Do not forward a public report to another endpoint.


def _status(code):
    return {200:'sent', 429:'limited', 400:'invalid'}.get(code, 'error')


class ReportClient:
    def __init__(self, send=None):
        self._send = send or build_opener(_NoRedirect()).open
        self._lock = threading.Lock()

    def submit(self, title, description):
        if not isinstance(title,str) or not isinstance(description,str):
            return {'status':'invalid'}
        title, description = title.strip(), description.strip()
        if not 5 <= len(title) <= 100 or not 10 <= len(description) <= 2000:
            return {'status':'invalid'}
        if not self._lock.acquire(blocking=False):
            return {'status':'busy'}
        try:
            data = json.dumps({'title':title, 'description':description,
                'version':__version__, 'os':' '.join((platform.system(),platform.release(),platform.version()))},
                ensure_ascii=False).encode('utf-8')
            request = Request(REPORT_ENDPOINT,data=data,headers={'Content-Type':'application/json'},method='POST')
            with self._send(request,timeout=REPORT_TIMEOUT) as response:
                return {'status':_status(response.status)}
        except HTTPError as exc:
            code = exc.code
            exc.close()
            return {'status':_status(code)}
        except (URLError, TimeoutError, OSError):
            log.warning('Report request failed: network unavailable or timed out')
            return {'status':'network'}
        except Exception:
            log.warning('Report request could not be completed')
            return {'status':'error'}
        finally:
            self._lock.release()
