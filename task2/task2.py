"""
Завдання №2
Створення заданої кількості процесів-нащадків.

Кожен дочірній процес генерує псевдовипадкове число в діапазоні 0..1:
  - якщо число >= 0.5 → процес завершується нормально (код 0)
  - якщо число  < 0.5 → процес виконує нескінченний цикл

Батьківський процес:
  1. Засинає на 3 секунди.
  2. Збирає (waitpid WNOHANG) вже завершені дочірні процеси.
  3. Виводить список процесів, що ще працюють.
  4. Засинає ще на 5 секунд.
  5. Надсилає SIGTERM решті процесів і збирає їх.
"""
import os
import sys
import time
import random
import signal

from my_system import my_system

DEFAULT_COUNT = 10


def report_exit(pid: int, status: int) -> None:
    """Виводить причину завершення процесу з PID pid."""
    if os.WIFEXITED(status):
        code = os.WEXITSTATUS(status)
        if code == 0:
            print(f"  PID {pid}: нормальне завершення з кодом 0")
        else:
            print(f"  PID {pid}: завершення через помилку, код {code}")
    elif os.WIFSIGNALED(status):
        sig = os.WTERMSIG(status)
        print(f"  PID {pid}: завершення через сигнал {sig}")
    else:
        print(f"  PID {pid}: невідомий статус {status}")


def main() -> None:
    count = DEFAULT_COUNT
    if len(sys.argv) > 1:
        try:
            count = int(sys.argv[1])
            if count < 1:
                raise ValueError
        except ValueError:
            print(
                f"Помилка: кількість процесів має бути натуральним числом, "
                f"отримано {sys.argv[1]!r}",
                file=sys.stderr,
            )
            sys.exit(1)

    print(f"\n=== Стан процесів ДО запуску (ps aux | grep {os.getpid()}) ===")
    my_system(f"ps aux | grep -E 'PID|{os.getpid()}' | grep -v grep")

    print(f"\nСтворюємо {count} дочірніх процесів...\n")

    child_pids: list[int] = []

    for i in range(count):
        pid = os.fork()

        if pid < 0:
            print(f"fork() failed для процесу #{i}", file=sys.stderr)
            continue

        if pid == 0:
            # ---------- дочірній процес ----------
            random.seed(os.getpid())
            value = random.random()
            print(
                f"  Дочірній PID {os.getpid()} [#{i}]: value={value:.4f}",
                flush=True,
            )

            if value >= 0.5:
                print(
                    f"  Дочірній PID {os.getpid()} [#{i}]: "
                    f"успішне завершення (value={value:.4f} >= 0.5)",
                    flush=True,
                )
                os._exit(0)
            else:
                print(
                    f"  Дочірній PID {os.getpid()} [#{i}]: "
                    f"іду в нескінченний цикл (value={value:.4f} < 0.5)",
                    flush=True,
                )
                while True:
                    time.sleep(1)
        else:
            # ---------- батьківський процес ----------
            child_pids.append(pid)

    # -- крок 1: засипаємо на 3 секунди --
    print(f"\nБатьківський процес (PID {os.getpid()}) засинає на 3 с...")
    time.sleep(3)

    # -- крок 2: збираємо завершені процеси (WNOHANG) --
    print("\n--- Збираємо завершені дочірні процеси ---")
    still_running: list[int] = []

    for pid in child_pids:
        result_pid, status = os.waitpid(pid, os.WNOHANG)
        if result_pid == 0:
            still_running.append(pid)
        else:
            report_exit(pid, status)

    # -- крок 3: виводимо список живих процесів --
    if still_running:
        print(f"\n--- Процеси, що ще працюють ({len(still_running)} шт.) ---")
        for pid in still_running:
            print(f"  PID {pid}")
        my_system(
            "ps aux | head -1 && ps aux | grep -E '"
            + "|".join(str(p) for p in still_running)
            + "' | grep -v grep"
        )
    else:
        print("\nВсі дочірні процеси вже завершились.")

    # -- крок 4: засипаємо ще на 5 секунд --
    print("\nБатьківський процес засинає ще на 5 с...")
    time.sleep(5)

    # -- крок 5: завершуємо процеси-нащадки, що залишились --
    if still_running:
        print("\n--- Надсилаємо SIGTERM процесам, що ще працюють ---")
        for pid in still_running:
            try:
                os.kill(pid, signal.SIGTERM)
                print(f"  SIGTERM → PID {pid}")
            except ProcessLookupError:
                print(f"  PID {pid} вже не існує")

        # Даємо трохи часу завершитись
        time.sleep(0.5)

        print("\n--- Остаточно прибираємо з пам'яті ---")
        for pid in still_running:
            try:
                result_pid, status = os.waitpid(pid, 0)
                report_exit(result_pid, status)
            except ChildProcessError:
                print(f"  PID {pid}: вже зібрано або не існує")

    ppid = os.getpid()
    print(
        f"\n=== Стан процесів ПІСЛЯ завершення (ps aux | grep {ppid}) ==="
    )
    my_system(f"ps aux | grep -E 'PID|{ppid}' | grep -v grep")

    print("\nГотово.")


if __name__ == "__main__":
    main()
