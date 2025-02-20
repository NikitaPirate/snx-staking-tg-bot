import logging

from app.bootstrap import bootstrap

log_format = "[%(asctime)s] [%(name)s] [%(levelname)s] %(message)s"
date_format = "%Y-%m-%d %H:%M:%S"
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("apscheduler").setLevel(logging.WARNING)
logging.basicConfig(format=log_format, datefmt=date_format, level=logging.INFO)


if __name__ == "__main__":
    app = bootstrap()
    app.run_polling()
