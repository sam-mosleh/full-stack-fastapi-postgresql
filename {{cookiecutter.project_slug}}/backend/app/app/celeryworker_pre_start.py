from app.core.log import logger
from app.examiners import check_db


def main() -> None:
    logger.info("Initializing celeryworker service")
    check_db()
    logger.info("Service finished initializing")


if __name__ == "__main__":
    main()
