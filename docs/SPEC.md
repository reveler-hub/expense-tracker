# Expense Tracker — Spec

Agreed via a `/grill-me` interview before implementation.

- **Command**: `expense`
- **On launch**: shows the spending summary first (category breakdown + this month's total), then a menu below it with:
  - Add expense
  - View / edit entries
  - Manage categories
  - Quit
- **Adding an expense**: amount, category (pick from list), date, free-text note
- **Viewing entries**: arrow-key navigable list -> `e` to edit the selected entry, `d` to delete (asks "are you sure?" first)
- **Categories**: fixed starter list (Food, Transport, Bills, Fun, Other), managed the same way — arrow keys, `e` to rename, `d` to delete (asks first)
- **Deleting a category in use**: any expenses tagged with it move to "Other" automatically; their note is untouched
- **Summary**: totals broken down both by category and by month
- **Editing an entry**: can change any of its fields, including category (added after an initial gap was found in testing)
- Implementation details left to the implementer: data persisted in a plain file in the user's home folder so it survives between sessions; dates default to "today" unless changed; date input/display should follow the user's system locale rather than a hardcoded format (added after testing revealed hardcoded ISO dates).
