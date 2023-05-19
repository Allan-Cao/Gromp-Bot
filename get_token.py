# https://docs.bayesesports.com/docs-data-portal/api/token_reuse/ with modifications
import os
import requests
import json
from typing import Optional
from datetime import datetime
from datetime import timedelta

if os.path.exists(".env"):
    from dotenv import load_dotenv

    load_dotenv()

bayes_username = os.environ.get("BAYES_USERNAME")
bayes_password = os.environ.get("BAYES_PASSWORD")
if bayes_username is None or bayes_password is None:
    raise ValueError("Bayes login is not set.")
token_file = os.environ.get("TOKEN_FILE", "token.json")


def portal_login(username: str, password: str) -> dict | None:
    """Send API request to get an access token using supplied `username` and `password`. Return JSON response, received from the server"""
    url = "https://lolesports-api.bayesesports.com/auth/login"
    headers = {"Content-Type": "application/json"}
    creds = {"username": username, "password": password}
    response = requests.post(url, json=creds, headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        response.raise_for_status()


def store_token(response_token: dict, filename: str):
    """Save access token details, received from the API to a JSON file. The expiresIn field is replaced with expiresAt UNIX timestamp"""
    result = dict(response_token)
    expire_date = datetime.now() + timedelta(seconds=result.pop("expiresIn"))
    result["expiresAt"] = expire_date.timestamp()
    with open(filename, "w") as f:
        json.dump(result, f)


def is_stored_token_fresh(stored_token: dict) -> bool:
    """Check if the access token that is stored in filename is still valid"""
    expire_date = datetime.fromtimestamp(stored_token["expiresAt"])
    return datetime.now() < expire_date


def get_token_from_file(filename) -> Optional[str]:
    """Load access token info from JSON `filename` and return the access token if it is still fresh. If it's not, or if the file is missing, return None"""
    if not os.path.exists(filename):
        return None
    with open(filename) as f:
        stored_token = json.load(f)
    if is_stored_token_fresh(stored_token):
        return stored_token["accessToken"]
    else:
        return None


def get_token() -> str:
    """Get an auth token from the local file or send an API request to login if stored token is too old"""
    token = get_token_from_file(token_file)
    if token is None:
        # If there is not a saved token or it's too old, we need to re-generate it.
        response_token = portal_login(bayes_username, bayes_password)
        if response_token is None:
            raise ValueError(
                "An error occured authenticating with the Bayes authentication server."
            )
        store_token(response_token, token_file)
        token = response_token["accessToken"]
    return token


if __name__ == "__main__":
    print(get_token())
