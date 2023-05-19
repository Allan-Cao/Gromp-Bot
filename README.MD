# Gromp Bot

This is a Discord bot that serves League of Legends Esports replays directly to coaches and players. It uses the Bayes Esports API to retrieve data about tournaments and matches, and provides a simple interface for users to search for and download replays.

## Installation

To use this bot, you'll need to have Python **3.10** or higher installed on your system. You'll also need to install the required Python packages by running the following command:

```bash
pip install -r requirements.txt
```
    
## Environment Variables

You'll also need to set the following environment variables. You can do this by renaming .env.example to a file called .env in the root directory of the project and modifying the variables in the file.

`GUILDS_ALLOWED` specifies which servers the bot is allowed to take commands from. This should be a string that has comma-seperated server-IDs.

[(How to find your server ID)](https://support.discord.com/hc/en-us/articles/206346498-Where-can-I-find-my-User-Server-Message-ID-#:~:text=Obtaining%20Server%20IDs%20%2D%20Mobile%20App,ID%20to%20get%20the%20ID.)
## Usage

To use this bot, you'll need to invite it to your Discord server. You can do this by creating a new Discord application and adding a bot to it, then generating an invite link for the bot.

Once the bot is in your server, you can use the following commands:

- `/tournaments [search]`: Lists the top 10 tournaments, or the top 5 tournaments that match the given search query.
- `/match [tournament] [team1] [team2]`: Lists the matches for the given tournament and teams.
- `/scrim [lobby_name] [enemy_team]`: Lists the past 20 scrims for the given lobby name and/or enemy team.
- `/download [game_id]`: Provides a download link for the replay of the given game ID.
## License

This project is licensed under the [MIT](https://choosealicense.com/licenses/mit/) License. See the LICENSE file for more information.
## Credits

This bot was created by Allan Cao and uses the Bayes Esports API to retrieve data about tournaments, matches and replays.
