"""
Ship or Burn! Coop express — QA Discord Bot
Точка входа. Хостится на Discloud.
"""
import os
import logging
import discord
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
log = logging.getLogger("shipburn-bot")

INTENTS = discord.Intents.default()
INTENTS.message_content = True  # обязательно для чтения текста багрепортов
INTENTS.guilds = True
INTENTS.members = True  # нужно, чтобы резолвить Member при закрытии/переоткрытии тикетов

# SECURITY: бот никогда не должен резолвить @everyone/@here/роли в своих
# сообщениях, даже если такой текст случайно попадёт в ответ модели.
# Это защита от prompt-injection через баг-репорт (см. cogs/qa_agent.py).
SAFE_MENTIONS = discord.AllowedMentions(everyone=False, roles=False, users=True)

bot = commands.Bot(
    command_prefix="!",
    intents=INTENTS,
    help_command=None,
    allowed_mentions=SAFE_MENTIONS,
)

INITIAL_COGS = [
    "cogs.tickets",       # должен грузиться раньше bug_reports/qa_agent — они его используют
    "cogs.bug_reports",
    "cogs.qa_agent",
    "cogs.trello_sync",
]

# Переменные окружения, без которых бот либо не будет работать, либо будет
# работать в урезанном/небезопасном режиме — логируем явно при старте,
# чтобы это было видно в логах Discloud, а не всплывало тихой ошибкой позже.
RECOMMENDED_ENV = [
    "BUG_REPORT_CHANNEL_ID",
    "TICKET_CATEGORY_ID",
    "ADMIN_ROLE_ID",
    "TRELLO_API_KEY",
    "TRELLO_TOKEN",
    "TRELLO_BOARD_ID",
    "ANTHROPIC_API_KEY",
]


def _check_env():
    for name in RECOMMENDED_ENV:
        if not os.getenv(name):
            log.warning(f"Переменная окружения {name} не задана — соответствующий функционал будет отключён/урезан")


@bot.event
async def on_ready():
    log.info(f"Logged in as {bot.user} (id={bot.user.id})")
    try:
        synced = await bot.tree.sync()
        log.info(f"Synced {len(synced)} slash command(s)")
    except Exception as e:
        log.exception(f"Slash sync failed: {e}")


async def load_extensions():
    for ext in INITIAL_COGS:
        try:
            await bot.load_extension(ext)
            log.info(f"Loaded extension: {ext}")
        except Exception:
            log.exception(f"Failed to load extension: {ext}")


@bot.event
async def setup_hook():
    _check_env()
    await load_extensions()


if __name__ == "__main__":
    token = os.getenv("DISCORD_TOKEN")
    if not token:
        raise RuntimeError("DISCORD_TOKEN не найден в .env")
    bot.run(token, log_handler=None)
