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
from dotenv import load_dotenv

logging.basicConfig(level=logging.INFO)

load_dotenv()

discord_token = os.environ.get("DISCORD_TOKEN")
if discord_token is None:
    raise ValueError("Discord token not set.")

bot = discord.Bot(help_command=commands.MinimalHelpCommand())

TAGS = get_tags()
ICONS = get_icons()


@bot.event
async def on_ready():
    await bot.change_presence(
        status=discord.Status.online,
        activity=discord.Game("with data"),
    )
    print(f"We have logged in as {bot.user}")


@bot.slash_command(guild_ids=[1074844803310833785, 1044416171736309940])
async def tournaments(ctx, search: Optional[str]) -> Optional[list]:
    if search is None:
        await ctx.respond("\n".join(TAGS[0:10]))
    else:
        possible_tags = process.extract(search, TAGS, limit=5)
        if len(possible_tags) == 0:
            await ctx.respond("No matching Tournaments were found")
        else:
            await ctx.respond(
                "\n".join([tournament[0] for tournament in possible_tags])
            )


def create_pages(matches: list[BayesGame] | list[BayesScrim]) -> list:
    pages = []
    for game in matches:
        if game.game_finished and game.rofl_available:
            if isinstance(game, BayesScrim):
                embed = discord.Embed(title=game.teams)
            elif isinstance(game, BayesGame):
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


@bot.slash_command(guild_ids=[1074844803310833785, 1044416171736309940])
async def match(
    ctx, tournament: Optional[str], team1: Optional[str], team2: Optional[str]
):
    querystring = {}
    if team1 is not None:
        querystring["team1"] = team1
    if team2 is not None:
        querystring["team2"] = team2
    if tournament is not None:
        most_likely_tournament = process.extractOne(tournament, TAGS)
        print(most_likely_tournament)
        querystring["tags"] = most_likely_tournament
    pages = create_pages([BayesGame(game) for game in get_matches(querystring)])
    if len(pages) > 0:
        paginator = Paginator(pages=pages)
        await paginator.respond(ctx.interaction, ephemeral=False)
    else:
        await ctx.respond("No matches were found.")


@bot.slash_command(guild_ids=[1074844803310833785, 1044416171736309940])
async def scrim(ctx, lobby_name: Optional[str], enemy_team: Optional[str]):
    querystring = {}
    if lobby_name is not None:
        querystring["gameName"] = lobby_name
    if enemy_team is not None:
        querystring["teamCodes"] = [enemy_team]
    pages = create_pages([BayesScrim(game) for game in get_scrim_games(querystring)])
    if len(pages) > 0:
        paginator = Paginator(pages=pages)
        await paginator.respond(ctx.interaction, ephemeral=False)
    else:
        await ctx.respond("No scrims were found.")


@bot.slash_command(guild_ids=[1074844803310833785, 1044416171736309940])
async def download(ctx, game_id: str):
    await ctx.respond(get_asset_link(game_id))


bot.run(discord_token)
