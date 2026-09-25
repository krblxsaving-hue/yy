import discord
from discord.ext import commands
import datetime

intents = discord.Intents.default()
intents.message_content = True
intents.members = True  # required for ban/kick/timeout
bot = commands.Bot(command_prefix=",", intents=intents, help_command=None)

# Stores the last deleted message per channel (for ,s)
snipes = {}

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")

@bot.event
async def on_message_delete(message):
    snipes[message.channel.id] = {
        "content": message.content,
        "author": message.author,
        "avatar": message.author.display_avatar.url
    }

# ---------- HELP ----------
@bot.command()
async def help(ctx):
    embed = discord.Embed(title="Command List", color=discord.Color.blurple())
    embed.add_field(name=",ping", value="Check if the bot is responsive", inline=False)
    embed.add_field(name=",info", value="Server info", inline=False)
    embed.add_field(name=",kick @member <reason>", value="Kick a member", inline=False)
    embed.add_field(name=",ban @member <reason>", value="Ban a member", inline=False)
    embed.add_field(name=",unban <user_id>", value="Unban a user", inline=False)
    embed.add_field(name=",to @member <minutes>", value="Timeout a member", inline=False)
    embed.add_field(name=",unto @member", value="Remove a member's timeout", inline=False)
    embed.add_field(name=",purge <amount>", value="Delete a number of messages", inline=False)
    embed.add_field(name=",renew", value="Recreate this channel (clears all messages)", inline=False)
    embed.add_field(name=",s", value="Show the last deleted message", inline=False)
    await ctx.send(embed=embed)

# ---------- MODERATION ----------
@bot.command()
@commands.has_permissions(kick_members=True)
async def kick(ctx, member: discord.Member, *, reason="No reason provided"):
    await member.kick(reason=reason)
    await ctx.send(f"{member.mention} has been kicked. Reason: {reason}")

@bot.command()
@commands.has_permissions(ban_members=True)
async def ban(ctx, member: discord.Member, *, reason="No reason provided"):
    await member.ban(reason=reason)
    await ctx.send(f"{member.mention} has been banned. Reason: {reason}")

@bot.command()
@commands.has_permissions(ban_members=True)
async def unban(ctx, user_id: int):
    try:
        user = await bot.fetch_user(user_id)
        await ctx.guild.unban(user)
        await ctx.send(f"{user} has been unbanned.")
    except discord.NotFound:
        await ctx.send("No banned user found with that ID.")

@bot.command()
@commands.has_permissions(moderate_members=True)
async def to(ctx, member: discord.Member, minutes: int = 5, *, reason="No reason provided"):
    duration = datetime.timedelta(minutes=minutes)
    await member.timeout(duration, reason=reason)
    await ctx.send(f"{member.mention} has been timed out for {minutes} minute(s). Reason: {reason}")

@bot.command()
@commands.has_permissions(moderate_members=True)
async def unto(ctx, member: discord.Member):
    await member.timeout(None)
    await ctx.send(f"{member.mention}'s timeout has been removed.")

@bot.command(aliases=["clear"])
@commands.has_permissions(manage_messages=True)
async def purge(ctx, amount: int = 10):
    deleted = await ctx.channel.purge(limit=amount + 1)  # +1 to include the command message
    msg = await ctx.send(f"Deleted {len(deleted) - 1} messages.")
    await msg.delete(delay=3)

@bot.command()
@commands.has_permissions(manage_channels=True)
async def renew(ctx):
    channel = ctx.channel
    new_channel = await channel.clone(reason="Channel renewed")
    await new_channel.move(beginning=False, offset=0, before=channel)
    await channel.delete(reason="Channel renewed")
    await new_channel.send("This channel has been renewed.")

# ---------- SNIPE ----------
@bot.command()
async def s(ctx):
    data = snipes.get(ctx.channel.id)
    if not data:
        await ctx.send("Nothing to snipe here.")
        return
    embed = discord.Embed(description=data["content"], color=discord.Color.red())
    embed.set_author(name=data["author"], icon_url=data["avatar"])
    await ctx.send(embed=embed)

# ---------- OTHER ----------
@bot.command()
async def ping(ctx):
    await ctx.send(f"Pong! {round(bot.latency * 1000)}ms")

@bot.command()
async def info(ctx):
    await ctx.send(f"Server: {ctx.guild.name}\nMembers: {ctx.guild.member_count}")

import os

bot.run(os.getenv("DISCORD_TOKEN"))
