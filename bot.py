from typing import List, Optional
from bayes_helper import (
    BayesGame,
    BayesGameType,
    BayesMatch,
    get_asset_url,
    BayesAssetType,
    get_team_names,
    get_matches,
    get_all_tags,
)

import os
import logging
from datetime import datetime
from fuzzywuzzy import process
import disnake
from disnake.ext import commands
from disnake import Option

# Logging configuration
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(),
    ],
)

# Load environment variables
if os.path.exists(".env"):
    from dotenv import load_dotenv

    load_dotenv()

discord_token = os.environ.get("DISCORD_TOKEN")
guilds_allowed = os.environ.get("GUILDS_ALLOWED")
if guilds_allowed is None:
    guild_ids = []
else:
    guild_ids = list(map(int, guilds_allowed.split(",")))
tags = get_all_tags()

# Bot initialization
bot = commands.InteractionBot(test_guilds=guild_ids)


class SeriesViewer(disnake.ui.View):
    def __init__(self, embeds: List[disnake.Embed]):
        super().__init__(timeout=None)
        self.embeds = embeds
        self.index = 0

        # Sets the footer of the embeds with their respective page numbers.
        for i, embed in enumerate(self.embeds):
            embed.set_footer(text=f"Game {i + 1} of {len(self.embeds)}")

        self._update_state()

    def _update_state(self) -> None:
        self.first_page.disabled = self.prev_page.disabled = self.index == 0
        self.last_page.disabled = self.next_page.disabled = (
            self.index == len(self.embeds) - 1
        )

    @disnake.ui.button(emoji="⏪", style=disnake.ButtonStyle.blurple)
    async def first_page(
        self, button: disnake.ui.Button, inter: disnake.MessageInteraction
    ):
        self.index = 0
        self._update_state()

        await inter.response.edit_message(embed=self.embeds[self.index], view=self)

    @disnake.ui.button(emoji="◀", style=disnake.ButtonStyle.secondary)
    async def prev_page(
        self, button: disnake.ui.Button, inter: disnake.MessageInteraction
    ):
        self.index -= 1
        self._update_state()

        await inter.response.edit_message(embed=self.embeds[self.index], view=self)

    @disnake.ui.button(emoji="▶", style=disnake.ButtonStyle.secondary)
    async def next_page(
        self, button: disnake.ui.Button, inter: disnake.MessageInteraction
    ):
        self.index += 1
        self._update_state()

        await inter.response.edit_message(embed=self.embeds[self.index], view=self)

    @disnake.ui.button(emoji="⏩", style=disnake.ButtonStyle.blurple)
    async def last_page(
        self, button: disnake.ui.Button, inter: disnake.MessageInteraction
    ):
        self.index = len(self.embeds) - 1
        self._update_state()

        await inter.response.edit_message(embed=self.embeds[self.index], view=self)

    @disnake.ui.button(emoji="🔽", style=disnake.ButtonStyle.green)
    async def download(
        self, button: disnake.ui.Button, inter: disnake.MessageInteraction
    ):
        current_embed = self.embeds[self.index]
        game_id = next(
            (field.value for field in current_embed.fields if field.name == "Game ID"),
            None,
        )
        if game_id is None:
            return await inter.response.send_message("Unable to find the game ID.")
        asset_link = get_asset_url(game_id, BayesAssetType.ROFL_REPLAY)
        await inter.response.send_message(asset_link)


# Create pages function
def create_pages(games: BayesMatch) -> list:
    pages = []
    for game in games.games:
        if game.game_finished and game.rofl_available:
            if game.league is None or game.tournament is None:
                embed = disnake.Embed(title=game.team_string)
            else:
                embed = disnake.Embed(
                    title=game.team_string,
                    description=f"{game.league} | {game.tournament}",
                )
            embed.add_field(name="Lobby Name", value=game.game_name or "-")
            embed.add_field(name="Start Time", value=f"<t:{game.started_at}:F>")
            embed.add_field(name="Patch", value=game.patch or "unknown")
            embed.add_field(name="Game ID", value=game.platform_id or "ERROR")
            embed.add_field(name="Page", value=games.page_string)

            embed.set_author(
                name="Lord Grompulus Kevin Ribbiton of Croaksworth Bot",
                icon_url="https://static.wikia.nocookie.net/leagueoflegends/images/8/8b/Gromp_Render.png",
            )
            embed.set_footer(
                text=f"Generated with data from Bayes Esports by Gromp Bot • {datetime.now().strftime('%b %d %Y • %H:%M')} "
            )
            pages.append(embed)
    return pages


def get_tag_filter(inter, filter_tag: str) -> list:
    return [tag for tag, confidence in process.extract(filter_tag, tags, limit=25)]


# Event listener
@bot.event
async def on_ready():
    await bot.change_presence(
        status=disnake.Status.online,
        activity=disnake.Game("with data"),
    )
    logging.info(f"We have logged in as {bot.user}")
    print(f"We have logged in as {bot.user}")


# Slash command for matches
@bot.slash_command(guild_ids=guild_ids)
async def match(
    inter,
    game_type: BayesGameType = commands.Param(
        default=BayesGameType.ESPORTS.value, description="Game Type to filter by."
    ),
    team_name: str = commands.Param(
        default=None,
        description="Team name to filter by. For scrims this is the enemy team's name.",
        autocomplete=get_team_names,
    ),
    tags: str = commands.Param(
        default=None,
        description="Tournament/tag to filter by",
        autocomplete=get_tag_filter,
    ),
    number_of_games: int = commands.Param(
        default=25,
        description="Number of games to return (max 100)",
    ),
    page: int = commands.Param(default=1, description="Page number"),
):
    querystring = {
        "types": game_type,
        "size": number_of_games,
        "page": page - 1,
    }
    if team_name:
        querystring["teamName"] = team_name
    if tags:
        querystring["tags"] = [tags]
    print(querystring)
    games = get_matches(querystring)
    if games is None or not games.games_available:
        await inter.response.send_message(
            "No matches found. Check your parameters and try again."
        )
        return

    pages = create_pages(games)
    if not pages:
        await inter.response.send_message(
            "No replays available. Please try again later."
        )
        return

    await inter.response.send_message(embed=pages[0], view=SeriesViewer(pages))


# Slash command for downloading
@bot.slash_command(guild_ids=guild_ids)
async def download(ctx, game_id: str):
    await ctx.respond(get_asset_url(game_id, BayesAssetType.ROFL_REPLAY))


# Run the bot
bot.run(discord_token)
