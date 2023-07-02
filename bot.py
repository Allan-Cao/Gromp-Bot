from bayes_helper import (
    get_tags,
    BayesGame,
    BayesGameType,
    get_asset_url,
    BayesAssetType,
    get_team_names,
    get_matches,
    get_icons,
)
import discord
from discord.ext import commands
from discord.commands import option
import os
from discord.ext.pages import Paginator, Page
from fuzzywuzzy import process
import logging
from datetime import datetime

# TODO Add actual logging to help with future debugging
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
        current_embed = interaction.message.embeds[0] # type: ignore
        game_id = next(
            (page.value for page in current_embed.fields if page.name == "Game ID"),
            None,
        )
        if game_id is None:
            return await interaction.response.send_message(
                "Unable to find the game ID."
            )
        asset_link = get_asset_url(game_id, BayesAssetType.ROFL_REPLAY)
        await interaction.response.send_message(asset_link)


def create_pages(
    games: list[BayesGame], games_found, total_pages, current_page
) -> list:
    # Non-programmers won't understand the difference between 0 and 1 indexing... so we lie to them
    page_string = (
        None
        if total_pages == 1
        else f"Page {current_page + 1}/{total_pages - 1} ({games_found} games found)"
    )
    pages = []
    for game in games:
        if game.game_finished and game.rofl_available:
            if game.league is None or game.tournament is None:
                embed = discord.Embed(title=game.team_string)
            else:
                embed = discord.Embed(
                    title=game.team_string,
                    description=f"{game.league} | {game.tournament}",
                )
            # Unknown if the V2 API will support this...
            # icon_tag = max(
            #     [process.extractOne(tag, list(ICONS.keys())) for tag in game.tags],
            #     key=lambda x: x[1],
            # )
            # if icon_tag is not None and icon_tag[1] >= 85:
            #     embed.set_thumbnail(url=ICONS[icon_tag[0]])
            # embed.add_field(
            #     name="Tournament", value=max(game.tags, key=len), inline=False
            # )
            embed.add_field(name="Lobby Name", value=game.game_name or "-")
            embed.add_field(name="Start Time", value=f"<t:{game.started_at}:F>")
            embed.add_field(name="Patch", value=game.patch or "unknown")

            embed.add_field(name="Game ID", value=game.platform_id or "ERROR")
            if page_string is not None:
                embed.add_field(name="Page", value=page_string)

            # This stuff should not be hard coded but it's fine for now...
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


# @bot.slash_command(guild_ids=guild_ids)
# async def tournaments(ctx, search: Optional[str]):
#     if search is None:
#         tags = TAGS[:10]
#     else:
#         possible_tags = process.extract(search, TAGS, limit=5)
#         tags = (
#             [tournament[0] for tournament in possible_tags]
#             if possible_tags
#             else ["No matching Tournaments were found"]
#         )
#     await ctx.respond("\n".join(tags))


@bot.slash_command(guild_ids=guild_ids)
@option(
    "game_type",
    description="Game Type (Esports match or Scrim)",
    choices=[BayesGameType.SCRIM, BayesGameType.ESPORTS],
    default=BayesGameType.ESPORTS,
)
@option(
    "team_name",
    description="Team name (will autocomplete). For scrims this is enemy team",
    autocomplete=get_team_names,
    required=False,
)
@option("tags", description="Tags to filter by: e.g. NACL Summer 2023", required=False)
@option(
    "number_of_games", description="Number of games to return (max 100)", required=False
)
@option("page", description="Page number (defaults to the first page)", required=False)
async def match(
    ctx,
    game_type: BayesGameType,
    team_name: str,
    tags: str,
    number_of_games: int = 10,
    page: int = 0,
):
    querystring = {
        "page": 0,
        "type": game_type.value,
        "tags": tags,
        "teamName": team_name,
        "size": number_of_games,
        "page": page,
    }
    games = get_matches(querystring)
    if games is None or games.get("totalCount" == 0):
        await ctx.respond("No matches found")
        return
    games_found = games.get("totalCount")
    total_pages = games.get("totalPages")
    current_page = games.get("pageNumber")

    pages = create_pages(
        [BayesGame(game) for game in games["items"]],
        games_found,
        total_pages,
        current_page,
    )
    view = discord.ui.View(timeout=None)
    view.add_item(DownloadButton())
    paginator = Paginator(pages=pages, custom_view=view)
    await paginator.respond(ctx.interaction)


@bot.slash_command(guild_ids=guild_ids)
async def download(ctx, game_id: str):
    await ctx.respond(get_asset_url(game_id, BayesAssetType.ROFL_REPLAY))


bot.run(discord_token)
