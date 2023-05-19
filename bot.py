from bayes_helper import (
    get_tags,
    get_asset_link,
    BayesGame,
    get_matches,
    get_icons,
    BayesScrim,
    get_scrim_games,
)
import discord
from discord.ext import commands
import os
from discord.ext.pages import Paginator, Page
from fuzzywuzzy import process
from typing import Optional
import logging
from datetime import datetime

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(),
    ],
)

if os.path.exists(".env"):
    from dotenv import load_dotenv

    load_dotenv()

discord_token = os.environ.get("DISCORD_TOKEN")
if discord_token is None:
    raise ValueError("Discord token not set.")
guilds_allowed = os.environ.get("GUILDS_ALLOWED")
if guilds_allowed is None:
    guild_ids = []
else:
    guild_ids = list(map(int, guilds_allowed.split(",")))

bot = discord.Bot(help_command=commands.MinimalHelpCommand())

TAGS = get_tags()
ICONS = get_icons()


class DownloadButton(discord.ui.Button):
    def __init__(self, *args, **kwargs):
        super().__init__(label="Download Replay", *args, **kwargs)

    async def callback(self, interaction: discord.Interaction):
        current_embed = interaction.message.embeds[0]
        game_id = next(
            (page.value for page in current_embed.fields if page.name == "Game ID"),
            None,
        )
        if game_id is None:
            return await interaction.response.send_message(
                "Unable to find the game ID."
            )
        asset_link = get_asset_link(game_id)
        await interaction.response.send_message(asset_link)


def create_pages(matches: list[BayesGame] | list[BayesScrim]) -> list:
    pages = []
    for game in matches:
        if game.game_finished and game.rofl_available:
            if isinstance(game, BayesScrim):
                embed = discord.Embed(title=game.teams)
            elif isinstance(game, BayesGame):
                if game.blockName is None and game.subBlockName is None:
                    embed = discord.Embed(title=game.teams)
                else:
                    embed = discord.Embed(
                        title=game.teams,
                        description=f"{game.blockName} | {game.subBlockName}",
                    )
                icon_tag = max(
                    [process.extractOne(tag, list(ICONS.keys())) for tag in game.tags],
                    key=lambda x: x[1],
                )
                if icon_tag is not None and icon_tag[1] >= 85:
                    embed.set_thumbnail(url=ICONS[icon_tag[0]])
                embed.add_field(
                    name="Tournament", value=max(game.tags, key=len), inline=False
                )
            else:
                raise TypeError("Game type not supported")
            embed.add_field(name="Lobby Name", value=game.game_name, inline=True)
            embed.add_field(
                name="Game time", value=f"<t:{game.local_timestring}:F>", inline=True
            )

            embed.add_field(name="Game ID", value=game.game_id)
            embed.set_author(
                name="Lord Grompulus Kevin Ribbiton of Croaksworth Bot",
                icon_url="https://static.wikia.nocookie.net/leagueoflegends/images/8/8b/Gromp_Render.png",
            )

            embed.set_footer(
                text=f"Generated with data from Bayes Esports by Gromp Bot • {datetime.now().strftime('%b %d %Y • %H:%M')} "
            )

            pages.append(
                Page(
                    embeds=[embed],
                )
            )
    return pages


@bot.event
async def on_ready():
    await bot.change_presence(
        status=discord.Status.online,
        activity=discord.Game("with data"),
    )
    logging.info(f"We have logged in as {bot.user}")
    print(f"We have logged in as {bot.user}")


@bot.slash_command(guild_ids=guild_ids)
async def tournaments(ctx, search: Optional[str]):
    if search is None:
        tags = TAGS[:10]
    else:
        possible_tags = process.extract(search, TAGS, limit=5)
        tags = (
            [tournament[0] for tournament in possible_tags]
            if possible_tags
            else ["No matching Tournaments were found"]
        )
    await ctx.respond("\n".join(tags))


@bot.slash_command(guild_ids=guild_ids)
async def match(
    ctx, tournament: Optional[str], team1: Optional[str], team2: Optional[str]
):
    querystring = {"team1": team1, "team2": team2}
    if tournament is not None:
        most_likely_tournament = process.extractOne(tournament, TAGS)
        querystring["tags"] = (
            most_likely_tournament[0] if most_likely_tournament else None
        )
    pages = create_pages([BayesGame(game) for game in get_matches(querystring)])
    if len(pages) == 0:
        await ctx.respond("No matches found")
        return
    view = discord.ui.View()
    view.add_item(DownloadButton())
    paginator = Paginator(pages=pages, custom_view=view)
    await paginator.respond(ctx.interaction)


@bot.slash_command(guild_ids=guild_ids)
async def scrim(ctx, lobby_name: Optional[str], enemy_team: Optional[str]):
    querystring = {"gameName": lobby_name} if lobby_name else {}
    if enemy_team is not None:
        querystring["teamCodes"] = enemy_team
    pages = create_pages([BayesScrim(game) for game in get_scrim_games(querystring)])
    view = discord.ui.View()
    view.add_item(DownloadButton())
    paginator = Paginator(pages=pages, custom_view=view)
    await paginator.respond(ctx.interaction, ephemeral=len(pages) == 0)


@bot.slash_command(guild_ids=guild_ids)
async def download(ctx, game_id: str):
    await ctx.respond(get_asset_link(game_id))


bot.run(discord_token)
