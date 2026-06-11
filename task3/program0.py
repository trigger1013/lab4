"""
Завдання №3 - Програма 0 (батьківська).
Працює на Linux/macOS (fork + execvpe) та Windows (subprocess).

Приймає два параметри командного рядка:
  n   - кількість рівних частин, на які розбивається інтервал [0, 1]
  num - кількість випробувань для кожного дочірнього процесу (NUM)

Розбиває [0, 1] на n відрізків, запускає n дочірніх процесів
(кожен виконує program1.py зі своїм інтервалом), збирає результати
через коди завершення і виводить таблицю.
"""
import os
import sys
import subprocess

PROGRAM1 = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "program1.py"
)


def parse_args() -> tuple[int, int]:
    """Розбирає та валідує аргументи командного рядка."""
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

    return n, num


# ---------------------------------------------------------------------------
# POSIX: fork + execvpe
# ---------------------------------------------------------------------------

def run_posix(
    intervals: list[tuple[float, float]], env: dict[str, str]
) -> list[tuple[int, float, float]]:
    """
    Запускає дочірні процеси через fork()+execvpe() на POSIX.
    Повертає список (pid, a, b).
    """
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

    return child_pids


def collect_posix(
    child_pids: list[tuple[int, float, float]], num: int
) -> None:
    """Очікує завершення дочірніх процесів і виводить таблицю (POSIX)."""
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

    print_summary(results, num)


# ---------------------------------------------------------------------------
# Windows: subprocess.Popen
# ---------------------------------------------------------------------------

def run_windows(
    intervals: list[tuple[float, float]], env: dict[str, str]
) -> list[tuple["subprocess.Popen[bytes]", float, float]]:
    """
    Запускає дочірні процеси через subprocess.Popen() на Windows.
    Повертає список (proc, a, b).
    """
    procs: list[tuple[subprocess.Popen[bytes], float, float]] = []

    for a, b in intervals:
        proc = subprocess.Popen(
            [sys.executable, PROGRAM1, str(a), str(b)],
            env=env,
        )
        procs.append((proc, a, b))

    return procs


def collect_windows(
    procs: list[tuple["subprocess.Popen[bytes]", float, float]],
    num: int,
) -> None:
    """Очікує завершення дочірніх процесів і виводить таблицю (Windows)."""
    results: list[tuple[float, float, int]] = []

    for proc, a, b in procs:
        proc.wait()
        code = proc.returncode
        pid = proc.pid

        if code >= 0:
            theoretical = round((b - a) * num)
            results.append((a, b, code))
            print(
                f"{pid:>8}  [{a:.6f}, {b:.6f}]  "
                f"{code:>10}  {theoretical:>12}"
            )
        else:
            print(
                f"{pid:>8}  [{a:.6f}, {b:.6f}]"
                f"  завершено примусово (код {code})"
            )

    print_summary(results, num)


# ---------------------------------------------------------------------------
# Підсумок (спільний)
# ---------------------------------------------------------------------------

def print_summary(
    results: list[tuple[float, float, int]], num: int
) -> None:
    total = sum(c for _, _, c in results)
    print("-" * 60)
    print(f"{'Сума':>33}  {total:>10}  {num:>12}")
    print(
        f"\nОчікувана сума ≈ {num} "
        "(усі відрізки покривають [0,1] без крайніх точок)"
    )


# ---------------------------------------------------------------------------
# Точка входу
# ---------------------------------------------------------------------------

def main() -> None:
    n, num = parse_args()

    step = 1.0 / n
    intervals = [
        (round(i * step, 10), round((i + 1) * step, 10))
        for i in range(n)
    ]

    env = os.environ.copy()
    env["NUM"] = str(num)

    print(f"Запускаємо {n} дочірніх процесів, NUM={num}\n")

    header = (
        f"{'PID':>8}  {'Інтервал':^22}  "
        f"{'Кількість':>10}  {'Теоретично':>12}"
    )
    print(header)
    print("-" * 60)

    if os.name == "nt":
        procs = run_windows(intervals, env)
        collect_windows(procs, num)
    else:
        child_pids = run_posix(intervals, env)
        collect_posix(child_pids, num)


if __name__ == "__main__":
    main()
