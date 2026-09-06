from datetime import date, datetime


def format_date(d: date, fmt: str) -> str:
    return d.strftime(fmt)


def parse_date(text: str, fmt: str) -> date:
    return datetime.strptime(text, fmt).date()
