
# Gromp Bot

This is a Discord bot that serves League of Legends Esports replays directly to coaches and players. It uses the Bayes Esports API to retrieve data about tournaments and matches, and provides a simple interface for users to search for and download replays.

## Run Locally

To use this bot, you'll need to have Python **3.10** or higher installed on your system.

#### Clone the project

```bash
git clone https://github.com/Allan-Cao/Gromp-Bot.git
```

#### (Optional) Create a virtual environment

```bash
py -m virtualenv bot-env
```
Activate the newly created environment (Linux)
```bash
source /bot-env/bin/activate
```
Activate the newly created environment (Windows)
```bash
bot-env\bin\activate
```

#### Install dependencies

```bash
pip install -r requirements.txt
```


#### Environment Variables

You'll need to set the environment variables. You can do this by renaming .env.example to a file called .env in the root directory of the project and modifying the variables in the file or if you are deploying with docker, consider passing in env variables with the `--env-file` option.

`GUILDS_ALLOWED` specifies which servers the bot is allowed to take commands from which should be a string that has comma-seperated server-IDs.

[(How to find your server ID)](https://support.discord.com/hc/en-us/articles/206346498-Where-can-I-find-my-User-Server-Message-ID-#:~:text=Obtaining%20Server%20IDs%20%2D%20Mobile%20App,ID%20to%20get%20the%20ID.)

#### Start the bot

```bash
python bot.py
```


## Building and Deploying with Docker

To build and deploy the project using Docker, follow these steps:

1. Install Docker on your system if you haven't already. You can download Docker from the official website: https://www.docker.com/get-started

2. Clone the project repository to your local machine:
```bash
git clone https://github.com/Allan-Cao/Gromp-Bot.git
```

3. Navigate to the project directory:
```bash
cd Gromp-Bot
```

4. Build the Docker image using the following command:
```bash
docker build -t gromp-bot .
```
This command will build a Docker image with the name `gromp-bot`.

5. Run the Docker container using the following command:
```bash
docker run -d gromp-bot
```

6. Verify that the container is running using the following command:
```bash
docker ps
```

This command will show a list of running Docker containers. You should see a container with the name `gromp-bot`.

7. To stop the container, use the following command:
```bash
docker stop <docker-container-id>
```

This command will stop the container.

That's it! You've successfully built and deployed the project using Docker. You can now use the bot by inviting it to your Discord server and using its slash commands.
## License

This project is licensed under the [MIT](https://choosealicense.com/licenses/mit/) License. See the LICENSE file for more information.
