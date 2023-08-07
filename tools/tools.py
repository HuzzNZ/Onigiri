from datetime import datetime


def log_time() -> str:
    """
    Returns a string representing the current time.

    :return: String representing the current time
    """
    return datetime.now().strftime('[%b %d %H:%M:%S]  ')
