import json
from datetime import date
from pathlib import Path

from expense_tracker.core import Expense, Tracker


def save_tracker(tracker: Tracker, path: Path) -> None:
    data = {
        "categories": tracker.list_categories(),
        "expenses": [
            {
                "id": e.id,
                "amount": e.amount,
                "category": e.category,
                "note": e.note,
                "date": e.date.isoformat(),
            }
            for e in tracker.list_expenses()
        ],
    }
    path.write_text(json.dumps(data, indent=2))


def load_tracker(path: Path) -> Tracker:
    tracker = Tracker()
    if not path.exists():
        return tracker

    data = json.loads(path.read_text())
    tracker._categories = list(data["categories"])
    tracker._expenses = [
        Expense(
            id=e["id"],
            amount=e["amount"],
            category=e["category"],
            note=e["note"],
            date=date.fromisoformat(e["date"]),
        )
        for e in data["expenses"]
    ]
    tracker._next_id = max((e.id for e in tracker._expenses), default=0) + 1
    return tracker
