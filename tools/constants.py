import sys
import logging

YES = "🟢  "
WARNING = "🟠  "
NO = "🔴  "

LOG_HANDLER = logging.StreamHandler(sys.stdout)
fmt = logging.Formatter(
    '%(asctime)s [%(levelname)-8s] onigiri: %(message)s',
    "[%Y-%m-%d %H:%M:%S]"
)
LOG_HANDLER.setFormatter(fmt)
