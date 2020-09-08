import logging

from loguru import logger as loguru_logger

from app.core.config import settings


class InterceptHandler(logging.Handler):
    loglevel_mapping = {
        logging.CRITICAL: "CRITICAL",
        logging.ERROR: "ERROR",
        logging.WARNING: "WARNING",
        logging.INFO: "INFO",
        logging.DEBUG: "DEBUG",
        logging.NOTSET: "NOTSET",
    }

    def emit(self, record):
        try:
            level = loguru_logger.level(record.levelname).name
        except AttributeError:
            level = self.loglevel_mapping[record.levelno]

        frame, depth = logging.currentframe(), 2
        while frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back
            depth += 1

        log = loguru_logger.bind(request_id="app")
        log.opt(depth=depth, exception=record.exc_info).log(level, record.getMessage())


intercept_handler = InterceptHandler()
logging.root.setLevel(settings.LOG_LEVEL.upper())
for name in (
    "gunicorn",
    "gunicorn.access",
    "gunicorn.error",
    "uvicorn",
    "uvicorn.access",
    "uvicorn.error",
):
    logging.getLogger(name).handlers = [intercept_handler]

logger = loguru_logger.bind(request_id=None, method=None)
