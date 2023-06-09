# Use an official Python 3.11 runtime as a parent image
FROM python:3.11-alpine

# Install Git
RUN apk update && apk add git

# Set the working directory to /app
WORKDIR /app

# Clone the repository from GitHub
RUN git clone https://github.com/Allan-Cao/Gromp-Bot.git .

# Install any needed packages specified in requirements.txt
RUN pip install --trusted-host pypi.python.org -r requirements.txt

# Run the command to start the bot
CMD ["python", "bot.py"]
