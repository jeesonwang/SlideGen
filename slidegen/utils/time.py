import datetime

import dateutil.parser

from slidegen.config import settings


def now_datetime() -> datetime.datetime:
    """Get real-time datetime"""
    return now_tz_datetime().replace(tzinfo=None)


def now_tz_datetime() -> datetime.datetime:
    """Get datetime with TIMEZONE"""
    return datetime.datetime.now(tz=settings.TZ)


def init_datetime() -> datetime.datetime:
    """Initialize data time"""
    return strptime("1970-01-01 00:00:00")


def strftime(date: datetime.datetime, fmt: str = "%Y-%m-%d %H:%M:%S") -> str:
    return date.strftime(fmt)


def now_tz_datestring(fmt: str = "%Y-%m-%d %H:%M:%S") -> str:
    return strftime(now_datetime(), fmt=fmt)


def strptime(datestr: str, fmt: str | None = None) -> datetime.datetime:
    if fmt is not None:
        return datetime.datetime.strptime(datestr, fmt)

    if len(datestr) == 10:
        return datetime.datetime.strptime(datestr, "%Y-%m-%d")
    elif len(datestr) == 19:
        return datetime.datetime.strptime(datestr, "%Y-%m-%d %H:%M:%S")
    raise


def days_date_range(start_date: str, end_date: str) -> list[str]:
    """Get time period list"""
    dates = []
    dt = datetime.datetime.strptime(start_date, "%Y-%m-%d")
    date = start_date[:]
    while date <= end_date:
        dates.append(date)
        dt = dt + datetime.timedelta(days=1)
        date = dt.strftime("%Y-%m-%d")
    return dates


def time_difference(date1: str | datetime.datetime, date2: str | datetime.datetime) -> datetime.timedelta:
    """Get time difference"""
    if isinstance(date1, str):
        date1 = strptime(date1)
    if isinstance(date2, str):
        date2 = strptime(date2)
    return date2 - date1


def convert_to_search_interval(
    start: datetime.datetime | str, end: datetime.datetime | str, length: int = 19
) -> tuple[str, str]:
    """
    Convert %Y-%m-%d time format to %Y-%m-%d %H:%M:%S

    example:
        start: 2020-03-01 will be converted to 2020-03-01 00:00:00
        end: 2020-03-31 will be converted to 2020-03-31 23:59:59

    :param start: Start time
    :param end: End time
    :param length: Time length
    :return: Start and end time
    """
    start = convert_to_search_start_time(start)[:length]
    end = convert_to_search_end_time(end)[:length]
    return start, end


def convert_to_search_start_time(start: datetime.datetime | str) -> str:
    if isinstance(start, str) and len(start) == 19:
        return start
    if isinstance(start, datetime.datetime):
        start_time = start.date()
    else:
        start_time = datetime.datetime.strptime(start, "%Y-%m-%d")
    start = start_time.strftime("%Y-%m-%d %H:%M:%S")
    return start


def convert_to_search_end_time(end: datetime.datetime | str) -> str:
    if isinstance(end, str) and len(end) == 19:
        return end

    if not isinstance(end, datetime.datetime):
        end_time = datetime.datetime.strptime(end, "%Y-%m-%d")
        end_time = end_time.replace(hour=23, minute=59, second=59)
    else:
        end_time = end
    end_time_str = end_time.strftime("%Y-%m-%d %H:%M:%S")
    return end_time_str


def is_valid_datetime(value: str) -> bool:
    try:
        dateutil.parser.parse(value)
        return True
    except Exception:
        return False
