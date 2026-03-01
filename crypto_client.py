"""
Crypto.com Exchange API v1 (Gen 3) - Client with authentication and diagnostics.

Usage:
    Set environment variables:
        CRYPTO_API_KEY    - Your API key
        CRYPTO_SECRET_KEY - Your secret key

    Run diagnostic:
        python crypto_client.py
"""

import hashlib
import hmac
import json
import os
import time
import requests


EXCHANGE_URL = "https://api.crypto.com/exchange/v1/"


def _build_params_string(params: dict) -> str:
    """
    Serialize params dict into a string for signing.

    Crypto.com spec: sort keys alphabetically, then concatenate key+value pairs.
    For nested values, convert to string representation.
    Empty dict -> empty string "".
    """
    if not params:
        return ""
    return "".join(f"{k}{params[k]}" for k in sorted(params.keys()))


def _sign(method: str, request_id: int, api_key: str, params: dict, nonce: int, secret_key: str) -> str:
    """
    Build the HMAC-SHA256 signature per Crypto.com Exchange API v1 spec.

    Signature payload: method + id + api_key + params_string + nonce
    """
    params_string = _build_params_string(params)
    sig_payload = f"{method}{request_id}{api_key}{params_string}{nonce}"
    signature = hmac.new(
        secret_key.encode("utf-8"),
        sig_payload.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()
    return signature


def call_private(method: str, params: dict, api_key: str, secret_key: str) -> dict:
    """Send an authenticated request to the Crypto.com Exchange API."""
    nonce = int(time.time() * 1000)
    request_id = 1

    signature = _sign(method, request_id, api_key, params, nonce, secret_key)

    body = {
        "id": request_id,
        "method": method,
        "api_key": api_key,
        "params": params,
        "nonce": nonce,
        "sig": signature,
    }

    response = requests.post(
        EXCHANGE_URL,
        json=body,
        headers={"Content-Type": "application/json"},
        timeout=10,
    )
    return {"http_status": response.status_code, "body": response.json()}


def diagnose(api_key: str, secret_key: str) -> None:
    """
    Run a step-by-step authentication diagnostic.

    Prints exactly what is being signed so issues are easy to spot.
    """
    method = "private/get-account-summary"
    request_id = 1
    params = {}
    nonce = int(time.time() * 1000)

    params_string = _build_params_string(params)
    sig_payload = f"{method}{request_id}{api_key}{params_string}{nonce}"
    signature = hmac.new(
        secret_key.encode("utf-8"),
        sig_payload.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()

    body = {
        "id": request_id,
        "method": method,
        "api_key": api_key,
        "params": params,
        "nonce": nonce,
        "sig": signature,
    }

    print("=" * 60)
    print("CRYPTO.COM AUTH DIAGNOSTIC")
    print("=" * 60)
    print(f"  Nonce (ms)     : {nonce}")
    print(f"  Params string  : '{params_string}' ({len(params_string)} chars)")
    print(f"  Sig payload    : '{sig_payload}'")
    print(f"  Sig payload len: {len(sig_payload)} chars")
    print(f"  Signature      : {signature}")
    print(f"  API key length : {len(api_key)} chars")
    print(f"  Secret length  : {len(secret_key)} chars")
    print()
    print("Request body:")
    print(json.dumps(body, indent=2))
    print()
    print("Sending request...")

    try:
        response = requests.post(
            EXCHANGE_URL,
            json=body,
            headers={"Content-Type": "application/json"},
            timeout=10,
        )
        result = response.json()
        print(f"HTTP Status : {response.status_code}")
        print(f"Response    : {json.dumps(result, indent=2)}")

        code = result.get("code", -1)
        if code == 0:
            print("\n✓ Authentication SUCCESS")
        elif code == 40101:
            print("\n✗ Error 40101 - Authentication failure")
            print()
            print("Possible causes:")
            print("  1. The secret key does not match this API key")
            print("     -> Regenerate both key and secret together in Crypto.com")
            print("  2. The API key was created on crypto.com APP (not Exchange)")
            print("     -> Must use Exchange API keys from exchange.crypto.com")
            print("  3. The API key is revoked, expired or not yet active")
            print("     -> Check status in Exchange > API Management")
            print("  4. IP whitelist does not include the server's current IP")
            print(f"     -> Verify your server IP is whitelisted")
        elif code == 40102:
            print("\n✗ Error 40102 - IP not whitelisted")
        else:
            print(f"\n✗ Unexpected error code: {code}")
    except requests.exceptions.RequestException as exc:
        print(f"Network error: {exc}")

    print("=" * 60)


if __name__ == "__main__":
    api_key = os.environ.get("CRYPTO_API_KEY", "")
    secret_key = os.environ.get("CRYPTO_SECRET_KEY", "")

    if not api_key or not secret_key:
        print("ERROR: Set CRYPTO_API_KEY and CRYPTO_SECRET_KEY environment variables.")
        print()
        print("Example:")
        print("  export CRYPTO_API_KEY='your_api_key'")
        print("  export CRYPTO_SECRET_KEY='your_secret_key'")
        print("  python crypto_client.py")
        raise SystemExit(1)

    diagnose(api_key, secret_key)
