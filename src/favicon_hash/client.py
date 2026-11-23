import os
import urllib3
import requests
from urllib.parse import quote_plus
from pycti import OpenCTIConnectorHelper

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class FaviconHashClient:
    def __init__(self, helper: OpenCTIConnectorHelper, api_url: str, timeout: int = 10,
                 ca_bundle: str = None):
        self.helper = helper
        self.api_url = api_url.rstrip('/')
        self.timeout = timeout
        self.user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        if ca_bundle and os.path.exists(ca_bundle):
            self.verify_ssl = ca_bundle
            self.helper.log_info(f"Используется CA-сертификат: {ca_bundle}")
        else:
            self.verify_ssl = False
            self.helper.log_info("Проверка SSL отключена (verify=False)")
        self.proxies = {}
        if os.getenv('HTTP_PROXY'):
            self.proxies['http'] = os.getenv('HTTP_PROXY')
        if os.getenv('HTTPS_PROXY'):
            self.proxies['https'] = os.getenv('HTTPS_PROXY')
        if self.proxies:
            self.helper.log_info(f"Используются прокси: {self.proxies}")

    def _get_favicon_data_for_protocol(self, domain: str, protocol: str):
        full_url = f"{protocol}://{domain}"
        encoded_url = quote_plus(full_url)
        request_url = f"{self.api_url}?url={encoded_url}"
        headers = {"User-Agent": self.user_agent}
        try:
            response = requests.get(
                request_url,
                headers=headers,
                timeout=self.timeout,
                verify=self.verify_ssl,
                proxies=self.proxies
            )
            response.raise_for_status()
            data = response.json()
            required_fields = ["req_location", "favicon_hash", "md5", "sha256"]
            if all(field in data for field in required_fields):
                return data
            else:
                self.helper.log_debug(f"Неполные данные для {full_url}: {data}")
                return None
        except Exception as e:
            self.helper.log_debug(f"Ошибка для {full_url}: {e}")
            return None

    def get_favicon_data(self, domain: str):
        data = self._get_favicon_data_for_protocol(domain, "https")
        if data is None:
            self.helper.log_debug(f"HTTPS не удался, пробуем HTTP для {domain}")
            data = self._get_favicon_data_for_protocol(domain, "http")
        return data
