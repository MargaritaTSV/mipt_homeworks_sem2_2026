#!/usr/bin/env python
from typing import Any

UNKNOWN_COMMAND_MSG = "Unknown command!"
NONPOSITIVE_VALUE_MSG = "Value must be grater than zero!"
INCORRECT_DATE_MSG = "Invalid date!"
NOT_EXISTS_CATEGORY = "Category not exists!"
SUCCESS_MSG = "Added"


EXPENSE_CATEGORIES = {
    "Food": ("Supermarket", "Restaurants", "FastFood", "Coffee", "Delivery"),
    "Transport": ("Taxi", "Public transport", "Gas", "Car service"),
    "Housing": ("Rent", "Utilities", "Repairs", "Furniture"),
    "Health": ("Pharmacy", "Doctors", "Dentist", "Lab tests"),
    "Entertainment": ("Movies", "Concerts", "Games", "Subscriptions"),
    "Clothing": ("Outerwear", "Casual", "Shoes", "Accessories"),
    "Education": ("Courses", "Books", "Tutors"),
    "Communications": ("Mobile", "Internet", "Subscriptions"),
    "Other": ("Other",),
}

financial_transactions_storage: list[dict[str, Any]] = []

PARTS = 3
MIN_MONTH_NUMBER = 1
MAX_MONTH_NUMBER = 12
CATEGORY_PARTS = 2

INCOME_COMMAND_LEN = 3
COST_CATEGORIES_COMMAND_LEN = 2
COST_COMMAND_LEN = 4
STATS_COMMAND_LEN = 2

DAY_INDEX = 0
MONTH_INDEX = 1
YEAR_INDEX = 2

AMOUNT_KEY = "amount"
DATE_KEY = "date"
CATEGORY_KEY = "category"

SEPARATOR = "::"
NEW_LINE = "\n"
ZERO_FLOAT = float(0)


def is_divisible(number: int, divisor: int) -> bool:
    return number % divisor == 0


def is_century_year(year: int) -> bool:
    return is_divisible(year, 100)


def is_leap_year(year: int) -> bool:
    if is_divisible(year, 400):
        return True
    if is_century_year(year):
        return False
    return is_divisible(year, 4)


def split_date_parts(maybe_dt: str) -> list[str] | None:
    array_with_date = maybe_dt.split("-")
    if len(array_with_date) != PARTS:
        return None
    return array_with_date


def parse_date_numbers(parts: list[str]) -> tuple[int, int, int] | None:
    if not all(part.isdigit() for part in parts):
        return None

    day = int(parts[DAY_INDEX])
    month = int(parts[MONTH_INDEX])
    year = int(parts[YEAR_INDEX])
    return day, month, year


def get_days_in_month(year: int) -> dict[int, int]:
    return {
        1: 31,
        2: 29 if is_leap_year(year) else 28,
        3: 31,
        4: 30,
        5: 31,
        6: 30,
        7: 31,
        8: 31,
        9: 30,
        10: 31,
        11: 30,
        12: 31,
    }


def has_normal_month(month: int) -> bool:
    return MIN_MONTH_NUMBER <= month <= MAX_MONTH_NUMBER


def has_normal_day(day: int, month: int, year: int) -> bool:
    if day < 1:
        return False
    return day <= get_days_in_month(year)[month]


def parse_date(maybe_dt: str) -> tuple[int, int, int] | None:
    date_parts = split_date_parts(maybe_dt)
    if date_parts is None:
        return None

    parsed_numbers = parse_date_numbers(date_parts)
    if parsed_numbers is None:
        return None

    day, month, year = parsed_numbers
    if not has_normal_month(month):
        return None
    if not has_normal_day(day, month, year):
        return None

    return parsed_numbers


def is_normal_number(number_part: str) -> bool:
    return number_part.isdigit()


def parse_amount(raw_number: str) -> float | None:
    normalized_number = raw_number.replace(",", ".")
    is_valid = True

    if normalized_number.count(".") > 1 or normalized_number == "":
        is_valid = False
    else:
        number_part = normalized_number.removeprefix("-")
        if number_part == "":
            is_valid = False
        elif "." in number_part:
            left_part, right_part = number_part.split(".")
            is_valid = (
                    left_part != ""
                    and right_part != ""
                    and is_normal_number(left_part)
                    and is_normal_number(right_part)
            )
        else:
            is_valid = is_normal_number(number_part)

    if is_valid:
        return float(normalized_number)
    return None


def is_normal_category(category_name: str) -> bool:
    split_category = category_name.split(SEPARATOR)
    if len(split_category) != CATEGORY_PARTS:
        return False

    vast_category, narrow_category = split_category
    if vast_category not in EXPENSE_CATEGORIES:
        return False

    return narrow_category in EXPENSE_CATEGORIES[vast_category]


def cost_categories_handler() -> str:
    all_categories: list[str] = []

    for common_category, target_categories in EXPENSE_CATEGORIES.items():
        all_categories.extend(
            f"{common_category}{SEPARATOR}{target_category}"
            for target_category in target_categories
        )

    return NEW_LINE.join(all_categories)


def income_transaction(
    amount: float,
    date: tuple[int, int, int],
) -> dict[str, Any]:
    return {
        AMOUNT_KEY: amount,
        DATE_KEY: date,
    }


def cost_transaction(
    category: str,
    amount: float,
    date: tuple[int, int, int],
) -> dict[str, Any]:
    return {
        CATEGORY_KEY: category,
        AMOUNT_KEY: amount,
        DATE_KEY: date,
    }


def income_handler(amount: float, date: str) -> str:
    if amount <= 0:
        financial_transactions_storage.append({})
        return NONPOSITIVE_VALUE_MSG

    parsed_date = parse_date(date)
    if parsed_date is None:
        financial_transactions_storage.append({})
        return INCORRECT_DATE_MSG

    financial_transactions_storage.append(
        income_transaction(amount, parsed_date),
    )
    return SUCCESS_MSG


def cost_handler(category_name: str, amount: float, cost_date: str) -> str:
    if amount <= 0:
        financial_transactions_storage.append({})
        return NONPOSITIVE_VALUE_MSG

    parsed_date = parse_date(cost_date)
    if parsed_date is None:
        financial_transactions_storage.append({})
        return INCORRECT_DATE_MSG

    if not is_normal_category(category_name):
        financial_transactions_storage.append({})
        return NOT_EXISTS_CATEGORY

    financial_transactions_storage.append(
        cost_transaction(category_name, amount, parsed_date),
    )
    return SUCCESS_MSG


def update_category_statistics(
    category_stats: dict[str, float],
    category_name: str,
    amount: float,
) -> None:
    short_category_name = category_name.split(SEPARATOR)[1]
    current_value = category_stats.get(short_category_name, ZERO_FLOAT)
    category_stats[short_category_name] = current_value + amount


def get_transaction_date_like_tuple(
    transaction: dict[str, Any],
) -> tuple[int, int, int] | None:
    transaction_date = transaction[DATE_KEY]

    if isinstance(transaction_date, tuple):
        return transaction_date
    if isinstance(transaction_date, str):
        return parse_date(transaction_date)
    return None


def get_transaction_amount(transaction: dict[str, Any]) -> float:
    amount = transaction[AMOUNT_KEY]
    if isinstance(amount, float):
        return amount
    return float(amount)


def is_transaction_normal_for_stats(transaction: dict[str, Any]) -> bool:
    if not transaction:
        return False
    if get_transaction_amount(transaction) <= 0:
        return False
    if get_transaction_date_like_tuple(transaction) is None:
        return False
    if CATEGORY_KEY not in transaction:
        return True
    return is_normal_category(transaction[CATEGORY_KEY])


def process_transaction_for_total(
    transaction: dict[str, Any],
    report_date_tuple: tuple[int, int, int],
    total: float,
) -> float:
    if not is_transaction_normal_for_stats(transaction):
        return total

    transaction_date = get_transaction_date_like_tuple(transaction)
    if transaction_date is None:
        return total
    if not is_not_after(transaction_date, report_date_tuple):
        return total

    transaction_amount = get_transaction_amount(transaction)
    if CATEGORY_KEY in transaction:
        return total - transaction_amount
    return total + transaction_amount


def process_transaction_for_month(
    transaction: dict[str, Any],
    report_date_tuple: tuple[int, int, int],
    month_income: float,
    month_expenses: float,
    category_stats: dict[str, float],
) -> tuple[float, float]:
    if not is_transaction_normal_for_stats(transaction):
        return month_income, month_expenses

    transaction_date = get_transaction_date_like_tuple(transaction)
    if transaction_date is None:
        return month_income, month_expenses
    if not (
            is_same_month(transaction_date, report_date_tuple)
            and is_not_after(transaction_date, report_date_tuple)
    ):
        return month_income, month_expenses

    transaction_amount = get_transaction_amount(transaction)
    category_name = transaction.get(CATEGORY_KEY)
    if category_name is None:
        month_income += transaction_amount
        return month_income, month_expenses

    month_expenses += transaction_amount
    update_category_statistics(category_stats, category_name, transaction_amount)
    return month_income, month_expenses


def get_result(difference_in_this_month: float) -> str:
    if difference_in_this_month >= 0:
        return f"This month, the profit amounted to {difference_in_this_month:.2f} rubles."

    loss = abs(difference_in_this_month)
    return f"This month, the loss amounted to {loss:.2f} rubles."


def make_lines(category_stats: dict[str, float]) -> list[str]:
    detailed_lines = ["Details (category: amount):"]
    sorted_categories = sorted(category_stats)

    for index, category_name in enumerate(sorted_categories, start=1):
        detailed_lines.append(
            f"{index}. {category_name}: {category_stats[category_name]:.2f}",
        )

    return detailed_lines


def build_answer(
    date: str,
    total: float,
    income: float,
    expenses: float,
    stats_by_category: dict[str, float],
) -> str:
    difference_in_month = income - expenses
    lines = [
        f"Your statistics as of {date}:",
        f"Total capital: {total:.2f} rubles",
        get_result(difference_in_month),
        f"Income: {income:.2f} rubles",
        f"Expenses: {expenses:.2f} rubles",
        "",
        *make_lines(stats_by_category),
    ]
    return NEW_LINE.join(lines)


def get_initial_stats() -> tuple[float, float, float, dict[str, float]]:
    return ZERO_FLOAT, ZERO_FLOAT, ZERO_FLOAT, {}


def get_report_date(report_date: str) -> tuple[int, int, int] | None:
    return parse_date(report_date)


def collect_stats(
    report_date_tuple: tuple[int, int, int],
) -> tuple[float, float, float, dict[str, float]]:
    capital, income, expenses, category_stats = get_initial_stats()

    for transaction in financial_transactions_storage:
        capital = process_transaction_for_total(transaction, report_date_tuple, capital)
        income, expenses = process_transaction_for_month(
            transaction,
            report_date_tuple,
            income,
            expenses,
            category_stats,
        )

    return capital, income, expenses, category_stats


def stats_handler(report_date: str) -> str:
    report_date_tuple = get_report_date(report_date)
    if report_date_tuple is None:
        return INCORRECT_DATE_MSG

    collected_stats = collect_stats(report_date_tuple)
    return build_answer(report_date, *collected_stats)


def get_year_month_day(date_value: tuple[int, int, int]) -> tuple[int, int, int]:
    day, month, year = date_value
    return year, month, day


def is_not_after(
    first_date: tuple[int, int, int],
    second_date: tuple[int, int, int],
) -> bool:
    return get_year_month_day(first_date) <= get_year_month_day(second_date)


def is_same_month(
    first_date: tuple[int, int, int],
    second_date: tuple[int, int, int],
) -> bool:
    return (
        first_date[MONTH_INDEX] == second_date[MONTH_INDEX]
        and first_date[YEAR_INDEX] == second_date[YEAR_INDEX]
    )


def check_income_command(parts: list[str]) -> str:
    if len(parts) != INCOME_COMMAND_LEN:
        return UNKNOWN_COMMAND_MSG

    amount = parse_amount(parts[1])
    if amount is None or amount <= 0:
        return NONPOSITIVE_VALUE_MSG

    return income_handler(amount, parts[2])


def check_cost_command(parts: list[str]) -> str:
    if len(parts) == COST_CATEGORIES_COMMAND_LEN and parts[1] == "categories":
        return cost_categories_handler()

    if len(parts) != COST_COMMAND_LEN:
        return UNKNOWN_COMMAND_MSG

    category_name = parts[1]
    if not is_normal_category(category_name):
        return NEW_LINE.join([NOT_EXISTS_CATEGORY, cost_categories_handler()])

    amount = parse_amount(parts[2])
    if amount is None or amount <= 0:
        return NONPOSITIVE_VALUE_MSG

    return cost_handler(category_name, amount, parts[3])


def check_stats_command(parts: list[str]) -> str:
    if len(parts) != STATS_COMMAND_LEN:
        return UNKNOWN_COMMAND_MSG

    return stats_handler(parts[1])


def get_result(parts: list[str]) -> str:
    if not parts:
        return UNKNOWN_COMMAND_MSG

    action = parts[0]
    if action == "income":
        return check_income_command(parts)
    if action == "cost":
        return check_cost_command(parts)
    if action == "stats":
        return check_stats_command(parts)
    return UNKNOWN_COMMAND_MSG


def main() -> None:
    for command in iter(input, ""):
        print(get_result(command.split()))


if __name__ == "__main__":
    main()
