import time
import uuid
import hashlib
import hmac
import requests
import logging

_LOGGER = logging.getLogger(__name__)


def sha256_hex(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def hmac_sha256(key: str, msg: str) -> str:
    return hmac.new(key.encode("utf-8"), msg.encode("utf-8"), hashlib.sha256).hexdigest().upper()


def canonical_url(path: str, query: dict) -> str:
    if not query:
        return path
    items = sorted(query.items(), key=lambda x: x[0])
    qs = "&".join(f"{k}={v}" for k, v in items)
    return f"{path}?{qs}"


def build_headers_block(custom_headers: dict) -> str:
    if not custom_headers:
        return ""
    return "".join(f"{k}:{v}\n" for k, v in custom_headers.items())


def build_string_to_sign(method: str, body: str, custom_headers: dict, path: str, query: dict) -> str:
    body_sha = sha256_hex(body.encode() if body else b"")
    headers_block = build_headers_block(custom_headers)
    url = canonical_url(path, query)
    return f"{method.upper()}\n{body_sha}\n{headers_block}\n{url}"


class TuyaShadowApi:
    def __init__(self, client_id: str, client_secret: str, region: str):
        self._client_id = client_id
        self._client_secret = client_secret
        self._region = region
        self._base = f"https://openapi.tuya{region}.com"
        self._token = None
        self._token_expire = 0  # epoch ms

    def _get_token(self) -> str:
        now = int(time.time() * 1000)
        if self._token and now < self._token_expire - 60_000:
            return self._token

        path = "/v1.0/token"
        query = {"grant_type": 1}
        url = self._base + canonical_url(path, query)
        method = "GET"
        body = ""
        nonce = uuid.uuid4().hex
        t = int(time.time() * 1000)

        string_to_sign = build_string_to_sign(method, body, {}, path, query)
        to_sign = self._client_id + str(t) + nonce + string_to_sign
        sign = hmac_sha256(self._client_secret, to_sign)

        headers = {
            "client_id": self._client_id,
            "t": str(t),
            "sign_method": "HMAC-SHA256",
            "nonce": nonce,
            "sign": sign,
            "mode": "cors",
        }

        resp = requests.get(url, headers=headers, timeout=10)
        _LOGGER.debug("Token response: %s", resp.text)
        js = resp.json()
        if not js.get("success") or "result" not in js:
            raise RuntimeError(f"Failed to get token: {js}")
        result = js["result"]
        self._token = result["access_token"]
        self._token_expire = now + int(result.get("expire_time", 7200)) * 1000
        return self._token

    def get_shadow(self, device_id: str) -> dict:
        token = self._get_token()

        path = f"/v2.0/cloud/thing/{device_id}/shadow/properties"
        url = self._base + path
        query = {}
        method = "GET"
        body = ""
        nonce = uuid.uuid4().hex
        t = int(time.time() * 1000)

        string_to_sign = build_string_to_sign(method, body, {}, path, query)
        to_sign = self._client_id + token + str(t) + nonce + string_to_sign
        sign = hmac_sha256(self._client_secret, to_sign)

        headers = {
            "client_id": self._client_id,
            "access_token": token,
            "t": str(t),
            "nonce": nonce,
            "sign_method": "HMAC-SHA256",
            "sign": sign,
        }

        resp = requests.get(url, headers=headers, timeout=10)
        _LOGGER.debug("Shadow response for %s: %s", device_id, resp.text)
        js = resp.json()
        if not js.get("success") or "result" not in js:
            raise RuntimeError(f"Failed to get shadow for {device_id}: {js}")
        # Returns list of {code, value, ...}
        return js["result"]["properties"]
