import logging
from pathlib import Path

def setup_logging(log_file: Path) -> logging.Logger:
    """
    Configure application-wide logging.

    Logs are written both to the console (INFO+) and to a file (DEBUG+).
    """
    logger_name = "profile_finder"
    logger = logging.getLogger(logger_name)
    logger.setLevel(logging.DEBUG)

    # Avoid adding duplicate handlers if setup_logging is called multiple times.
    if logger.handlers:
        return logger

    log_file = Path(log_file)
    log_file.parent.mkdir(parents=True, exist_ok=True)

    # File handler: verbose debug log
    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setLevel(logging.DEBUG)
    file_formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    file_handler.setFormatter(file_formatter)

    # Console handler: more compact info log
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_formatter = logging.Formatter("%(levelname)s - %(message)s")
    console_handler.setFormatter(console_formatter)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    logger.debug("Logger initialized; writing to %s", log_file)
    return logger