import logging
import os
from logging.handlers import RotatingFileHandler

def setup_logger():

    os.makedirs('logs', exist_ok=True)

    formatter = logging.Formatter(
        fmt='%(asctime)s %(levelname)-8s %(name)s — %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # handler ke file — maksimal 5MB, simpan 3 file terakhir
    file_handler = RotatingFileHandler(
        filename='logs/app.log',
        maxBytes=5 * 1024 * 1024,
        backupCount=3,
        encoding='utf-8'
    )
    file_handler.setFormatter(formatter)
    file_handler.setLevel(logging.INFO)

    # handler ke terminal
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    console_handler.setLevel(logging.INFO)

    # root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)