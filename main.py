import datetime
import discord
from discord import app_commands
from discord.ext import commands
import random
import shlex
import re
from dotenv import load_dotenv
import os

intents = discord.Intents.default()
intents.message_content = True
intents.reactions = True
intents.members = True

bot = commands.Bot(command_prefix='/', intents=intents)

# Dictionary to store names and their last chosen order per channel
names = {}
# Dictionary to store message IDs of registration messages per channel
registration_messages = {}
# Global cache for user display names
display_name_cache = {}


@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}!')
    MY_GUILD = discord.Object(id='688826072187404290')
    await bot.tree.sync(guild=MY_GUILD)
    await bot.tree.sync()

@bot.tree.command(name="register")
async def register(interaction: discord.Interaction):
    """Create an embed for users to react to and register their names."""
    embed = discord.Embed(title="Guild League Registration", description="React ✅ to be added to the name list.", color=0x00ff00)
    # Send the initial response with the embed
    await interaction.response.send_message(embed=embed)
    # Fetch the message object after it has been sent
    message = await interaction.original_response()
    await message.add_reaction("✅")
    channel_id = str(interaction.channel_id)
    names[channel_id] = []  # Initialize an empty list for names
    registration_messages[channel_id] = message.id


@bot.event
async def on_reaction_add(reaction, user):
    channel_id = str(reaction.message.channel.id)
    if user != bot.user and reaction.message.id == registration_messages.get(channel_id) and reaction.emoji == "✅":
        if user.id not in [uid for uid, _ in names.get(channel_id, [])]:
            names[channel_id].append((user.id, False))  # Add with not picked status
            await update_embed(reaction.message)

@bot.event
async def on_reaction_remove(reaction, user):
    channel_id = str(reaction.message.channel.id)
    if user != bot.user and reaction.message.id == registration_messages.get(channel_id) and reaction.emoji == "✅":
        if user.id in [uid for uid, _ in names.get(channel_id, [])]:
            names[channel_id] = [(uid, picked) for uid, picked in names[channel_id] if uid != user.id]
            await update_embed(reaction.message)

async def get_display_name(guild, user_id):
    """
    Retrieves the display name from cache or fetches from the guild if not cached.

    Args:
    guild (discord.Guild): The guild from which to fetch the member.
    user_id (int): The user ID for whom the display name is required.

    Returns:
    str: The display name of the user.
    """
    if user_id in display_name_cache:
        return display_name_cache[user_id]
    else:
        # Fetch the member and cache their display name
        member = await guild.fetch_member(user_id)
        display_name_cache[user_id] = member.display_name
        return member.display_name

async def update_embed(source):
    if isinstance(source, discord.Interaction):
        channel_id = str(source.channel_id)
        channel = source.channel
    elif isinstance(source, discord.Message):
        channel_id = str(source.channel.id)
        channel = source.channel
    else:
        return  # Exit if the source is not valid

    message_id = registration_messages.get(channel_id)
    if not message_id:
        return  # Exit if no registration message is found

    message = await channel.fetch_message(message_id)
    user_names = []

    for user_id, _ in names[channel_id]:
        display_name = await get_display_name(channel.guild, user_id)
        user_names.append(display_name)

    description = "\n".join(user_names)
    new_embed = discord.Embed(title="Guild League Registration", description=description, color=0x00ff00)
    new_embed.set_footer(text="React ✅ to be added to the name list.")
    await message.edit(embed=new_embed)

def generate_discord_timestamp():
    now = datetime.datetime.now(datetime.timezone.utc)
    if now.minute < 30:
        next_match = now.replace(second=0, microsecond=0, minute=30)
    else:
        next_match = now.replace(second=0, microsecond=0, minute=0) + datetime.timedelta(hours=1)
    return int(next_match.timestamp())


@bot.tree.command(name="choose")
@app_commands.describe(number='The number of participants to choose', mention='Will @ members if true', included_members='Members to always include')
async def choose(interaction: discord.Interaction, number: int, mention: bool = False, included_members: str = ''):
    await interaction.response.defer()
    channel_id = str(interaction.channel_id)
    if channel_id not in names:
        names[channel_id] = []

    # Extract IDs from provided mentions or plain text numbers
    included_member_ids = []
    for id_or_mention in shlex.split(included_members):
        match = re.match(r"<@!?(\d+)>", id_or_mention)
        if match:
            included_member_ids.append(int(match.group(1)))
        elif id_or_mention.isdigit():
            included_member_ids.append(int(id_or_mention))
        else:
            await interaction.followup.send(f"Invalid user identifier: {id_or_mention}. Please provide valid user IDs or mentions.", ephemeral=True)
            return

    # Register new members if they are not already registered
    for user_id in included_member_ids:
        if user_id not in [uid for uid, _ in names[channel_id]]:
            names[channel_id].append((user_id, False))

    # Update registration message after adding new members
    await update_embed(interaction)

    # Prepare for selection
    total_registered = len(names[channel_id])
    if number <= 0 or number > total_registered:
        await interaction.followup.send(
            f"The number of participants must be greater than zero and no greater than the total number of registered participants ({total_registered}).",
            ephemeral=True)
        return

    # Selection logic
    chosen = included_member_ids.copy()
    try_selecting_more_participants(chosen, number, names[channel_id])

    # Update picked status
    for user_id in chosen:
        for i, (uid, _) in enumerate(names[channel_id]):
            if uid == user_id:
                names[channel_id][i] = (uid, True)

    # Send final selection
    participants = [f"<@{user_id}>" for user_id in chosen]
    timestamp = generate_discord_timestamp()
    title = f"Guild League Team <t:{timestamp}:R>"
    description = "Here are the randomly selected members for participation:"

    embed = discord.Embed(title=title, description=description, color=0x1abc9c)
    embed.add_field(name="Participants", value="\n".join(participants), inline=False)

    await interaction.followup.send(content="\n".join(participants) if mention else "", embed=embed)

def try_selecting_more_participants(chosen, number, participants):
    while len(chosen) < number:
        available_members = [user_id for user_id, picked in participants if not picked and user_id not in chosen]
        if not available_members:  # All members are picked and we need more participants
            for i in range(len(participants)):
                participants[i] = (participants[i][0], False)  # Reset all to not picked
            available_members = [user_id for user_id, picked in participants if user_id not in chosen]
        to_add = min(len(available_members), number - len(chosen))
        chosen.extend(random.sample(available_members, to_add))



@bot.tree.command(name="add")
@app_commands.describe(member='Member to add')
async def add_participant(interaction: discord.Interaction, member: discord.Member):
    channel_id = str(interaction.channel_id)
    if channel_id not in names:
        names[channel_id] = []
    if member.id in [user_id for user_id, _ in names[channel_id]]:
        await interaction.response.send_message("This member is already registered.", ephemeral=True)
        return
    names[channel_id].append((member.id, False))
    await update_embed(interaction)
    await interaction.response.send_message(f"{member.display_name} has been added to the participant list.", ephemeral=True)

@bot.tree.command(name="delete")
@app_commands.describe(member='Member to remove')
async def delete_participant(interaction: discord.Interaction, member: discord.Member):
    channel_id = str(interaction.channel_id)
    if channel_id not in names or (member.id, True) not in names[channel_id] and (member.id, False) not in names[channel_id]:
        await interaction.response.send_message("This member is not registered.", ephemeral=True)
        return
    names[channel_id] = [(user_id, picked) for user_id, picked in names[channel_id] if user_id != member.id]
    await update_embed(interaction)
    await interaction.response.send_message(f"{member.display_name} has been removed from the participant list.", ephemeral=True)


@bot.tree.command(name="help")
async def help(interaction: discord.Interaction, visible: bool = False):
    # Create an embed object for a cleaner display
    embed = discord.Embed(title="Help - Guild League Bot", description="Learn how to use the bot commands.",
                          color=0x00ff00)

    # Adding fields for each command and its description
    embed.add_field(name="/register", value="Start a Guild League registration event in the current channel. React to the message to be included.",
                    inline=False)
    embed.add_field(name="/choose",
                    value="Selects a specified number of participants 'randomly'. Ensures everyone is picked once before repicking. Included members will always be picked first (e.g. shais). Mention will @ members for notifications. Usage: `/choose [number] [mention=True/False] [included_members]`",
                    inline=False)
    embed.add_field(name="/add", value="Adds a new participant to the current registration poll. Usage: `/add [member]`",
                    inline=False)
    embed.add_field(name="/delete", value="Removes a participant from the current registration poll. Usage: `/delete [member]`",
                    inline=False)
    embed.add_field(name="/help", value="Displays this help message.", inline=False)

    # Sending the embed to the channel where the help command was invoked
    await interaction.response.send_message(embed=embed, ephemeral=not visible)


def get_discord_bot_token():
    """
    Retrieves the Discord bot token from environment variables.

    Returns:
    str: The bot token.

    Raises:
    RuntimeError: If the token is not found in the environment variables.
    """
    # Load environment variables from .env file
    load_dotenv()
    token = os.getenv("DISCORD_BOT_TOKEN")
    if not token:
        raise RuntimeError("Discord bot token not found. Please set the DISCORD_BOT_TOKEN environment variable.")
    return token


def main():
    # Initialize the bot with the desired intents
    bot = commands.Bot(command_prefix='/', intents=intents)

    try:
        token = get_discord_bot_token()
    except RuntimeError as e:
        print(e)
        return

    # Run the bot with the loaded token
    bot.run(token)


if __name__ == "__main__":
    main()