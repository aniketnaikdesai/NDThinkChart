from data.models import Alarm


def evaluate_alarms(
    prev_price: float | None,
    curr_price: float,
    alarms: list[Alarm],
) -> list[Alarm]:
    """
    Return active, untriggered alarms crossed between prev_price and curr_price.
    """
    if prev_price is None or curr_price <= 0:
        return []

    triggered: list[Alarm] = []
    for alarm in alarms:
        if not alarm.active or alarm.triggered:
            continue

        crossed_above = prev_price < alarm.price <= curr_price
        crossed_below = prev_price > alarm.price >= curr_price

        if alarm.direction == "cross_above" and crossed_above:
            triggered.append(alarm)
        elif alarm.direction == "cross_below" and crossed_below:
            triggered.append(alarm)
        elif alarm.direction == "cross_either" and (crossed_above or crossed_below):
            triggered.append(alarm)

    return triggered
