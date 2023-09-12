from dateutil.parser import isoparse
from typing import Optional

import discord
from get_token import get_token
import requests
import enum

class BayesGameType(enum.Enum):
    ESPORTS = "ESPORTS"
    SCRIM = "SCRIM"
    CHAMPIONS_QUEUE = "CHAMPIONS_QUEUE"

class BayesAssetType(enum.Enum):
    ROFL_REPLAY = "ROFL_REPLAY"
    HISTORIC_DUMP = "HISTORIC_BAYES_DUMP"
    HISTORIC_SEPARATED = "HISTORIC_BAYES_SEPARATED"
    GAMH_DETAILS = "GAMH_DETAILS"
    GAMH_SUMMARY = "GAMH_SUMMARY"

class BayesTeam:
    def __init__(self, team):
        self.name = team.get("name")
        self.code = team.get("code")
        self._esports_Id = team.get("esportsTeamId")
    
    @property
    def esports_Id(self):
        if self._esports_Id is not None:
            return int(self._esports_Id)
        else:
            return None

class BayesGame:
    def __init__(self, game: dict):
        self.game = game
        self.type = game.get("type")
        self.platform_id = game.get("platformGameId")
        self.esports_id = game.get("esportsGameId")
        self.game_name = game.get("name")
        self.lobby_name = game.get("name")
        self.status = game.get("status")
        self._started_at = game.get("startedAt")
        self._ended_at = game.get("endedAt")
        self.league = game.get("league")
        self.tournament = game.get("tournament")
        self.assets = game.get("assets")
        self.tags = game.get("tags")
        self._teams = game.get("teams")
        self.game_version = game.get("gameVersion")
        self.match_format = game.get("matchFormat")
        # Not sure what this is as there is no documentation on it
        self.state = game.get("state")
    
    @property
    def game_type(self) -> Optional[BayesGameType]:
        if self.type is None:
            return None
        return BayesGameType(self.type)
    
    @property
    def patch(self) -> Optional[str]:
        if self.game_version is None:
            return None
        return self.game_version.split(".")[0] + "." + self.game_version.split(".")[1]
    @property
    def teams(self):
        if self._teams is None:
            return None
        return [BayesTeam(team) for team in self._teams]
    @property
    def team_string(self):
        if self.teams is None:
            return "??? vs ???"
        if len(self.teams) == 2:
            return f"{self.teams[0].name} vs {self.teams[1].name}"
        elif len(self.teams) == 1:
            return f"{self.teams[0].name} vs ???"
    
    @property
    def started_at(self):
        return self.timestring_to_integer(self._started_at)
    
    @property
    def ended_at(self):
        return self.timestring_to_integer(self._ended_at)
    
    @property
    def team_names(self):
        if self.teams is None:
            return ["???", "???"]
        return [team.name for team in self.teams]

    @property
    def game_finished(self) -> bool:
        return self.status in ["LINKED", "FINISHED", "ENDED"] # This is not documented, but it's what the API returns...

    @property
    def rofl_available(self) -> bool:
        if self.assets is None:
            return False
        return any(asset in ["ROFL_REPLAY"] for asset in self.assets) # Also not documented, but it's what the API returns...

    def timestring_to_integer(self, timestring) -> Optional[int]:
        return int(isoparse(timestring).timestamp()) if timestring is not None else None

class BayesMatch():
    def __init__(self, match: dict):
        self._total_count = match.get("totalCount")
        self._total_pages = match.get("totalPages")
        self._page_number = match.get("pageNumber")
        self._items = match.get("items")

    @property
    def games(self) -> list[BayesGame]:
        if self._items is not None:
            return [BayesGame(game) for game in self._items]
        return []
        
    @property
    def games_available(self) -> bool:
        if self.games is not None:
            if len(self.games) > 0:
                return True
        return False
    
    @property
    def page_string(self) -> str:
        if self._total_count is not None and self._total_pages is not None and self._page_number is not None:
            return f"Page {self._page_number + 1}/{self._total_pages - 1} ({self._total_count} games found)"
        return "Page 1/1 (0 games found)"

def get_asset_url(platform_id: str, asset_type: BayesAssetType) -> Optional[str]:
    token = get_token()
    url = f"https://lolesports-api.bayesesports.com/v2/games/{platform_id}/download?option={asset_type.value}"
    response = requests.get(
        url, headers={"Authorization": f"Bearer {token}"}
    )
    return response.json()["url"] if response.ok else None

def get_matches(querystring) -> Optional[BayesMatch]:
    token = get_token()
    try:
        response = requests.get(
            "https://lolesports-api.bayesesports.com/v2/games",
            headers={"Authorization": f"Bearer {token}"},
            params=querystring,
        )
        response.raise_for_status()
        return BayesMatch(response.json())
    except (requests.exceptions.RequestException, ValueError):
        return None

def get_team_names(possible_team_name: discord.AutocompleteContext) -> list[str]:
    token = get_token()
    response = requests.get(
        f"https://lolesports-api.bayesesports.com/v2/games/teams/suggestions?name={possible_team_name.value}",
        headers={"Authorization": f"Bearer {token}"},
    )
    return [_.get("name") for _ in response.json()] if response.ok else []
