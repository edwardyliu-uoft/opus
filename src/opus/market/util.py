from __future__ import annotations

import calendar


def parse_timestamp(date_str: str, time_str: str) -> int:
    """Parses date and time strings into UNIX nanoseconds from epoch."""
    if time_str.isdigit():
        return int(time_str)

    if "-" in date_str:
        y, m, d = int(date_str[0:4]), int(date_str[5:7]), int(date_str[8:10])
    else:
        y, m, d = int(date_str[0:4]), int(date_str[4:6]), int(date_str[6:8])

    parts = time_str.split(".")
    hms = parts[0]
    nano_str = parts[1] if len(parts) > 1 else "0"
    nano_str = (nano_str.ljust(9, "0"))[:9]
    hour, minute, second = [int(x) for x in hms.split(":")]
    unix_sec = calendar.timegm((y, m, d, hour, minute, second))
    return int(unix_sec * 1_000_000_000 + int(nano_str))
