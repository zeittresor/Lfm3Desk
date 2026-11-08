"""Verified HTTPS using native Windows trust plus the packaged public CA bundle."""
from functools import lru_cache
import ssl
import sys
import urllib.request

@lru_cache(maxsize=1)
def tls_context():
    if sys.platform=='win32':
        import truststore
        context=truststore.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    else:
        context=ssl.create_default_context()
    import certifi
    context.load_verify_locations(cafile=certifi.where())
    context.verify_mode=ssl.CERT_REQUIRED
    context.check_hostname=True
    return context

def open_url(request,timeout=30):
    return urllib.request.urlopen(request,timeout=timeout,context=tls_context())
