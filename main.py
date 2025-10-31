import discord
from discord import app_commands
from discord.ext import commands
import asyncio
from datetime import datetime, timedelta

# ========= CONFIG =========
TOKEN = "YOUR_BOT_TOKEN"
GUILD_ID = 123456789012345678  # your server id
VOUCH_CHANNEL_ID = 123456789012345678  # your vouch channel id

# 🎨 THEMES
THEMES = {
    "nebula": "https://your-download-link.com/nebula.zip",
    "euphoria": "https://your-download-link.com/euphoria.zip",
    "enigma": "https://your-download-link.com/enigma.zip"
}
# ==========================

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)
tree = bot.tree

cooldowns = {}       # user_id: datetime
banned_users = {}    # user_id: unban_time


@bot.event
async def on_ready():
    await tree.sync(guild=discord.Object(id=GUILD_ID))
    print(f"✅ Logged in as {bot.user}")
    await bot.change_presence(activity=discord.Game("Free Themes | UnicHosting On Top 🔥"))


@bot.event
async def on_guild_join(guild):
    # Restrict bot to your server only
    if guild.id != GUILD_ID:
        await guild.leave()


@tree.command(name="deploy", description="Deploy a free UnicHosting theme!", guild=discord.Object(id=GUILD_ID))
@app_commands.describe(theme="Choose which theme to deploy (nebula, euphoria, enigma)")
async def deploy(interaction: discord.Interaction, theme: str):
    user = interaction.user

    # Temp ban check
    if user.id in banned_users:
        if datetime.utcnow() < banned_users[user.id]:
            remaining = banned_users[user.id] - datetime.utcnow()
            await interaction.response.send_message(
                f"🚫 You’re temp banned from deploying for {int(remaining.total_seconds() // 60)} minutes.",
                ephemeral=True
            )
            return
        else:
            del banned_users[user.id]

    # Invalid theme check
    if theme.lower() not in THEMES:
        await interaction.response.send_message(
            f"❌ Invalid theme name! Choose one of: **Nebula**, **Euphoria**, or **Enigma**",
            ephemeral=True
        )
        return

    # Discord status check
    if not user.activity or "UnicHosting" not in str(user.activity):
        await interaction.response.send_message(
            "⚠️ You must add `UnicHosting On Top!` and your invite link in your **Discord status** to deploy a theme.",
            ephemeral=True
        )
        return

    # Cooldown check
    if user.id in cooldowns and datetime.utcnow() < cooldowns[user.id]:
        remaining = cooldowns[user.id] - datetime.utcnow()
        await interaction.response.send_message(
            f"⏳ You can deploy again in {int(remaining.total_seconds() // 3600)} hour(s).",
            ephemeral=True
        )
        return

    # Try sending theme to DM
    try:
        await user.send(
            f"🎉 **Here’s your FREE Theme!**\n\n"
            f"✨ **Theme:** {theme.title()}\n"
            f"📦 **Download:** {THEMES[theme.lower()]}\n\n"
            f"💬 Please vouch in <#{VOUCH_CHANNEL_ID}> within **10 minutes** or you’ll be temp-banned for 1 day!\n\n"
            f"❤️ *Thanks for using UnicHosting!*"
        )
        await interaction.response.send_message("✅ Check your DMs for the theme link!", ephemeral=True)
    except:
        await interaction.response.send_message("❌ I couldn’t DM you! Please enable DMs and try again.", ephemeral=True)
        return

    # Wait 10 min for vouch
    await asyncio.sleep(600)
    channel = interaction.guild.get_channel(VOUCH_CHANNEL_ID)
    messages = [msg async for msg in channel.history(limit=100)]
    vouched = any(str(user.id) in msg.content for msg in messages)

    if not vouched:
        banned_users[user.id] = datetime.utcnow() + timedelta(days=1)
        try:
            await user.send("⛔ You didn’t vouch in time! You are banned from deploying for **1 day.**")
        except:
            pass

    # 2-hour cooldown
    cooldowns[user.id] = datetime.utcnow() + timedelta(hours=2)


@tree.command(name="themes", description="View available UnicHosting themes", guild=discord.Object(id=GUILD_ID))
async def themes(interaction: discord.Interaction):
    embed = discord.Embed(
        title="🎨 Available Free Themes",
        description=(
            "🪐 **Nebula** – Modern & Clean look\n"
            "💫 **Euphoria** – Sleek and Premium feel\n"
            "🔮 **Enigma** – Dark and Mysterious\n\n"
            "Use `/deploy <theme>` to claim your free one!"
        ),
        color=0x5865F2
    )
    embed.set_footer(text="UnicHosting On Top 🔥")
    await interaction.response.send_message(embed=embed, ephemeral=True)


bot.run(TOKEN)

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
