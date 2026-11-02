import os
import datetime
import discord
from discord.ext import commands
from flask import Flask
from threading import Thread

# --- 1. FLASK KEEP-ALIVE (Render дээр 24/7 сэрээх веб сервер) ---
app = Flask('')

@app.route('/')
def home():
    return "Bot 24/7 амжилттай ажиллаж байна!"

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()

# --- 2. DISCORD BOT SETUP ---
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f'✅ {bot.user} аюулгүй байдлыг хамгаалан 24/7 ажиллахад бэлэн боллоо!')

# --- 3. AUTO-ROLE (Шинэ гишүүн орж ирэхэд роль өгөх) ---
@bot.event
async def on_member_join(member):
    ROLE_ID = 123456789012345678  # Өөрийн серверийн шинэ гишүүн роль ID-г энд бичнэ
    role = member.guild.get_role(ROLE_ID)
    if role:
        try:
            await member.add_roles(role)
            print(f"Шинэ гишүүн {member.name}-д роль амжилттай олгогдлоо.")
        except Exception as e:
            print(f"Роль олгоход алдаа гарлаа: {e}")

# --- 4. SECURITY & AUTOMOD SYSTEM (Шүүлтүүрүүд) ---
@bot.event
async def on_message(message):
    if message.author.bot:
        return

    content = message.content.lower()

    # A. Серверийн линк хориглох (Anti-Invite Link)
    if "discord.gg/" in content or "discord.com/invite/" in content:
        try:
            await message.delete()
            timeout_duration = datetime.timedelta(minutes=5)
            await message.author.timeout(timeout_duration, reason="Серверийн линк явуулсан")
            
            warn = await message.channel.send(
                f"{message.author.mention}, сервер дээр линк (invite link) явуулах хориотой! **5 минут** timeout өглөө."
            )
            await warn.delete(delay=7)
            return
        except Exception as e:
            print(f"Link filter алдаа: {e}")

    # B. Хэт олон хүн tag хийхээс хамгаалах (Anti-Mass Mention)
    if len(message.mentions) >= 5 or message.mention_everyone:
        try:
            await message.delete()
            timeout_duration = datetime.timedelta(minutes=10)
            await message.author.timeout(timeout_duration, reason="Mention Spam")
            
            warn = await message.channel.send(
                f"{message.author.mention}, хэт олон хүн tag хийсэн тул **10 минут** timeout өглөө!"
            )
            await warn.delete(delay=6)
            return
        except Exception as e:
            print(f"Mention filter алдаа: {e}")

    # C. Хориотой үгс болон доромжлол шүүх (Anti-Toxic / Bad Words)
    toxic_words = ["хараал1", "муухай_үг", "доромжлох_үг"]  # Хориглох үгсээ энд нэмнэ
    if any(word in content for word in toxic_words):
        try:
            await message.delete()
            timeout_duration = datetime.timedelta(minutes=2)
            await message.author.timeout(timeout_duration, reason="Бусдыг доромжилсон / Зохисгүй үг хэрэглэсэн")
            
            warn = await message.channel.send(
                f"{message.author.mention}, бусдыг доромжлох болон зохисгүй үг хэрэглэхийг хориглоно! **2 минут** timeout өглөө."
            )
            await warn.delete(delay=6)
            return
        except Exception as e:
            print(f"Toxic filter алдаа: {e}")

    await bot.process_commands(message)

# --- 5. ADMIN COMMANDS ---
@bot.command()
@commands.has_permissions(manage_messages=True)
async def clear(ctx, amount: int = 10):
    await ctx.channel.purge(limit=amount + 1)
    msg = await ctx.send(f"🧹 **{amount}** мессеж устгагдлаа.")
    await msg.delete(delay=3)

@bot.command()
@commands.has_permissions(kick_members=True)
async def kick(ctx, member: discord.Member, *, reason="Шалтгаан тодорхойгүй"):
    await member.kick(reason=reason)
    msg = await ctx.send(f"👢 **{member.name}** серверээс хөөгдлөө. Шалтгаан: {reason}")
    await msg.delete(delay=5)

# --- 6. RUN SERVER & BOT ---
keep_alive()  # Flask веб серверийг цаана нь асаана

TOKEN = os.getenv("DISCORD_TOKEN")  # Render Environment Variable-аас токен уншина
bot.run(TOKEN)