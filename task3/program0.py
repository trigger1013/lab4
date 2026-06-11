"""
Завдання №3 — Програма 0 (батьківська)

Приймає два параметри командного рядка:
  n   — кількість рівних частин, на які розбивається інтервал [0, 1]
  num — кількість випробувань для кожного дочірнього процесу (NUM)

Розбиває [0, 1] на n відрізків [a_i, b_i], встановлює NUM=num,
запускає n дочірніх процесів (кожен виконує program1.py з своїм [a_i, b_i]),
очікує завершення всіх і виводить отримані від них результати.
"""
import os
import sys


PROGRAM1 = os.path.join(os.path.dirname(__file__), "program1.py")


def main() -> None:
    if len(sys.argv) != 3:
        print(f"Використання: {sys.argv[0]} <n> <num>", file=sys.stderr)
        sys.exit(1)

    try:
        n = int(sys.argv[1])
        num = int(sys.argv[2])
        if n < 1 or num < 1:
            raise ValueError
    except ValueError:
        print(
            "Помилка: n та num мають бути натуральними числами.",
            file=sys.stderr,
        )
        sys.exit(1)

    # Розбиваємо [0, 1] на n рівних частин
    step = 1.0 / n
    intervals = [
        (round(i * step, 10), round((i + 1) * step, 10))
        for i in range(n)
    ]

    # Встановлюємо змінну оточення NUM для дочірніх процесів
    env = os.environ.copy()
    env["NUM"] = str(num)

    print(f"Запускаємо {n} дочірніх процесів, NUM={num}\n")

    child_pids: list[tuple[int, float, float]] = []

    for a, b in intervals:
        pid = os.fork()

        if pid < 0:
            print(f"fork() failed для інтервалу [{a}, {b}]", file=sys.stderr)
            continue

        if pid == 0:
            # Дочірній процес: запускаємо program1.py через execvpe
            try:
                os.execvpe(
                    sys.executable,
                    [sys.executable, PROGRAM1, str(a), str(b)],
                    env,
                )
            except OSError as e:
                print(f"execvpe failed: {e}", file=sys.stderr)
                os._exit(1)
        else:
            child_pids.append((pid, a, b))

    # Очікуємо завершення всіх дочірніх процесів
    header = (
        f"{'PID':>8}  {'Інтервал':^22}  "
        f"{'Кількість':>10}  {'Теоретично':>12}"
    )
    print(header)
    print("-" * 60)

    results: list[tuple[float, float, int]] = []

    for pid, a, b in child_pids:
        _, status = os.waitpid(pid, 0)

        if os.WIFEXITED(status):
            count = os.WEXITSTATUS(status)
            theoretical = round((b - a) * num)
            results.append((a, b, count))
            print(
                f"{pid:>8}  [{a:.6f}, {b:.6f}]  "
                f"{count:>10}  {theoretical:>12}"
            )
        elif os.WIFSIGNALED(status):
            sig = os.WTERMSIG(status)
            print(
                f"{pid:>8}  [{a:.6f}, {b:.6f}]"
                f"  завершено сигналом {sig}"
            )

    # Підсумок
    total = sum(c for _, _, c in results)
    print("-" * 60)
    print(f"{'Сума':>33}  {total:>10}  {num:>12}")
    print(
        f"\nОчікувана сума ≈ {num} "
        "(усі відрізки покривають [0,1] без крайніх точок)"
    )


if __name__ == "__main__":
    main()
