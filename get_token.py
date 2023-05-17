import os
import requests
import json
from typing import Optional
from datetime import datetime
from datetime import timedelta

TOKEN_FILE = "token.json"
# Temporary for dev
from dotenv import load_dotenv
load_dotenv()

PWD_ENV = os.environ.get("HEET_PWD")
USR_ENV = os.environ.get("HEET_USR")

if PWD_ENV == None:
    print("Bayes password not found")
    quit()
if USR_ENV == None:
    print("Bayes username not found")
    quit()

def portal_login(username: str, password: str) -> dict:
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
    token = get_token_from_file(TOKEN_FILE)
    if token is None:
        username = USR_ENV
        password = PWD_ENV
        response_token = portal_login(username, password)
        store_token(response_token, TOKEN_FILE)
        token = response_token["accessToken"]
    return token


if __name__ == "__main__":
    print(get_token())
