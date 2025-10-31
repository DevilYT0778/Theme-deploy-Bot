import discord
from discord import app_commands
from discord.ext import tasks
import asyncio
from datetime import datetime, timedelta
import os

# ===== CONFIG =====
TOKEN = os.getenv("DISCORD_TOKEN")
GUILD_ID = int(os.getenv("GUILD_ID", "0"))
VOUCH_CHANNEL_ID = int(os.getenv("VOUCH_CHANNEL_ID", "0"))

REQUIRED_STATUS_TEXT = "UnicHosting on Top!"
REQUIRED_INVITE = "discord.gg/yourinvite"   # change this!

VOUCH_TIME_MIN = 10
COOLDOWN_HOURS = 2
BAN_DURATION_HOURS = 24

THEMES = {
    "nebula": "https://example.com/themes/nebula.zip",
    "aurora": "https://example.com/themes/aurora.zip",
    "midnight": "https://example.com/themes/midnight.zip",
}

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
bot = discord.Client(intents=intents)
tree = app_commands.CommandTree(bot)

pending_vouches = {}
cooldowns = {}

# --- Leave other servers ---
@bot.event
async def on_guild_join(guild):
    if guild.id != GUILD_ID:
        await guild.leave()

# --- Startup ---
@bot.event
async def on_ready():
    guild = discord.Object(id=GUILD_ID)
    await tree.sync(guild=guild)
    await bot.change_presence(
        activity=discord.Game(name="Free Themes | UnicHosting On Top 🔥")
    )
    print(f"✅ Logged in as {bot.user}")
    print("🌐 Slash commands synced and status set!")

# --- Deploy command ---
@tree.command(name="deploy", description="Get a free UnicHosting theme!", guild=discord.Object(id=GUILD_ID))
@app_commands.describe(theme="Choose which theme to deploy")
async def deploy(interaction: discord.Interaction, theme: str):
    user = interaction.user
    member = interaction.guild.get_member(user.id)
    custom_status = None
    for activity in member.activities:
        if isinstance(activity, discord.CustomActivity) and activity.name:
            custom_status = activity.name.lower()
            break

    if not custom_status or REQUIRED_STATUS_TEXT.lower() not in custom_status or REQUIRED_INVITE.lower() not in custom_status:
        await interaction.response.send_message(
            f"⚠️ You must have `{REQUIRED_STATUS_TEXT}` and `{REQUIRED_INVITE}` in your **Discord status**!\n\n"
            "Example:\n`UnicHosting on Top! discord.gg/yourinvite`",
            ephemeral=True
        )
        return

    if theme.lower() not in THEMES:
        await interaction.response.send_message(f"❌ Invalid theme. Options: {', '.join(THEMES)}", ephemeral=True)
        return

    if user.id in cooldowns and datetime.utcnow() < cooldowns[user.id]:
        remaining = cooldowns[user.id] - datetime.utcnow()
        minutes = int(remaining.total_seconds() // 60)
        await interaction.response.send_message(f"⏳ Wait **{minutes} mins** before next deploy.", ephemeral=True)
        return

    link = THEMES[theme.lower()]
    theme_name = theme.title()
    embed = discord.Embed(
        title=f"🎁 Free {theme_name} Theme!",
        description=(
            f"✨ Here’s your **{theme_name}** theme from **UnicHosting!**\n\n"
            f"📦 [**Download Theme**]({link})\n\n"
            f"💬 You must **vouch** in <#{VOUCH_CHANNEL_ID}> within **10 minutes**\n"
            f"🚨 No vouch = **1-day ban** from theme deploy.\n\n"
            f"🖤 *– UnicHosting Team*"
        ),
        color=discord.Color.purple()
    )
    embed.set_footer(text="Nebula Deploy Bot ✨")

    try:
        await user.send(embed=embed)
    except discord.Forbidden:
        await interaction.response.send_message("⚠️ Enable DMs to get your theme!", ephemeral=True)
        return

    await interaction.response.send_message(f"✅ Sent **{theme_name}** theme to your DMs!", ephemeral=True)
    pending_vouches[user.id] = {"deadline": datetime.utcnow() + timedelta(minutes=VOUCH_TIME_MIN), "guild_id": interaction.guild_id}
    cooldowns[user.id] = datetime.utcnow() + timedelta(hours=COOLDOWN_HOURS)

# --- Vouch Detection ---
@bot.event
async def on_message(message):
    if message.author.bot or message.channel.id != VOUCH_CHANNEL_ID:
        return
    uid = message.author.id
    if uid in pending_vouches:
        content = message.content.lower()
        if any(word in content for word in ["vouch", "legit", "thanks", "theme"]):
            await message.add_reaction("✅")
            del pending_vouches[uid]

# --- Vouch Timeout ---
@tasks.loop(seconds=60)
async def check_vouches():
    now = datetime.utcnow()
    expired = [uid for uid, data in pending_vouches.items() if now >= data["deadline"]]
    for uid in expired:
        data = pending_vouches[uid]
        guild = bot.get_guild(data["guild_id"])
        if not guild:
            del pending_vouches[uid]
            continue
        member = guild.get_member(uid)
        if member:
            try:
                await guild.ban(member, reason="No vouch for theme.")
                vouch_ch = guild.get_channel(VOUCH_CHANNEL_ID)
                if vouch_ch:
                    await vouch_ch.send(f"🚫 {member.mention} didn’t vouch → temp banned for 1 day.")
                await asyncio.sleep(BAN_DURATION_HOURS * 3600)
                await guild.unban(discord.Object(id=uid))
            except Exception as e:
                print("Ban error:", e)
        del pending_vouches[uid]

bot.run(TOKEN)
