import asyncio

from app.core.log import logger
from app.examiners import check_cache, check_db


def main() -> None:
    logger.info("Initializing backend service")
    check_db()
    asyncio.run(check_cache())
    logger.info("Service finished initializing")


if __name__ == "__main__":
    main()
