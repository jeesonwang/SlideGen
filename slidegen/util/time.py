import datetime

import dateutil.parser

from slidegen.config.conf import settings


def now_datetime():
    """获取实时datetime"""
    return now_tz_datetime().replace(tzinfo=None)


def now_tz_datetime():
    """获取带TIMEZONE的datetime"""
    return datetime.datetime.now(tz=settings.TZ)


def init_datetime():
    """初始化数据时间"""
    return strptime("1970-01-01 00:00:00")


def strftime(date: datetime.datetime, fmt: str = "%Y-%m-%d %H:%M:%S"):
    return date.strftime(fmt)


def now_tz_datestring(fmt: str = "%Y-%m-%d %H:%M:%S"):
    return strftime(now_datetime(), fmt=fmt)


def strptime(datestr: str, fmt=None):
    if fmt is not None:
        return datetime.datetime.strptime(datestr, fmt)

    if len(datestr) == 10:
        return datetime.datetime.strptime(datestr, "%Y-%m-%d")
    elif len(datestr) == 19:
        return datetime.datetime.strptime(datestr, "%Y-%m-%d %H:%M:%S")


def days_date_range(start_date: datetime.datetime, end_date: datetime.datetime):
    """获取时间周期列表"""
    dates = []
    dt = datetime.datetime.strptime(start_date, "%Y-%m-%d")
    date = start_date[:]
    while date <= end_date:
        dates.append(date)
        dt = dt + datetime.timedelta(days=1)
        date = dt.strftime("%Y-%m-%d")
    return dates


def time_difference(date1: str | datetime.datetime, date2: str | datetime.datetime) -> datetime.timedelta:
    """获取时间差"""
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

    Example:
        start: 2020-03-01 will be converted to 2020-03-01 00:00:00
        end: 2020-03-31 will be converted to 2020-03-31 23:59:59

    Args:
        start: start time
        end: end time
        length: time length

    Returns:
        start and end time
    """
    start = convert_to_search_start_time(start)[:length]
    end = convert_to_search_end_time(end)[:length]
    return start, end


def convert_to_search_start_time(start: datetime.datetime | str) -> str:
    if isinstance(start, str) and len(start) == 19:
        return start

    if isinstance(start, datetime.datetime):
        start = start.date()
    else:
        start = datetime.datetime.strptime(start, "%Y-%m-%d").date()

    return start.strftime("%Y-%m-%d %H:%M:%S")


def convert_to_search_end_time(end: datetime.datetime | str) -> str:
    if isinstance(end, str) and len(end) == 19:
        return end

    if not isinstance(end, datetime.datetime):
        end = datetime.datetime.strptime(end, "%Y-%m-%d").replace(hour=23, minute=59, second=59)

    end = end.strftime("%Y-%m-%d %H:%M:%S")
    return end


def is_valid_datetime(value: str):
    try:
        dateutil.parser.parse(value)
        return True
    except Exception:
        return False
