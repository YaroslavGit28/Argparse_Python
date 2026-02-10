"""
argparse_demo.py

Обучающая программа для знакомства с модулем argparse.

Показывает:
- позиционные и опциональные аргументы;
- типы, значения по умолчанию, choices;
- флаги (store_true / store_false);
- группы взаимоисключающих аргументов;
- подкоманды (subparsers) с отдельными обработчиками;
- разбор аргументов из файла (fromfile_prefix_chars);
- оформление вывода в виде аккуратных текстовых блоков для более понятного интерфейса.
"""

from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import List


@dataclass
class AppConfig:
    verbose: bool
    output: str | None


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="argparse-demo",
        description=(
            "Обучающий пример использования модуля argparse.\n"
            "Программа демонстрирует несколько подкоманд и разные типы аргументов."
        ),
        epilog=(
            "Примеры использования:\n"
            "  argparse-demo greet Alex --times 3 --shout\n"
            "  argparse-demo calc add 1 2 3 4 --precise\n"
            "  argparse-demo file stats sample.txt --verbose\n"
            "  argparse-demo @args.txt  (аргументы из файла)"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        fromfile_prefix_chars="@",
    )

    # Глобальные опции
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="подробный вывод (дополнительная отладочная информация)",
    )
    parser.add_argument(
        "-o",
        "--output",
        metavar="PATH",
        help="если указано — вывод сохранить в файл, а не в стандартный вывод",
    )

    # Подкоманды
    subparsers = parser.add_subparsers(
        title="подкоманды",
        dest="command",
        required=True,
        metavar="COMMAND",
        help="действие, которое нужно выполнить (например, greet, calc, file)",
    )

    # Подкоманда greet
    greet = subparsers.add_parser(
        "greet",
        help="приветствие пользователя",
        description="Печатает одно или несколько приветствий для указанного имени.",
    )
    greet.add_argument("name", help="имя человека, которого надо поприветствовать")
    greet.add_argument(
        "-t",
        "--times",
        type=int,
        default=1,
        help="сколько раз вывести приветствие (по умолчанию 1)",
    )
    greet.add_argument(
        "--shout",
        action="store_true",
        help="если указано — печатать прописными буквами",
    )
    greet.set_defaults(func=handle_greet)

    # Подкоманда calc
    calc = subparsers.add_parser(
        "calc",
        help="простые арифметические операции",
        description="Выполняет арифметические операции над списком чисел.",
    )
    calc.add_argument(
        "operation",
        choices=["add", "sub", "mul", "div"],
        help="операция: add, sub, mul, div",
    )
    calc.add_argument(
        "numbers",
        type=float,
        nargs="+",
        help="список чисел для обработки",
    )
    # Взаимоисключающая группа — формат вывода
    fmt_group = calc.add_mutually_exclusive_group()
    fmt_group.add_argument(
        "--int",
        dest="as_int",
        action="store_true",
        help="вывести результат как целое число (округление)",
    )
    fmt_group.add_argument(
        "--precise",
        dest="precise",
        action="store_true",
        help="вывести результат с высокой точностью",
    )
    calc.set_defaults(func=handle_calc)

    # Подкоманда file
    file_cmd = subparsers.add_parser(
        "file",
        help="операции с файлами (пример работы с Path и ошибками)",
        description="Простейшая статистика по текстовому файлу.",
    )
    file_sub = file_cmd.add_subparsers(
        title="действия с файлом",
        dest="file_command",
        required=True,
        metavar="FILE_CMD",
    )

    stats_cmd = file_sub.add_parser(
        "stats",
        help="подсчитать строки, слова и символы в файле",
    )
    stats_cmd.add_argument(
        "path",
        type=Path,
        help="путь к текстовому файлу",
    )
    stats_cmd.set_defaults(func=handle_file_stats)

    return parser


def get_config(args: argparse.Namespace) -> AppConfig:
    return AppConfig(verbose=bool(getattr(args, "verbose", False)), output=args.output)


def write_output(lines: List[str], config: AppConfig) -> None:
    """
    Единая точка вывода результатов.

    Для наглядности все результаты оборачиваются в "рамку" из символов,
    чтобы визуально отделять блоки информации друг от друга.
    """
    frame = "=" * 50
    text = "\n".join([frame, *lines, frame])

    if config.output:
        path = Path(config.output)
        path.write_text(text, encoding="utf-8")
        print(f"[INFO] Результат записан в файл: {path}")
    else:
        print(text)


def handle_greet(args: argparse.Namespace, config: AppConfig) -> None:
    name = args.name
    times = args.times
    if times < 1:
        raise SystemExit("Количество повторов должно быть >= 1")

    base = f"Привет, {name}!"
    if args.shout:
        base = base.upper()

    header = f"Блок приветствия для: {name}"
    lines = [header, "-" * len(header)]
    for i in range(times):
        if config.verbose:
            lines.append(f"[{i + 1}] {base}")
        else:
            lines.append(base)

    write_output(lines, config)


def handle_calc(args: argparse.Namespace, config: AppConfig) -> None:
    nums = args.numbers
    op = args.operation

    if op == "add":
        result = sum(nums)
        desc = "сумма"
    elif op == "sub":
        result = nums[0]
        for n in nums[1:]:
            result -= n
        desc = "вычитание"
    elif op == "mul":
        result = 1
        for n in nums:
            result *= n
        desc = "умножение"
    elif op == "div":
        result = nums[0]
        for n in nums[1:]:
            if n == 0:
                raise SystemExit("Деление на ноль запрещено")
            result /= n
        desc = "деление"
    else:
        raise SystemExit(f"Неизвестная операция: {op}")

    if args.as_int:
        display = str(int(round(result)))
    elif args.precise:
        display = f"{result:.10f}"
    else:
        display = str(result)

    header = f"Блок калькулятора: {op}"
    lines = [
        header,
        "-" * len(header),
        f"Операция: {desc}",
        f"Числа: {nums}",
        f"Результат: {display}",
    ]
    if config.verbose:
        lines.insert(0, "[DEBUG] режим подробного вывода включён")

    write_output(lines, config)


def handle_file_stats(args: argparse.Namespace, config: AppConfig) -> None:
    path: Path = args.path
    if not path.exists():
        raise SystemExit(f"Файл не найден: {path}")
    if not path.is_file():
        raise SystemExit(f"Ожидался файл, но это не файл: {path}")

    text = path.read_text(encoding="utf-8")
    lines_count = text.count("\n") + (0 if text.endswith("\n") else 1 if text else 0)
    words_count = len(text.split())
    chars_count = len(text)

    header = f"Статистика по файлу"
    result_lines = [
        header,
        "-" * len(header),
        f"Файл: {path}",
        f"Строк: {lines_count}",
        f"Слов: {words_count}",
        f"Символов: {chars_count}",
    ]
    if config.verbose:
        result_lines.append("[DEBUG] Подсчёт завершён успешно")

    write_output(result_lines, config)


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()

    if argv is None:
        argv = sys.argv[1:]

    args = parser.parse_args(argv)
    config = get_config(args)

    # Каждая подкоманда записывает в args.func обработчик
    if not hasattr(args, "func"):
        parser.print_help()
        return 1

    try:
        args.func(args, config)
    except SystemExit as e:
        # Перехватываем SystemExit, чтобы показать дружелюбное сообщение
        if e.code:
            print(f"[ERROR] {e}")
        return int(e.code or 0)
    except Exception as e:  # общая защита (для учебных целей)
        print(f"[UNEXPECTED ERROR] {e}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


