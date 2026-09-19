from datetime import datetime
from calendar import timegm

def parse_ibkr_date(date_str) -> int:
    """
    IBKR historical bars return dates in multiple formats:
      - Unix epoch (int/float or numeric string): e.g. 1789668000 or '1789668000'
      - Daily+: 'YYYYMMDD'             e.g. '20241215'
      - Intraday: 'YYYYMMDD  HH:MM:SS' e.g. '20241215  09:35:00'
    Returns UTC unix timestamp (int).
    """
    if isinstance(date_str, (int, float)):
        return int(date_str)
    date_str = str(date_str).strip()
    if date_str.isdigit() and len(date_str) == 10:
        return int(date_str)
    if len(date_str) == 8:
        dt = datetime.strptime(date_str, "%Y%m%d")
    else:
        dt = datetime.strptime(date_str, "%Y%m%d  %H:%M:%S")
    return int(timegm(dt.timetuple()))
