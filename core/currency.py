def format_currency(amount):
    try:
        value = int(round(float(amount or 0)))
    except (TypeError, ValueError):
        value = 0
    return f'{value} BYN'
