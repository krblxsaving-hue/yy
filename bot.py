import discord
from discord.ext import commands
import datetime
import os
from flask import Flask
from threading import Thread

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(
    command_prefix=",",
    intents=intents,
    help_command=None
)

WHITE = discord.Color.from_rgb(255, 255, 255)

# Stores the last deleted message per channel
snipes = {}


@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")


@bot.event
async def on_message_delete(message):
    if message.author.bot:
        return

    snipes[message.channel.id] = {
        "content": message.content,
        "author": message.author,
        "avatar": message.author.display_avatar.url
    }


# ---------- HELP ----------

@bot.command()
async def help(ctx):
    embed = discord.Embed(
        title="Command List",
        color=WHITE
    )

    embed.add_field(
        name=",ping",
        value="Check if the bot is responsive",
        inline=False
    )

    embed.add_field(
        name=",info",
        value="Server info",
        inline=False
    )

    embed.add_field(
        name=",kick @member <reason>",
        value="Kick a member",
        inline=False
    )

    embed.add_field(
        name=",ban @member <reason>",
        value="Ban a member",
        inline=False
    )

    embed.add_field(
        name=",unban <user_id>",
        value="Unban a user",
        inline=False
    )

    embed.add_field(
        name=",to @member <minutes>",
        value="Timeout a member",
        inline=False
    )

    embed.add_field(
        name=",unto @member",
        value="Remove a member's timeout",
        inline=False
    )

    embed.add_field(
        name=",purge <amount>",
        value="Delete a number of messages",
        inline=False
    )

    embed.add_field(
        name=",renew",
        value="Recreate this channel",
        inline=False
    )

    embed.add_field(
        name=",hide",
        value="Hide this channel from everyone",
        inline=False
    )

    embed.add_field(
        name=",hideall",
        value="Hide every channel from everyone",
        inline=False
    )

    embed.add_field(
        name=",unhide",
        value="Unhide this channel",
        inline=False
    )

    embed.add_field(
        name=",unhideall",
        value="Unhide every channel from everyone",
        inline=False
    )

    embed.add_field(
        name=",s",
        value="Show the last deleted message",
        inline=False
    )

    await ctx.send(embed=embed)


# ---------- MODERATION ----------

@bot.command()
@commands.has_permissions(kick_members=True)
async def kick(ctx, member: discord.Member, *, reason="No reason provided"):
    await member.kick(reason=reason)

    await ctx.send(
        f"{member.mention} has been kicked. Reason: {reason}"
    )


@bot.command()
@commands.has_permissions(ban_members=True)
async def ban(ctx, member: discord.Member, *, reason="No reason provided"):
    await member.ban(reason=reason)

    await ctx.send(
        f"{member.mention} has been banned. Reason: {reason}"
    )


@bot.command()
@commands.has_permissions(ban_members=True)
async def unban(ctx, user_id: int):
    try:
        user = await bot.fetch_user(user_id)
        await ctx.guild.unban(user)

        await ctx.send(
            f"{user} has been unbanned."
        )

    except discord.NotFound:
        await ctx.send(
            "No banned user found with that ID."
        )


@bot.command()
@commands.has_permissions(moderate_members=True)
async def to(
    ctx,
    member: discord.Member,
    minutes: int = 5,
    *,
    reason="No reason provided"
):
    if minutes <= 0:
        await ctx.send(
            "The duration must be greater than 0 minutes."
        )
        return

    duration = datetime.timedelta(minutes=minutes)

    await member.timeout(
        duration,
        reason=reason
    )

    await ctx.send(
        f"{member.mention} has been timed out for "
        f"{minutes} minute(s). Reason: {reason}"
    )


@bot.command()
@commands.has_permissions(moderate_members=True)
async def unto(ctx, member: discord.Member):
    await member.timeout(None)

    await ctx.send(
        f"{member.mention}'s timeout has been removed."
    )


@bot.command(aliases=["clear"])
@commands.has_permissions(manage_messages=True)
async def purge(ctx, amount: int = 10):
    deleted = await ctx.channel.purge(
        limit=amount + 1
    )

    msg = await ctx.send(
        f"Deleted {len(deleted) - 1} messages."
    )

    await msg.delete(delay=3)


# ---------- RENEW ----------

@bot.command()
@commands.has_permissions(manage_channels=True)
async def renew(ctx):
    channel = ctx.channel

    new_channel = await channel.clone(
        reason="Channel renewed"
    )

    await new_channel.move(
        before=channel
    )

    await channel.delete(
        reason="Channel renewed"
    )

    await new_channel.send(
        "This channel has been renewed."
    )


# ---------- HIDE ----------

@bot.command()
@commands.has_permissions(administrator=True)
async def hide(ctx):
    await ctx.channel.set_permissions(
        ctx.guild.default_role,
        view_channel=False
    )

    await ctx.send(
        "This channel is now hidden."
    )


@bot.command()
@commands.has_permissions(administrator=True)
async def hideall(ctx):
    count = 0

    for channel in ctx.guild.channels:
        # Keep the command channel accessible
        if channel.id == ctx.channel.id:
            continue

        try:
            await channel.set_permissions(
                ctx.guild.default_role,
                view_channel=False
            )

            count += 1

        except Exception as e:
            print(
                f"Failed to hide {channel.name}: {e}"
            )

    await ctx.send(
        f"{count} channels have been hidden."
    )


# ---------- UNHIDE ----------

@bot.command()
@commands.has_permissions(administrator=True)
async def unhide(ctx):
    await ctx.channel.set_permissions(
        ctx.guild.default_role,
        view_channel=True
    )

    await ctx.send(
        "This channel is now visible."
    )


@bot.command()
@commands.has_permissions(administrator=True)
async def unhideall(ctx):
    count = 0

    for channel in ctx.guild.channels:
        try:
            await channel.set_permissions(
                ctx.guild.default_role,
                view_channel=True
            )

            count += 1

        except Exception as e:
            print(
                f"Failed to unhide {channel.name}: {e}"
            )

    await ctx.send(
        f"{count} channels have been unhidden."
    )


# ---------- SNIPE ----------

@bot.command()
async def s(ctx):
    data = snipes.get(ctx.channel.id)

    if not data:
        await ctx.send(
            "Nothing to snipe here."
        )
        return

    content = data["content"]

    if not content:
        content = "No text content."

    embed = discord.Embed(
        description=content,
        color=WHITE
    )

    embed.set_author(
        name=data["author"],
        icon_url=data["avatar"]
    )

    await ctx.send(
        embed=embed
    )


# ---------- OTHER ----------

@bot.command()
async def ping(ctx):
    await ctx.send(
        f"Pong! {round(bot.latency * 1000)}ms"
    )


@bot.command()
async def info(ctx):
    await ctx.send(
        f"Server: {ctx.guild.name}\n"
        f"Members: {ctx.guild.member_count}"
    )


# ---------- ERROR HANDLING ----------

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        return

    if isinstance(error, commands.MissingPermissions):
        await ctx.send(
            "You do not have permission to use this command."
        )
        return

    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send(
            "A required argument is missing."
        )
        return

    if isinstance(error, commands.BadArgument):
        await ctx.send(
            "Invalid argument."
        )
        return

    print(f"Command error: {error}")


# ---------- KEEP ALIVE ----------

app = Flask(__name__)


@app.route("/")
def home():
    return "YY Bot is online!"


def run():
    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 8080))
    )


def keep_alive():
    thread = Thread(
        target=run,
        daemon=True
    )
    thread.start()


# ---------- START ----------

keep_alive()

TOKEN = os.getenv("DISCORD_TOKEN")

if not TOKEN:
    raise RuntimeError(
        "DISCORD_TOKEN environment variable is missing."
    )

bot.run(TOKEN)
