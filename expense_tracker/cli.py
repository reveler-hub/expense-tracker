import curses
import locale
from datetime import date
from pathlib import Path

from expense_tracker.core import Tracker, UnknownCategory
from expense_tracker.dateformat import format_date, parse_date
from expense_tracker.storage import load_tracker, save_tracker

DATA_PATH = None  # set in main()
DATE_FORMAT = "%Y-%m-%d"  # set in main(), from the user's locale


def detect_date_format() -> str:
    """The day/month/year order the user's system locale prefers, always with a 4-digit year.

    Assumes the process locale is already set (see main()) - curses fixes its screen
    encoding when initscr() runs, so setting the locale any later than that risks
    curses trying to draw locale-specific characters (e.g. a CJK D_FMT) it wasn't
    initialized to handle.
    """
    try:
        fmt = locale.nl_langinfo(locale.D_FMT)
    except (locale.Error, AttributeError, ValueError):
        fmt = None
    if not fmt:
        return "%Y-%m-%d"
    return fmt.replace("%y", "%Y")


def prompt_text(stdscr, y, message, initial=""):
    curses.echo()
    curses.curs_set(1)
    stdscr.addstr(y, 0, message)
    stdscr.clrtoeol()
    stdscr.refresh()
    win = curses.newwin(1, 60, y, len(message))
    win.addstr(0, 0, initial)
    win.refresh()
    text = win.getstr(0, 0).decode("utf-8") or initial
    curses.noecho()
    curses.curs_set(0)
    return text


def select_from_list(stdscr, items, title, start=0):
    """Arrow keys to move, Enter to pick, Esc to cancel. Returns index or None."""
    index = start
    while True:
        stdscr.clear()
        stdscr.addstr(0, 0, title)
        for i, item in enumerate(items):
            marker = "-> " if i == index else "   "
            attr = curses.A_REVERSE if i == index else curses.A_NORMAL
            stdscr.addstr(2 + i, 0, f"{marker}{item}", attr)
        stdscr.addstr(3 + len(items), 0, "(up/down to move, enter to pick, esc to cancel)")
        stdscr.refresh()
        key = stdscr.getch()
        if key in (curses.KEY_UP, ord("k")):
            index = (index - 1) % len(items)
        elif key in (curses.KEY_DOWN, ord("j")):
            index = (index + 1) % len(items)
        elif key in (curses.KEY_ENTER, 10, 13):
            return index
        elif key == 27:  # Esc
            return None


def list_with_actions(stdscr, items, title, hint="e: edit  d: delete  esc: back", extra_actions=None):
    """Arrow keys to move. Returns (action, index). action is 'edit', 'delete', a name from
    extra_actions, or None (back/cancel) - index is None whenever there's no selected item."""
    extra_actions = extra_actions or {}
    index = 0
    while True:
        stdscr.clear()
        stdscr.addstr(0, 0, title)
        if items:
            for i, item in enumerate(items):
                marker = "-> " if i == index else "   "
                attr = curses.A_REVERSE if i == index else curses.A_NORMAL
                stdscr.addstr(2 + i, 0, f"{marker}{item}", attr)
        else:
            stdscr.addstr(2, 0, "(nothing here yet)")
        stdscr.addstr(3 + len(items), 0, hint)
        stdscr.refresh()
        key = stdscr.getch()
        if key in extra_actions:
            return extra_actions[key], (index if items else None)
        elif key == 27:  # Esc always works, even on an empty list
            return None, None
        elif not items:
            continue
        elif key in (curses.KEY_UP, ord("k")):
            index = (index - 1) % len(items)
        elif key in (curses.KEY_DOWN, ord("j")):
            index = (index + 1) % len(items)
        elif key == ord("e"):
            return "edit", index
        elif key == ord("d"):
            return "delete", index


def confirm(stdscr, message):
    stdscr.clear()
    stdscr.addstr(0, 0, f"{message} (y/n)")
    stdscr.refresh()
    while True:
        key = stdscr.getch()
        if key in (ord("y"), ord("Y")):
            return True
        if key in (ord("n"), ord("N"), 27):
            return False


def parse_amount(stdscr, y, initial=""):
    while True:
        text = prompt_text(stdscr, y, "Amount: ", initial)
        try:
            return float(text)
        except ValueError:
            stdscr.addstr(y + 1, 0, "Not a number, try again.")
            stdscr.refresh()


def prompt_date(stdscr, y, initial=None):
    default = initial or date.today()
    hint = DATE_FORMAT.replace("%d", "DD").replace("%m", "MM").replace("%Y", "YYYY")
    text = prompt_text(stdscr, y, f"Date [{hint}] (enter for {format_date(default, DATE_FORMAT)}): ")
    if not text.strip():
        return default
    try:
        return parse_date(text.strip(), DATE_FORMAT)
    except ValueError:
        stdscr.addstr(y + 1, 0, "Couldn't read that date, using default.")
        stdscr.refresh()
        stdscr.getch()
        return default


def add_expense_flow(stdscr, tracker: Tracker):
    categories = tracker.list_categories()
    stdscr.clear()
    stdscr.refresh()
    choice = select_from_list(stdscr, categories, "Pick a category:")
    if choice is None:
        return
    category = categories[choice]

    stdscr.clear()
    amount = parse_amount(stdscr, 0)
    when = prompt_date(stdscr, 2)
    note = prompt_text(stdscr, 4, "Note (optional): ")

    tracker.add_expense(amount=amount, category=category, note=note, when=when)


def edit_expense_flow(stdscr, tracker: Tracker, expense_id: int):
    expense = tracker._find(expense_id)
    stdscr.clear()
    amount = parse_amount(stdscr, 0, initial=str(expense.amount))
    when = prompt_date(stdscr, 2, initial=expense.date)
    note = prompt_text(stdscr, 4, "Note: ", initial=expense.note)

    categories = tracker.list_categories()
    current_index = categories.index(expense.category) if expense.category in categories else 0
    choice = select_from_list(
        stdscr,
        categories,
        f"Change category (currently: {expense.category}). Enter to confirm, Esc to keep current:",
        start=current_index,
    )
    category = categories[choice] if choice is not None else None

    tracker.edit_expense(expense_id, amount=amount, category=category, note=note, when=when)


def view_edit_entries_flow(stdscr, tracker: Tracker):
    sort_by_amount = False
    while True:
        if sort_by_amount:
            expenses = sorted(tracker.list_expenses(), key=lambda e: e.amount, reverse=True)
        else:
            expenses = sorted(tracker.list_expenses(), key=lambda e: e.date, reverse=True)
        rows = [
            f"{format_date(e.date, DATE_FORMAT)}  {e.category:<10}  ${e.amount:>8.2f}  {e.note}"
            for e in expenses
        ]
        sort_label = "highest amount first" if sort_by_amount else "newest first"
        action, index = list_with_actions(
            stdscr,
            rows,
            f"Your expenses (sorted: {sort_label}):",
            hint="e: edit  d: delete  s: toggle sort  esc: back",
            extra_actions={ord("s"): "sort"},
        )
        if action is None:
            return
        if action == "sort":
            sort_by_amount = not sort_by_amount
            continue
        expense = expenses[index]
        if action == "edit":
            edit_expense_flow(stdscr, tracker, expense.id)
        elif action == "delete":
            if confirm(stdscr, f"Delete this expense ({expense.category}, ${expense.amount:.2f})?"):
                tracker.delete_expense(expense.id)


def manage_categories_flow(stdscr, tracker: Tracker):
    while True:
        categories = tracker.list_categories()
        action, index = list_with_actions(
            stdscr,
            categories,
            "Categories:",
            hint="e: rename  d: delete  a: add new  esc: back",
            extra_actions={ord("a"): "add"},
        )
        if action is None:
            return
        if action == "edit":
            old_name = categories[index]
            new_name = prompt_text(stdscr, 0, f"Rename '{old_name}' to: ")
            if new_name.strip():
                tracker.rename_category(old_name, new_name.strip())
        elif action == "delete":
            name = categories[index]
            if name == "Other":
                stdscr.clear()
                stdscr.addstr(0, 0, "Can't delete 'Other' - it's the fallback category.")
                stdscr.addstr(2, 0, "(press any key to continue)")
                stdscr.refresh()
                stdscr.getch()
                continue
            if confirm(stdscr, f"Delete '{name}'? Its expenses will move to 'Other'."):
                tracker.delete_category(name)
        elif action == "add":
            new_name = prompt_text(stdscr, 0, "New category name: ")
            if new_name.strip():
                tracker.add_category(new_name.strip())


def render_summary(stdscr, tracker: Tracker, y=0):
    summary = tracker.summary()
    this_month = f"{date.today().year:04d}-{date.today().month:02d}"
    spent_this_month = summary.by_month.get(this_month, 0.0)
    stdscr.addstr(y, 0, f"Spent this month: ${spent_this_month:.2f}   (all-time total: ${summary.total:.2f})")
    y += 2
    if summary.by_category:
        stdscr.addstr(y, 0, "By category:")
        y += 1
        for category, amount in sorted(summary.by_category.items(), key=lambda kv: -kv[1]):
            stdscr.addstr(y, 2, f"{category:<10} ${amount:.2f}")
            y += 1
        y += 1
    if summary.by_month:
        stdscr.addstr(y, 0, "By month:")
        y += 1
        for month, amount in sorted(summary.by_month.items(), reverse=True):
            stdscr.addstr(y, 2, f"{month}   ${amount:.2f}")
            y += 1
    return y + 1


def main_menu(stdscr, tracker: Tracker):
    menu_items = ["Add expense", "View / edit entries", "Manage categories", "Quit"]
    index = 0
    while True:
        stdscr.clear()
        y = render_summary(stdscr, tracker)
        for i, item in enumerate(menu_items):
            marker = "-> " if i == index else "   "
            attr = curses.A_REVERSE if i == index else curses.A_NORMAL
            stdscr.addstr(y + i, 0, f"{marker}{item}", attr)
        stdscr.refresh()
        save_tracker(tracker, DATA_PATH)

        key = stdscr.getch()
        if key in (curses.KEY_UP, ord("k")):
            index = (index - 1) % len(menu_items)
        elif key in (curses.KEY_DOWN, ord("j")):
            index = (index + 1) % len(menu_items)
        elif key in (curses.KEY_ENTER, 10, 13):
            choice = menu_items[index]
            if choice == "Add expense":
                add_expense_flow(stdscr, tracker)
            elif choice == "View / edit entries":
                view_edit_entries_flow(stdscr, tracker)
            elif choice == "Manage categories":
                manage_categories_flow(stdscr, tracker)
            elif choice == "Quit":
                save_tracker(tracker, DATA_PATH)
                return


def run(stdscr, data_path):
    global DATA_PATH, DATE_FORMAT
    DATA_PATH = data_path
    DATE_FORMAT = detect_date_format()
    curses.set_escdelay(25)
    curses.curs_set(0)
    tracker = load_tracker(data_path)
    try:
        main_menu(stdscr, tracker)
    finally:
        save_tracker(tracker, data_path)


def main():
    locale.setlocale(locale.LC_ALL, "")  # must happen before curses.wrapper() initializes the screen
    data_path = Path.home() / ".expense-tracker" / "expenses.json"
    data_path.parent.mkdir(parents=True, exist_ok=True)
    curses.wrapper(run, data_path)


if __name__ == "__main__":
    main()
