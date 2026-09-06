from collections import defaultdict
from dataclasses import dataclass
from datetime import date

DEFAULT_CATEGORIES = ["Food", "Transport", "Bills", "Fun", "Other"]


@dataclass
class Summary:
    by_category: dict[str, float]
    by_month: dict[str, float]
    total: float


class UnknownCategory(Exception):
    pass


@dataclass
class Expense:
    id: int
    amount: float
    category: str
    note: str
    date: date


class Tracker:
    def __init__(self):
        self._expenses: list[Expense] = []
        self._next_id = 1
        self._categories: list[str] = list(DEFAULT_CATEGORIES)

    def list_categories(self) -> list[str]:
        return list(self._categories)

    def add_category(self, name: str) -> None:
        if name not in self._categories:
            self._categories.append(name)

    def rename_category(self, old_name: str, new_name: str) -> None:
        index = self._categories.index(old_name)
        self._categories[index] = new_name
        for expense in self._expenses:
            if expense.category == old_name:
                expense.category = new_name

    def delete_category(self, name: str, reassign_to: str = "Other") -> None:
        self._categories.remove(name)
        for expense in self._expenses:
            if expense.category == name:
                expense.category = reassign_to

    def add_expense(self, amount: float, category: str, note: str, when: date) -> Expense:
        if category not in self._categories:
            raise UnknownCategory(category)
        expense = Expense(id=self._next_id, amount=amount, category=category, note=note, date=when)
        self._expenses.append(expense)
        self._next_id += 1
        return expense

    def list_expenses(self) -> list[Expense]:
        return list(self._expenses)

    def _find(self, expense_id: int) -> Expense:
        for expense in self._expenses:
            if expense.id == expense_id:
                return expense
        raise KeyError(expense_id)

    def edit_expense(self, expense_id: int, amount: float = None, category: str = None,
                      note: str = None, when: date = None) -> Expense:
        expense = self._find(expense_id)
        if category is not None and category not in self._categories:
            raise UnknownCategory(category)
        if amount is not None:
            expense.amount = amount
        if category is not None:
            expense.category = category
        if note is not None:
            expense.note = note
        if when is not None:
            expense.date = when
        return expense

    def delete_expense(self, expense_id: int) -> None:
        expense = self._find(expense_id)
        self._expenses.remove(expense)

    def summary(self) -> Summary:
        by_category: dict[str, float] = defaultdict(float)
        by_month: dict[str, float] = defaultdict(float)
        total = 0.0
        for expense in self._expenses:
            by_category[expense.category] += expense.amount
            month_key = f"{expense.date.year:04d}-{expense.date.month:02d}"
            by_month[month_key] += expense.amount
            total += expense.amount
        return Summary(by_category=dict(by_category), by_month=dict(by_month), total=total)
