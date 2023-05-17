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
        self.team1 = game["teamTriCodes"][0]
        self.team2 = game["teamTriCodes"][1]
        self.blockName = game["blockName"]
        self.subBlockName = game["subBlockName"]
        self.status = game["status"]
        self.createdAt = game["createdAt"]
        self.assets = game["assets"]
        self.tags = game["tags"]

    @property
    def game_finished(self) -> bool:
        return self.status == "FINISHED" or self.status == "ENDED"

    @property
    def rofl_available(self) -> bool:
        return "ROFL_REPLAY" in self.assets or "SCRIM_REPLAY" in self.assets

    @property
    def teams(self) -> str:
        return f"{self.team1} vs {self.team2}"

    @property
    def local_timestring(self) -> int:
        return int(isoparse(self.createdAt).timestamp())

class BayesScrim(BayesGame):
    def __init__(self, game):
        self.createdAt = game.get("createdAt")
        self.status = game.get("status")
        self.game_id = game.get("id")
        self.team1 = game["teams"][0]["code"]
        if len(game["teams"]) > 1:
            self.team2 = game["teams"][1]["code"]
        else:
            self.team2 = "Unknown"
        if game["replayAvailable"]:
            self.assets = ["SCRIM_REPLAY"]
        else:
            self.assets = []
        self.game_name = game["name"]
        
def get_matches(querystring: Optional[dict]) -> list:
    token = get_token()
    response = requests.get(
        "https://lolesports-api.bayesesports.com/emh/v1/games",
        headers={"Authorization": f"Bearer {token}"},
        params=querystring,
    )

    if response.status_code != 200:
        return []
    else:
        return response.json()["games"]

def get_icons():
    token = get_token()
    response = requests.get(
        'https://lolesports-api.bayesesports.com/historic/v1/riot-lol/leagues',
        headers={"Authorization": f"Bearer {token}"},
    ).json()
    return {tournament['name']: tournament['logoUrl'] for tournament in response}

def get_tags():
    token = get_token()
    return requests.get(
        "https://lolesports-api.bayesesports.com/emh/v1/tags",
        headers={"Authorization": f"Bearer {token}"},
    ).json()

def get_scrim_games(querystring: Optional[dict]) -> list:
    # Gets the latest 20 scrim games
    token = get_token()
    response = requests.get(
        "https://lolesports-api.bayesesports.com/scrim/v1/games",
        headers={"Authorization": f"Bearer {token}"},
        params=querystring,
    )
    if response.status_code != 200:
        return []
    else:
        return response.json()["games"]

def get_asset(
    gameId: str, asset_type: Optional[str] = "ROFL_REPLAY"
) -> Optional[str]:
    token = get_token()
    if asset_type == "SCRIM_REPLAY":
        response = requests.get(
            f"https://lolesports-api.bayesesports.com/scrim/v1/games/{gameId}/downloadRiotReplay",
            headers={"Authorization": f"Bearer {token}"},
        )
    else:
        querystring = {"gameId": gameId, "type": asset_type}
        response = requests.get(
            f"https://lolesports-api.bayesesports.com/emh/v1/games/{gameId}/download",
            headers={"Authorization": f"Bearer {token}"},
            params=querystring,
        )
    if response.status_code != 200:
        return None
    else:
        return response.json()["url"]

def get_asset_link(gameId: str) -> str:
    # Scrim gameId's are integers, so we can check if it's a scrim game
    # There could be a chance though that match games have integers as their gameId
    if gameId.isnumeric():
        match_link = get_asset(gameId, "SCRIM_REPLAY")
        if match_link is None:
            match_link = get_asset(gameId, "ROFL_REPLAY")
            if match_link is None:
                return "Game not found"
            else:
                return match_link
        else:
            return match_link
    else:
        match_link = get_asset(gameId, "ROFL_REPLAY")
        if match_link is None:
            return "No replay could be found"
        else:
            return match_link