from loguru import logger
import sys

# Remove default logger
logger.remove()

# Log to terminal with colors
logger.add(
    sys.stdout,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level}</level> | <cyan>{message}</cyan>",
    level="DEBUG"
)

# Log to file (keeps last 7 days)
logger.add(
    "logs/app.log",
    rotation="1 day",
    retention="7 days",
    level="INFO",
    format="{time} | {level} | {message}"
)

# Log errors separately
logger.add(
    "logs/errors.log",
    rotation="1 week",
    level="ERROR",
    format="{time} | {level} | {message} | {exception}"
)