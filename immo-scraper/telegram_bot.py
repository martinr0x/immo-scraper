import logging
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import List, Optional
from models import Filter, Listing
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes
)
from scraper import scrape_immo_webpage

def get_last_scrape_time()-> Optional[datetime]:
   f = Path("last_scrape_time.txt")
   if f.exists():
        return datetime.fromisoformat(f.read_text())

def get_current_filter(last_checked: Optional[datetime])-> Filter:
    return Filter(1800,None,60, 2.0, last_checked)
# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
# set higher logging level for httpx to avoid all GET and POST requests being logged
logging.getLogger("httpx").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)


# Define a few command handlers. These usually take the two arguments update and
# context.
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Sends explanation on how to use the bot."""
    await update.message.reply_text("Hi! Use /set <seconds> to set a timer")


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /help is issued."""
    await update.message.reply_text("Help!")


async def get_listings(context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send the alarm message."""
    job = context.job
    gmt_plus_1 = timezone(timedelta(hours=1))
    last_scraped = datetime.now(gmt_plus_1).isoformat()
    logger.info(f"Starting scraping {last_scraped}")
    async def post_listing(listings: List[Listing]):
        logger.info (f"Found that many listings {len(listings)}")
        for listing in filter(get_current_filter(job.data).match, listings):
            await context.bot.send_message(job.chat_id, text=listing.to_text())

    await scrape_immo_webpage(post_listing)
    
    Path("last_scrape_time.txt").write_text(last_scraped)
    job.data = last_scraped


def remove_job_if_exists(name: str, context: ContextTypes.DEFAULT_TYPE) -> bool:
    """Remove job with given name. Returns whether job was removed."""
    current_jobs = context.job_queue.get_jobs_by_name(name)
    if not current_jobs:
        return False
    for job in current_jobs:
        job.schedule_removal()
    return True


async def set_scraper(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Add a job to the queue."""
    chat_id = update.effective_message.chat_id
    chat_id = "-1002274814344"
    try:
        interval = float(context.args[0])
        if interval < 10:
            await update.effective_message.reply_text(
                "Bot should not run less than every 10 mins"
            )
            return

        # interval *= 60

        job_removed = remove_job_if_exists(str(chat_id), context)
        context.job_queue.run_once(
            get_listings, interval, chat_id=chat_id, name=str(chat_id), data=get_last_scrape_time()
        )

        text = "Immofilter successfully set!"
        if job_removed:
            text += " Old one was removed."
        await update.effective_message.reply_text(text)

    except (IndexError, ValueError):
        await update.effective_message.reply_text("Usage: /scrape <minutes>")


def main() -> None:
    """Start the bot."""
    # Create the Application and pass it your bot's token.
    application = (
        Application.builder()
        .token("8114856635:AAHGU6gdhPNTGdCxstvSGikvwaKEF82EGxw")
        .build()
    )

    # on different commands - answer in Telegram
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("scrape", set_scraper))

    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
