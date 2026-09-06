# Expense Tracker

A tiny terminal expense tracker: add expenses, edit or delete them, manage categories, and see totals by category and by month.

## Install

Requires Python 3.10+. The easiest way is [pipx](https://pipx.pypa.io/), which installs the `expense` command in its own isolated environment:

```bash
pipx install git+https://github.com/<your-username>/<your-repo>.git
```

Or, from a local clone:

```bash
git clone https://github.com/<your-username>/<your-repo>.git
cd <your-repo>
pipx install .
```

## Use

```bash
expense
```

Your data is stored in `~/.expense-tracker/expenses.json`.
