# Guild League Team Maker

A Discord bot designed to organize fair team selection for guild events, leagues, and activities. The bot ensures that all participants get selected before anyone is chosen again, making team selection balanced and fair over time.

![Discord Bot](https://img.shields.io/badge/discord-bot-blue)
![Python](https://img.shields.io/badge/python-3.11-green)

## Features

- User-friendly registration system using reactions
- Fair "random" selection ensuring everyone gets a chance to participate
- Support for prioritizing specific members in team selection
- Ability to manually add or remove participants
- Discord timestamp integration for scheduling the next match
- Docker support for easy deployment

## Installation

### Prerequisites

- Python 3.11 or higher
- Discord Bot Token from [Discord Developer Portal](https://discord.com/developers/applications)
- Discord.py library and other dependencies

### Standard Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/guild-league-team-maker.git
   cd guild-league-team-maker
   ```

2. Create a virtual environment:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Create a `.env` file in the root directory with your Discord bot token:
   ```
   DISCORD_BOT_TOKEN=your_discord_bot_token_here
   ```

5. Run the bot:
   ```bash
   python main.py
   ```

### Docker Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/guild-league-team-maker.git
   cd guild-league-team-maker
   ```

2. Create a `.env` file with your Discord bot token:
   ```
   DISCORD_BOT_TOKEN=your_discord_bot_token_here
   ```

3. Build and run using Docker Compose:
   ```bash
   docker-compose up -d
   ```

## Usage

### Adding the Bot to Your Server

1. Create a Discord application and bot in the [Discord Developer Portal](https://discord.com/developers/applications)
2. Enable necessary intents (Message Content, Reactions, and Server Members)
3. Generate an invite URL with the proper permissions
4. Invite the bot to your server

### Setting Up Team Selection

1. Use `/register` in a channel to create a registration embed
2. Have users react with ✅ to join the participant pool
3. When ready, use `/choose [number]` to select team members
4. Optional parameters:
   - `mention=True` to automatically mention selected users
   - `included_members="@User1 @User2"` to always include specific members

## Commands

| Command | Description | Parameters |
|---------|-------------|------------|
| `/register` | Creates a registration embed for users to join | None |
| `/choose` | Selects random participants from the registration list | `number`: Number of participants to choose<br>`mention`: Whether to mention selected users<br>`included_members`: Members to always include |
| `/add` | Manually adds a user to the participant list | `member`: The Discord member to add |
| `/delete` | Removes a user from the participant list | `member`: The Discord member to remove |
| `/help` | Displays help information | `visible`: Whether to make response visible to everyone |

## Command Examples

- Create a registration embed:
  ```
  /register
  ```

- Select 5 random participants:
  ```
  /choose number:5
  ```

- Select 10 participants, including specific members:
  ```
  /choose number:10 included_members:"@User1 @User2"
  ```

- Select 8 participants and mention them:
  ```
  /choose number:8 mention:True
  ```

## How It Works

The bot maintains a list of participants for each channel, tracking who has been selected previously. When choosing team members:

1. It first includes any specified mandatory members
2. It then selects random participants who haven't been chosen yet
3. If more members are needed than are available, it resets everyone's selection status and continues selection
4. This ensures a fair rotation of participants over multiple team selections

## License

This project is licensed under MIT.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
