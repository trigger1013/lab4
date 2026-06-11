"""
Завдання №3 — Програма 1 (дочірня)

Отримує через аргументи командного рядка два дійсних числа a та b
(0 < a < b < 1).
Через змінну оточення NUM (за замовчуванням 500) отримує кількість
випробувань. NUM разів генерує псевдовипадкове число в діапазоні 0..1,
підраховує, скільки разів число потрапляє в [a, b],
та повертає цей підрахунок як код завершення (max 255).
"""
import os
import sys
import random


def main() -> None:
    if len(sys.argv) != 3:
        print(
            f"Використання: {sys.argv[0]} <a> <b>",
            file=sys.stderr,
        )
        os._exit(1)

    try:
        a = float(sys.argv[1])
        b = float(sys.argv[2])
    except ValueError:
        print(
            "Помилка: a та b мають бути дійсними числами.",
            file=sys.stderr,
        )
        os._exit(1)

    if not (0 < a < b < 1):
        print("Помилка: необхідно 0 < a < b < 1.", file=sys.stderr)
        os._exit(1)

    num_str = os.environ.get("NUM", "500")
    try:
        num = int(num_str)
        if num < 1:
            raise ValueError
    except ValueError:
        print(
            f"Помилка: NUM={num_str!r} не є натуральним числом.",
            file=sys.stderr,
        )
        os._exit(1)

    random.seed(os.getpid())
    count = sum(1 for _ in range(num) if a <= random.random() <= b)

    exit_code = min(count, 255)
    os._exit(exit_code)


if __name__ == "__main__":
    main()
