import os
import discord
from discord.ext import commands, tasks
import datetime
from keep_alive import keep_alive  # Importing your keep_alive function

TOKEN = os.environ['TOKEN']
POLL_CHANNEL_NAME = "qotd"
SUGGESTIONS_CHANNEL_NAME = "suggestions"

intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.members = True

bot = commands.Bot(command_prefix='!', intents=intents)

last_sent_date = None  # Prevents double posting on the same day

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name}')
    daily_poll.start()

def read_index():
    try:
        with open("index.txt", "r") as f:
            return int(f.read().strip())
    except FileNotFoundError:
        return 0

def write_index(index):
    with open("index.txt", "w") as f:
        f.write(str(index))

def read_polls():
    try:
        with open("polls.txt", "r", encoding="utf-8") as f:
            return [line.strip() for line in f if line.strip()]
    except FileNotFoundError:
        return []

def append_poll(poll_text):
    with open("polls.txt", "a", encoding="utf-8") as f:
        f.write(poll_text + "\n")

@tasks.loop(minutes=1)
async def daily_poll():
    global last_sent_date
    await bot.wait_until_ready()

    now = datetime.datetime.now(datetime.timezone.utc)
    current_time = now.time()
    current_date = now.date()

    if current_time.hour == 15 and current_time.minute == 0:
        if last_sent_date != current_date:
            guild = bot.guilds[0]
            channel = discord.utils.get(guild.text_channels, name=POLL_CHANNEL_NAME)
            if not channel:
                print("Poll channel not found.")
                return

            index = read_index()
            polls = read_polls()

            if index < len(polls):
                message = await channel.send(f"@here **Would You Rather:**\n{polls[index]}")
                await message.add_reaction("1️⃣")
                await message.add_reaction("2️⃣")
                write_index(index + 1)
            else:
                await channel.send("@here **No more polls in the list. Please add more with `!add` command.**")

            last_sent_date = current_date

@bot.command()
async def test(ctx):
    polls = read_polls()
    index = read_index()
    if polls and 0 <= index < len(polls):
        message = await ctx.send(f"@here **Would You Rather:**\n{polls[index]}")
        await message.add_reaction("1️⃣")
        await message.add_reaction("2️⃣")
    else:
        await ctx.send("Poll not found at current index.")

@bot.command()
async def request(ctx, *, options):
    channel = discord.utils.get(ctx.guild.text_channels, name=SUGGESTIONS_CHANNEL_NAME)
    if channel:
        await channel.send(f"New suggestion from {ctx.author.mention}: {options}")
        await ctx.send("Suggestion submitted!")
    else:
        await ctx.send("Suggestions channel not found.")

@bot.command()
@commands.has_permissions(administrator=True)
async def add(ctx, *, poll_text):
    append_poll(poll_text)
    await ctx.send("Poll added successfully!")

@add.error
async def add_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send("You need to be an administrator to use this command.")

@bot.command()
@commands.has_permissions(administrator=True)
async def setindex(ctx, number: int):
    write_index(number)
    await ctx.send(f"Poll index set to {number}.")

@setindex.error
async def setindex_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send("You need to be an administrator to use this command.")
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send("You need to provide a number. Usage: `!setindex <number>`")
    elif isinstance(error, commands.BadArgument):
        await ctx.send("Invalid number format. Please enter a valid integer.")

@bot.command()
async def list(ctx):
    polls = read_polls()
    if polls:
        formatted = "\n".join([f"{i}: {p}" for i, p in enumerate(polls)])
        await ctx.send(f"**Poll List:**\n```\n{formatted}\n```")
    else:
        await ctx.send("Poll list is empty.")

# Add a simple web server to keep the Replit project alive
from flask import Flask
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is running."

# Keep the Replit project alive
keep_alive()  # This ensures the Flask server starts

# Run the bot
bot.run(TOKEN)  # This runs the bot after the web server starts
