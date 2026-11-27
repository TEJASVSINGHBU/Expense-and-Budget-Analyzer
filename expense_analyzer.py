"""
Personal Expense and Budget Analyzer
------------------------------------
Records income and expenses, categorizes spending, produces monthly
summaries, compares months, and gives rule-based budget alerts and
suggestions. Expenses are saved to / loaded from a CSV file.
"""

import csv
from datetime import date, datetime

CATEGORIES = ["Food", "Travel", "Shopping", "Entertainment", "Education", "Other"]
FILE_NAME = "expenses.csv"
FIELDS = ["date", "description", "category", "amount"]

# Rule: maximum share of the monthly budget each category should use
CATEGORY_LIMITS = {
    "Food": 0.35,
    "Travel": 0.15,
    "Shopping": 0.20,
    "Entertainment": 0.10,
    "Education": 0.15,
    "Other": 0.10,
}
WARNING_LEVEL = 0.80        # warn when 80% of budget is used
DOMINANT_SHARE = 0.40       # one category taking >40% of spending
MIN_SAVINGS_RATE = 0.20     # suggest saving at least 20% of income


# ---------- Input helpers (validation) ----------

def get_amount(prompt):
    """Keep asking until the user enters a valid positive number."""
    while True:
        try:
            value = float(input(prompt))
            if value <= 0:
                print("  Amount must be greater than 0.")
                continue
            return value
        except ValueError:
            print("  Invalid input. Please enter a number (e.g. 250 or 99.5).")


def choose_category():
    """Show the category menu and return the chosen category name."""
    print("Categories:")
    for number, name in enumerate(CATEGORIES, start=1):
        print(f"  {number}. {name}")
    while True:
        choice = input("Choose category number: ").strip()
        if choice.isdigit() and 1 <= int(choice) <= len(CATEGORIES):
            return CATEGORIES[int(choice) - 1]
        print(f"  Please enter a number between 1 and {len(CATEGORIES)}.")


def get_date(prompt):
    """Return a valid date string (YYYY-MM-DD). Blank means today."""
    while True:
        text = input(prompt).strip()
        if text == "":
            return str(date.today())
        try:
            datetime.strptime(text, "%Y-%m-%d")
            return text
        except ValueError:
            print("  Invalid date. Use YYYY-MM-DD (e.g. 2026-11-15).")


def get_month(prompt):
    """Return a valid month string (YYYY-MM). Blank means current month."""
    while True:
        text = input(prompt).strip()
        if text == "":
            return date.today().strftime("%Y-%m")
        try:
            datetime.strptime(text, "%Y-%m")
            return text
        except ValueError:
            print("  Invalid month. Use YYYY-MM (e.g. 2026-11).")


# ---------- Core logic ----------

def add_expense(expenses):
    """Take one expense from the user and store it as a dictionary."""
    description = input("Description: ").strip() or "No description"
    amount = get_amount("Amount (Rs.): ")
    category = choose_category()
    when = get_date("Date YYYY-MM-DD (blank = today): ")
    expenses.append({
        "date": when,
        "description": description,
        "category": category,
        "amount": amount,
    })
    print(f"  Added: {description} - Rs. {amount:.2f} [{category}] on {when}")


def delete_expense(expenses):
    """Remove an expense chosen by its number in the list."""
    if not expenses:
        print("  Nothing to delete.")
        return
    view_expenses(expenses)
    choice = input("Enter number to delete (blank to cancel): ").strip()
    if choice.isdigit() and 1 <= int(choice) <= len(expenses):
        removed = expenses.pop(int(choice) - 1)
        print(f"  Deleted: {removed['description']} (Rs. {removed['amount']:.2f})")
    elif choice != "":
        print("  Invalid number. Nothing deleted.")


def filter_by_month(expenses, month):
    """Return only the expenses whose date starts with YYYY-MM."""
    return [item for item in expenses if item["date"].startswith(month)]


def total_expenses(expenses):
    return sum(item["amount"] for item in expenses)


def category_totals(expenses):
    """Return a dictionary mapping each category to the amount spent in it."""
    totals = {}
    for item in expenses:
        totals[item["category"]] = totals.get(item["category"], 0) + item["amount"]
    return totals


def highest_category(totals):
    """Return (category, amount) with the highest spending, or None."""
    if not totals:
        return None
    return max(totals.items(), key=lambda pair: pair[1])


def monthly_totals(expenses):
    """Return {'YYYY-MM': total spent} for every month that has expenses."""
    totals = {}
    for item in expenses:
        month = item["date"][:7]
        totals[month] = totals.get(month, 0) + item["amount"]
    return totals


def generate_alerts(income, budget, month_expenses):
    """Apply simple rules and return a list of alert/suggestion messages."""
    alerts = []
    total = total_expenses(month_expenses)
    totals = category_totals(month_expenses)

    # Rule 1: overall budget
    if total > budget:
        alerts.append(f"ALERT: Over budget by Rs. {total - budget:.2f}.")
    elif total >= WARNING_LEVEL * budget:
        alerts.append(f"WARNING: {total / budget * 100:.0f}% of budget used. "
                      "Spend carefully for the rest of the month.")

    # Rule 2: per-category limits
    for name, amount in totals.items():
        limit = CATEGORY_LIMITS[name] * budget
        if amount > limit:
            alerts.append(f"ALERT: {name} spending (Rs. {amount:.2f}) is above its "
                          f"suggested limit of Rs. {limit:.2f}.")

    # Rule 3: one category dominating spending
    top = highest_category(totals)
    if top and total > 0 and top[1] / total > DOMINANT_SHARE:
        alerts.append(f"SUGGESTION: {top[0]} takes {top[1] / total * 100:.0f}% of "
                      "your spending. Look for ways to reduce it.")

    # Rule 4: savings rate
    if income > 0 and (income - total) / income < MIN_SAVINGS_RATE:
        alerts.append("SUGGESTION: You are saving less than 20% of your income.")

    if not alerts and month_expenses:
        alerts.append("GOOD: Your spending looks healthy this month.")
    return alerts


# ---------- File handling (CSV) ----------

def save_to_csv(expenses, filename=FILE_NAME):
    with open(filename, "w", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(expenses)
    print(f"  Saved {len(expenses)} expense(s) to {filename}.")


def load_from_csv(filename=FILE_NAME):
    expenses = []
    try:
        with open(filename, newline="") as file:
            for row in csv.DictReader(file):
                row["amount"] = float(row["amount"])
                datetime.strptime(row["date"], "%Y-%m-%d")
                expenses.append(row)
        print(f"  Loaded {len(expenses)} saved expense(s) from {filename}.")
    except FileNotFoundError:
        print("  No saved expenses found. Starting fresh.")
    except (KeyError, ValueError):
        print("  Saved file is corrupted. Starting fresh.")
        expenses = []
    return expenses


# ---------- Output ----------

def view_expenses(expenses):
    if not expenses:
        print("  No expenses recorded yet.")
        return
    print(f"\n{'No.':<5}{'Date':<12}{'Description':<22}{'Category':<15}{'Amount':>10}")
    print("-" * 64)
    for number, item in enumerate(expenses, start=1):
        print(f"{number:<5}{item['date']:<12}{item['description'][:20]:<22}"
              f"{item['category']:<15}{item['amount']:>10.2f}")


def display_monthly_summary(income, budget, expenses):
    month = get_month("Month YYYY-MM (blank = current month): ")
    month_expenses = filter_by_month(expenses, month)
    total = total_expenses(month_expenses)
    totals = category_totals(month_expenses)
    top = highest_category(totals)

    print("\n" + "=" * 44)
    print(f"        SPENDING SUMMARY - {month}")
    print("=" * 44)
    print(f"Monthly income : Rs. {income:.2f}")
    print(f"Monthly budget : Rs. {budget:.2f}")
    print(f"Total expenses : Rs. {total:.2f}")
    print(f"Savings        : Rs. {income - total:.2f}")

    print("\nSpending by category:")
    if totals:
        for name, amount in sorted(totals.items(), key=lambda p: p[1], reverse=True):
            print(f"  {name:<15} Rs. {amount:>9.2f}  ({amount / total * 100:.1f}%)")
        print(f"\nHighest spending category: {top[0]} (Rs. {top[1]:.2f})")
    else:
        print("  (no expenses in this month)")

    print("\nBudget status:")
    if total > budget:
        print(f"  OVER budget by Rs. {total - budget:.2f}.")
    else:
        print(f"  Within budget. Rs. {budget - total:.2f} remaining "
              f"({total / budget * 100:.1f}% used).")

    print("\nAlerts and suggestions:")
    for message in generate_alerts(income, budget, month_expenses) or ["  (none)"]:
        print(f"  - {message}")
    print("=" * 44)


def display_month_comparison(budget, expenses):
    """Text bar chart comparing total spending of each month."""
    totals = monthly_totals(expenses)
    if not totals:
        print("  No expenses recorded yet.")
        return
    print(f"\n{'Month':<10}{'Total':>12}  {'Status':<8} Spending (each # = 5% of budget)")
    print("-" * 70)
    for month in sorted(totals):
        amount = totals[month]
        status = "OVER" if amount > budget else "OK"
        bar = "#" * int(amount / budget * 20)
        print(f"{month:<10}{amount:>12.2f}  {status:<8} {bar}")


# ---------- Main program ----------

def main():
    print("=== Personal Expense and Budget Analyzer ===\n")
    income = get_amount("Enter your monthly income (Rs.): ")
    budget = get_amount("Enter your monthly budget (Rs.): ")
    expenses = load_from_csv()

    while True:
        print("\n--- MENU ---")
        print("1. Add expense")
        print("2. View all expenses")
        print("3. Delete an expense")
        print("4. Monthly summary and alerts")
        print("5. Month-by-month comparison")
        print("6. Save and exit")
        choice = input("Enter choice (1-6): ").strip()

        if choice == "1":
            add_expense(expenses)
        elif choice == "2":
            view_expenses(expenses)
        elif choice == "3":
            delete_expense(expenses)
        elif choice == "4":
            display_monthly_summary(income, budget, expenses)
        elif choice == "5":
            display_month_comparison(budget, expenses)
        elif choice == "6":
            save_to_csv(expenses)
            print("Goodbye!")
            break
        else:
            print("  Invalid choice. Please enter a number from 1 to 6.")


if __name__ == "__main__":
    main()
