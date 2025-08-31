import logging
from rich.logging import RichHandler

FMT = "%(asctime)s | %(levelname)s | %(name)s | %(message)s"

def setup_logging(level: str = "INFO"):
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format=FMT,
        datefmt="%H:%M:%S",
        handlers=[RichHandler(rich_tracebacks=True)]
    )
