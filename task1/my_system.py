"""
Завдання №1
Реалізація функції my_system() — спрощеного аналога system()
з використанням fork(), exec(), wait().
"""
import os
import sys


def my_system(command: str) -> int:
    """
    Запускає команду оболонки у дочірньому процесі.

    Створює дочірній процес через fork(), виконує команду через
    execvp() (передаючи її оболонці /bin/sh -c), та очікує
    на завершення дочірнього процесу через waitpid().

    Args:
        command: рядок з командою оболонки.

    Returns:
        Код завершення дочірнього процесу, або -1 у разі помилки fork().
    """
    pid = os.fork()

    if pid < 0:
        print("my_system: fork() failed", file=sys.stderr)
        return -1

    if pid == 0:
        # Дочірній процес: замінюємо образ процесу командою через sh
        try:
            os.execvp("/bin/sh", ["/bin/sh", "-c", command])
        except OSError as e:
            print(f"my_system: execvp failed: {e}", file=sys.stderr)
            os._exit(127)
    else:
        # Батьківський процес: очікуємо завершення дочірнього
        _, status = os.waitpid(pid, 0)

        if os.WIFEXITED(status):
            return os.WEXITSTATUS(status)
        elif os.WIFSIGNALED(status):
            print(
                f"my_system: child killed by signal {os.WTERMSIG(status)}",
                file=sys.stderr,
            )
            return -1

    return -1


if __name__ == "__main__":
    print("=== Демонстрація my_system() ===\n")

    commands = [
        "echo 'Hello from my_system!'",
        "ls -la /tmp | head -5",
        "date",
        "uname -a",
        "exit 42",
    ]

    for cmd in commands:
        print(f">> my_system({cmd!r})")
        ret = my_system(cmd)
        print(f"   exit code: {ret}\n")
