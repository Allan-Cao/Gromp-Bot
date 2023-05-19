from dateutil.parser import isoparse
from typing import Optional
from get_token import get_token
import requests
import re


class BayesGame:
    def __init__(self, game):
        self.game = game
        self.game_id = game["platformGameId"]
        self.game_name = game["name"]
        game_name = re.search("game ?\d", game["name"])
        # Currently self.name is not used due to inconsistent naming
        if game_name is None:
            self.name = ""
        else:
            self.name = game_name[0]
        self.team1_code = game["teamTriCodes"][0]
        self.team2_code = game["teamTriCodes"][1]
        self.blockName = game["blockName"]
        self.subBlockName = game["subBlockName"]
        self.status = game["status"]
        self.createdAt = game["createdAt"]
        self.assets = game["assets"]
        self.tags = game["tags"]

    @property
    def game_finished(self) -> bool:
        return self.status in ["FINISHED", "ENDED"]

    @property
    def rofl_available(self) -> bool:
        return any(asset in ["ROFL_REPLAY", "SCRIM_REPLAY"] for asset in self.assets)

    @property
    def teams(self) -> str:
        return f"{self.team1_code} vs {self.team2_code}"

    @property
    def local_timestring(self) -> int:
        return int(isoparse(self.createdAt).timestamp())


class BayesScrim(BayesGame):
    def __init__(self, game):
        self.createdAt = game.get("createdAt")
        self.status = game.get("status")
        self.game_id = game.get("id")
        self.team1_code = game["teams"][0]["code"]
        self.team2_code = (
            game["teams"][1]["code"] if len(game["teams"]) > 1 else "Unknown"
        )
        self.assets = ["SCRIM_REPLAY"] if game["replayAvailable"] else []
        self.game_name = game["name"]


def get_matches(querystring: Optional[dict]) -> list:
    token = get_token()
    try:
        response = requests.get(
            "https://lolesports-api.bayesesports.com/emh/v1/games",
            headers={"Authorization": f"Bearer {token}"},
            params=querystring,
        )
        response.raise_for_status()
        return response.json()["games"]
    except (requests.exceptions.RequestException, ValueError):
        return []


def get_icons() -> dict:
    token = get_token()
    try:
        response = requests.get(
            "https://lolesports-api.bayesesports.com/historic/v1/riot-lol/leagues",
            headers={"Authorization": f"Bearer {token}"},
        )
        response.raise_for_status()
        return {
            tournament["name"]: tournament["logoUrl"] for tournament in response.json()
        }
    except (requests.exceptions.RequestException, ValueError):
        return {}


def get_tags() -> list[str]:
    token = get_token()
    response = requests.get(
        "https://lolesports-api.bayesesports.com/emh/v1/tags",
        headers={"Authorization": f"Bearer {token}"},
    )
    return response.json() if response.ok else []


def get_scrim_games(querystring: Optional[dict]) -> list:
    # Gets the latest 20 scrim games
    token = get_token()
    response = requests.get(
        "https://lolesports-api.bayesesports.com/scrim/v1/games",
        headers={"Authorization": f"Bearer {token}"},
        params=querystring,
    )
    return response.json()["games"] if response.ok else []


def get_asset(
    game_id: int | str, asset_type: Optional[str] = "ROFL_REPLAY"
) -> Optional[str]:
    token = get_token()
    querystring = {}
    if asset_type == "SCRIM_REPLAY":
        url = f"https://lolesports-api.bayesesports.com/scrim/v1/games/{game_id}/downloadRiotReplay"
    else:
        querystring.update({"gameId": game_id, "type": asset_type})
        url = f"https://lolesports-api.bayesesports.com/emh/v1/games/{game_id}/download"
    response = requests.get(
        url, headers={"Authorization": f"Bearer {token}"}, params=querystring
    )
    return response.json()["url"] if response.ok else None


def get_asset_link(game_id: str) -> str:
    if game_id.isnumeric():
        asset_types = ["SCRIM_REPLAY", "ROFL_REPLAY"]
    else:
        asset_types = ["ROFL_REPLAY"]
    for asset_type in asset_types:
        asset_link = get_asset(game_id, asset_type)
        if asset_link is not None:
            return asset_link
    return "Game not found" if type(game_id) == int else "No replay could be found"
