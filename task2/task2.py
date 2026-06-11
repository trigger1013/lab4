"""
Завдання №2
Створення заданої кількості процесів-нащадків.
Працює на Linux/macOS (fork + waitpid) та Windows (multiprocessing).

Кожен дочірній процес генерує псевдовипадкове число в діапазоні 0..1:
  - якщо число >= 0.5 -> процес завершується нормально (код 0)
  - якщо число  < 0.5 -> процес виконує нескінченний цикл

Батьківський процес:
  1. Засинає на 3 секунди.
  2. Перевіряє, які дочірні процеси вже завершились (без блокування).
  3. Виводить список процесів, що ще працюють.
  4. Засинає ще на 5 секунд.
  5. Завершує процеси, що залишились, і виводить причину завершення.
"""
import os
import sys
import time
import random
import multiprocessing as mp

from my_system import my_system

DEFAULT_COUNT = 10


# ---------------------------------------------------------------------------
# Логіка дочірнього процесу (використовується і на POSIX, і на Windows)
# ---------------------------------------------------------------------------

def child_worker(index: int) -> None:
    """
    Тіло дочірнього процесу.
    Запускається як ціль multiprocessing.Process.
    """
    random.seed(os.getpid())
    value = random.random()
    print(
        f"  Дочірній PID {os.getpid()} [#{index}]: value={value:.4f}",
        flush=True,
    )

    if value >= 0.5:
        print(
            f"  Дочірній PID {os.getpid()} [#{index}]: "
            f"успішне завершення (value={value:.4f} >= 0.5)",
            flush=True,
        )
        sys.exit(0)
    else:
        print(
            f"  Дочірній PID {os.getpid()} [#{index}]: "
            f"іду в нескінченний цикл (value={value:.4f} < 0.5)",
            flush=True,
        )
        while True:
            time.sleep(1)


# ---------------------------------------------------------------------------
# Звіт про завершення процесу
# ---------------------------------------------------------------------------

def report_exit(proc: mp.Process) -> None:
    """
    Виводить причину завершення процесу.

    multiprocessing.Process.exitcode:
      0        — нормальне завершення
      > 0      — завершення через помилку
      < 0      — завершення через сигнал (значення = -номер_сигналу)
      None     — процес ще працює
    """
    code = proc.exitcode
    pid = proc.pid

    if code is None:
        print(f"  PID {pid}: процес ще працює")
    elif code == 0:
        print(f"  PID {pid}: нормальне завершення з кодом 0")
    elif code > 0:
        print(f"  PID {pid}: завершення через помилку, код {code}")
    else:
        print(f"  PID {pid}: завершення через сигнал {-code}")


# ---------------------------------------------------------------------------
# Показати стан процесів через my_system (ps або tasklist)
# ---------------------------------------------------------------------------

def show_processes(pids: list[int], label: str) -> None:
    """Виводить рядки з інформацією про вказані PID."""
    print(f"\n--- {label} ({len(pids)} шт.) ---")
    for pid in pids:
        print(f"  PID {pid}")

    if os.name == "nt":
        pids_str = ",".join(str(p) for p in pids)
        my_system(
            f'tasklist /FI "PID eq {pids_str}" /FO TABLE'
        )
    else:
        pids_pattern = "|".join(str(p) for p in pids)
        my_system(
            f"ps aux | head -1 && "
            f"ps aux | grep -E '{pids_pattern}' | grep -v grep"
        )


# ---------------------------------------------------------------------------
# Головна функція
# ---------------------------------------------------------------------------

def main() -> None:
    count = DEFAULT_COUNT
    if len(sys.argv) > 1:
        try:
            count = int(sys.argv[1])
            if count < 1:
                raise ValueError
        except ValueError:
            print(
                f"Помилка: кількість процесів має бути натуральним "
                f"числом, отримано {sys.argv[1]!r}",
                file=sys.stderr,
            )
            sys.exit(1)

    ppid = os.getpid()

    if os.name == "nt":
        print(f"\n=== Стан процесів ДО запуску (PID {ppid}) ===")
        my_system(f'tasklist /FI "PID eq {ppid}" /FO TABLE')
    else:
        print(f"\n=== Стан процесів ДО запуску (grep {ppid}) ===")
        my_system(f"ps aux | grep -E 'PID|{ppid}' | grep -v grep")

    print(f"\nСтворюємо {count} дочірніх процесів...\n")

    processes: list[mp.Process] = []

    for i in range(count):
        proc = mp.Process(target=child_worker, args=(i,))
        proc.start()
        processes.append(proc)

    # -- крок 1: засипаємо на 3 секунди --
    print(f"\nБатьківський процес (PID {ppid}) засинає на 3 с...")
    time.sleep(3)

    # -- крок 2: перевіряємо, хто вже завершився (неблокуючий join) --
    print("\n--- Збираємо завершені дочірні процеси ---")
    still_running: list[mp.Process] = []

    for proc in processes:
        proc.join(timeout=0)          # неблокуючий — аналог WNOHANG
        if proc.is_alive():
            still_running.append(proc)
        else:
            report_exit(proc)

    # -- крок 3: виводимо список живих процесів --
    if still_running:
        show_processes(
            [p.pid for p in still_running],
            "Процеси, що ще працюють",
        )
    else:
        print("\nВсі дочірні процеси вже завершились.")

    # -- крок 4: засипаємо ще на 5 секунд --
    print("\nБатьківський процес засинає ще на 5 с...")
    time.sleep(5)

    # -- крок 5: завершуємо тих, хто залишився --
    if still_running:
        print("\n--- Завершуємо процеси, що ще працюють ---")
        for proc in still_running:
            if proc.is_alive():
                # SIGTERM на POSIX, TerminateProcess на Windows
                proc.terminate()
                print(f"  terminate() → PID {proc.pid}")

        time.sleep(0.5)

        print("\n--- Остаточно прибираємо з пам'яті ---")
        for proc in still_running:
            proc.join(timeout=2)
            report_exit(proc)

    if os.name == "nt":
        print(f"\n=== Стан процесів ПІСЛЯ завершення (PID {ppid}) ===")
        my_system(f'tasklist /FI "PID eq {ppid}" /FO TABLE')
    else:
        print(f"\n=== Стан процесів ПІСЛЯ завершення (grep {ppid}) ===")
        my_system(f"ps aux | grep -E 'PID|{ppid}' | grep -v grep")

    print("\nГотово.")


if __name__ == "__main__":
    # Обов'язково для Windows: захищає від рекурсивного spawn
    mp.freeze_support()
    main()
