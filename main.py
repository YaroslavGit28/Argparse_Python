from __future__ import annotations

import json
import sys
import time
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from rich import box
from rich.console import Console
from rich.prompt import Prompt, Confirm, IntPrompt
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn, TimeElapsedColumn
from rich.panel import Panel
from rich.traceback import install

# Включаем красивый вывод трассировок ошибок
install(show_locals=True)

console = Console()
DATA_FILE = Path("tasks.json")


@dataclass
class Task:
    id: int
    title: str
    description: str
    status: str  # "todo", "in_progress", "done"
    priority: int  # 1..5
    created_at: str
    updated_at: str

    @staticmethod
    def from_dict(data: dict) -> "Task":
        return Task(
            id=data["id"],
            title=data["title"],
            description=data["description"],
            status=data["status"],
            priority=data["priority"],
            created_at=data["created_at"],
            updated_at=data["updated_at"],
        )


class TaskRepository:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.tasks: List[Task] = []
        self._load()

    def _load(self) -> None:
        if not self.path.exists():
            self.tasks = []
            return
        try:
            with self.path.open("r", encoding="utf-8") as f:
                raw = json.load(f)
            self.tasks = [Task.from_dict(item) for item in raw]
        except Exception as e:
            console.print(
                Panel.fit(
                    f"[red]Ошибка чтения файла данных:[/red] {e}\n"
                    f"Файл: {self.path.resolve()}",
                    title="Ошибка",
                    border_style="red",
                )
            )
            self.tasks = []

    def _save(self) -> None:
        data = [asdict(task) for task in self.tasks]
        with self.path.open("w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def next_id(self) -> int:
        if not self.tasks:
            return 1
        return max(task.id for task in self.tasks) + 1

    def add(self, title: str, description: str, priority: int) -> Task:
        now = datetime.now().isoformat(timespec="seconds")
        task = Task(
            id=self.next_id(),
            title=title,
            description=description,
            status="todo",
            priority=priority,
            created_at=now,
            updated_at=now,
        )
        self.tasks.append(task)
        self._save()
        return task

    def find(self, task_id: int) -> Optional[Task]:
        for t in self.tasks:
            if t.id == task_id:
                return t
        return None

    def update_status(self, task_id: int, new_status: str) -> bool:
        task = self.find(task_id)
        if not task:
            return False
        task.status = new_status
        task.updated_at = datetime.now().isoformat(timespec="seconds")
        self._save()
        return True

    def delete(self, task_id: int) -> bool:
        before = len(self.tasks)
        self.tasks = [t for t in self.tasks if t.id != task_id]
        if len(self.tasks) == before:
            return False
        self._save()
        return True

    def all(self) -> List[Task]:
        return list(self.tasks)

    def filter_by_status(self, status: str) -> List[Task]:
        return [t for t in self.tasks if t.status == status]


def render_tasks_table(tasks: List[Task], title: str = "Список задач") -> None:
    table = Table(
        title=title,
        box=box.MINIMAL_DOUBLE_HEAD,
        show_lines=True,
        header_style="bold cyan",
    )
    table.add_column("ID", justify="right", style="bold")
    table.add_column("Заголовок", style="white")
    table.add_column("Статус", style="magenta")
    table.add_column("Приоритет", justify="center")
    table.add_column("Создана", style="dim")
    table.add_column("Обновлена", style="dim")

    status_colors = {
        "todo": "yellow",
        "in_progress": "blue",
        "done": "green",
    }

    for task in tasks:
        status_text = f"[{status_colors.get(task.status, 'white')}]{task.status}[/]"
        priority_stars = "★" * task.priority + "☆" * (5 - task.priority)
        table.add_row(
            str(task.id),
            task.title,
            status_text,
            f"[bold]{priority_stars}[/]",
            task.created_at,
            task.updated_at,
        )

    if not tasks:
        console.print(Panel("Пока нет задач", title=title, border_style="yellow"))
    else:
        console.print(table)


def show_header() -> None:
    console.print(
        Panel.fit(
            "[bold cyan]Трекер задач на базе библиотеки Rich[/bold cyan]\n"
            "[dim]Демонстрация работы с таблицами, прогрессом и ошибками[/dim]",
            border_style="cyan",
        )
    )


def show_menu() -> str:
    console.print(
        Panel.fit(
            "\n".join(
                [
                    "[bold]1[/bold] — Показать все задачи",
                    "[bold]2[/bold] — Добавить задачу",
                    "[bold]3[/bold] — Изменить статус задачи",
                    "[bold]4[/bold] — Удалить задачу",
                    "[bold]5[/bold] — Смоделировать выполнение задач (прогресс)",
                    "[bold]0[/bold] — Выход",
                ]
            ),
            title="Меню",
            border_style="green",
        )
    )
    return Prompt.ask("Выберите пункт", choices=["0", "1", "2", "3", "4", "5"], default="1")


def add_task_flow(repo: TaskRepository) -> None:
    console.print("[bold]Добавление новой задачи[/bold]")
    title = Prompt.ask("Заголовок задачи").strip()
    if not title:
        console.print("[red]Заголовок не может быть пустым[/red]")
        return
    description = Prompt.ask("Описание задачи (можно оставить пустым)", default="").strip()
    while True:
        try:
            priority = IntPrompt.ask("Приоритет (1 — низкий, 5 — высокий)", default=3)
            if not 1 <= priority <= 5:
                raise ValueError
            break
        except Exception:
            console.print("[red]Введите целое число от 1 до 5[/red]")
    task = repo.add(title, description, priority)
    console.print(
        Panel.fit(
            f"Задача [bold]{task.title}[/bold] (ID={task.id}) добавлена",
            border_style="green",
        )
    )


def change_status_flow(repo: TaskRepository) -> None:
    if not repo.all():
        console.print("[yellow]Нет задач для обновления статуса[/yellow]")
        return

    render_tasks_table(repo.all(), title="Текущие задачи")
    try:
        task_id = IntPrompt.ask("Введите ID задачи")
    except Exception:
        console.print("[red]Неверный ID[/red]")
        return

    task = repo.find(task_id)
    if not task:
        console.print(f"[red]Задача с ID={task_id} не найдена[/red]")
        return

    console.print(f"Текущий статус: [bold]{task.status}[/bold]")
    status = Prompt.ask(
        "Новый статус",
        choices=["todo", "in_progress", "done"],
        default=task.status,
    )
    ok = repo.update_status(task_id, status)
    if ok:
        console.print("[green]Статус успешно обновлён[/green]")
    else:
        console.print("[red]Не удалось обновить статус[/red]")


def delete_task_flow(repo: TaskRepository) -> None:
    if not repo.all():
        console.print("[yellow]Нет задач для удаления[/yellow]")
        return

    render_tasks_table(repo.all(), title="Текущие задачи")
    try:
        task_id = IntPrompt.ask("Введите ID задачи для удаления")
    except Exception:
        console.print("[red]Неверный ID[/red]")
        return

    task = repo.find(task_id)
    if not task:
        console.print(f"[red]Задача с ID={task_id} не найдена[/red]")
        return

    if not Confirm.ask(f"Точно удалить задачу [bold]{task.title}[/bold]?", default=False):
        console.print("[yellow]Удаление отменено[/yellow]")
        return

    ok = repo.delete(task_id)
    if ok:
        console.print("[green]Задача удалена[/green]")
    else:
        console.print("[red]Не удалось удалить задачу[/red]")


def simulate_progress_flow(repo: TaskRepository) -> None:
    tasks = repo.filter_by_status("in_progress") or repo.filter_by_status("todo")
    if not tasks:
        console.print("[yellow]Нет задач в статусе 'todo' или 'in_progress' для симуляции[/yellow]")
        return

    console.print(
        Panel.fit(
            "Симуляция выполнения задач с помощью прогресс-бара Rich",
            border_style="blue",
        )
    )

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        TimeElapsedColumn(),
        console=console,
        transient=True,
    ) as progress:
        task_ids = []
        for t in tasks:
            task_id = progress.add_task(f"Задача {t.id}: {t.title}", total=100)
            task_ids.append((task_id, t))

        # Простейшая симуляция — идём по шагам
        for step in range(0, 101, 10):
            for task_id, t in task_ids:
                progress.update(task_id, completed=step)
            time.sleep(0.2)

    # После симуляции все задачи помечаем как done
    for _, t in task_ids:
        repo.update_status(t.id, "done")

    console.print("[green]Симуляция завершена, задачи помечены как 'done'[/green]")


def main() -> None:
    repo = TaskRepository(DATA_FILE)
    show_header()

    while True:
        try:
            choice = show_menu()
            if choice == "0":
                console.print("[bold cyan]До встречи![/bold cyan]")
                break
            elif choice == "1":
                render_tasks_table(repo.all(), title="Все задачи")
            elif choice == "2":
                add_task_flow(repo)
            elif choice == "3":
                change_status_flow(repo)
            elif choice == "4":
                delete_task_flow(repo)
            elif choice == "5":
                simulate_progress_flow(repo)
        except KeyboardInterrupt:
            console.print("\n[red]Прерывание по Ctrl+C[/red]")
            if Confirm.ask("Выйти из программы?", default=True):
                break
        except Exception as e:
            # Демонстрация обработки ошибок + Rich Traceback
            console.print(
                Panel.fit(
                    f"[red]Непредвиденная ошибка:[/red] {e}",
                    title="Ошибка",
                    border_style="red",
                )
            )


if __name__ == "__main__":
    # Если rich не установлен, это проявится уже при импорте выше.
    # Здесь просто запускаем программу.
    try:
        main()
    except ModuleNotFoundError:
        sys.stderr.write(
            "Не установлена библиотека 'rich'. Установите её командой:\n"
            "    pip install rich\n"
        )
        raise


