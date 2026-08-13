import re


def get_seconds_from_time(time_interval: int | float | str) -> float:
    error_str = f"Invalid time interval: {time_interval}"
    if not isinstance(time_interval, str):
        try:
            return float(time_interval)
        except (ValueError, TypeError) as exc:
            raise ValueError(error_str) from exc

    try:
        return float(time_interval)
    except ValueError:
        pass

    pattern = r"(\d+)([smhdw])"

    unit_to_seconds = {
        "s": 1,  # seconds
        "m": 60,  # minutes
        "h": 3600,  # hours
        "d": 86400,  # days
        "w": 604800,  # weeks
    }

    matches = re.findall(pattern, time_interval.lower())
    if not matches:
        raise ValueError(error_str)

    total_seconds = 0
    for value, unit in matches:
        unit_value = unit_to_seconds.get(unit)
        if not unit_value:
            raise ValueError(error_str)

        total_seconds += int(value) * unit_value

    return float(total_seconds)
