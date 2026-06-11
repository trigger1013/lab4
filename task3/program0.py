"""
Завдання №3 — Програма 0 (батьківська)

УВАГА: використовує os.fork() — лише POSIX (Linux/macOS).

Приймає два параметри командного рядка:
  n   — кількість рівних частин, на які розбивається інтервал [0, 1]
  num — кількість випробувань для кожного дочірнього процесу (NUM)
"""
import os
import sys


PROGRAM1 = os.path.join(os.path.dirname(__file__), "program1.py")


def check_posix() -> None:
    """Перевіряє, що скрипт запущено на POSIX-системі."""
    if os.name == "nt":
        print(
            "Помилка: програма використовує os.fork() і "
            "підтримується лише на Linux/macOS.",
            file=sys.stderr,
        )
        sys.exit(1)


def main() -> None:
    check_posix()

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

    step = 1.0 / n
    intervals = [
        (round(i * step, 10), round((i + 1) * step, 10))
        for i in range(n)
    ]

    env = os.environ.copy()
    env["NUM"] = str(num)

    print(f"Запускаємо {n} дочірніх процесів, NUM={num}\n")

    child_pids: list[tuple[int, float, float]] = []

    for a, b in intervals:
        pid = os.fork()

        if pid < 0:
            print(
                f"fork() failed для інтервалу [{a}, {b}]",
                file=sys.stderr,
            )
            continue

        if pid == 0:
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

    total = sum(c for _, _, c in results)
    print("-" * 60)
    print(f"{'Сума':>33}  {total:>10}  {num:>12}")
    print(
        f"\nОчікувана сума ≈ {num} "
        "(усі відрізки покривають [0,1] без крайніх точок)"
    )


if __name__ == "__main__":
    main()
