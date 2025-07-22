import ctypes
import re
import tkinter as tk
from tkinter import messagebox
from typing import List, Optional, Tuple

from core.logic import validate_user_code
from core.task_config import get_task
from entities import BG_COLOR, CODE_COLORS, FG_COLOR, HIGHLIGHT_PATTERNS

USER_CODE_FILE = "user_code.py"
TASK, EXAMPLES = get_task()

try:
    ctypes.windll.shcore.SetProcessDpiAwareness(1)
except Exception:
    pass


def search_re(pattern: str, text: str) -> List[Tuple[str, str]]:
    """
    Ищет все совпадения регулярного выражения в тексте.

    Аргументы:
        pattern: Регулярное выражение для поиска
        text: Текст для поиска совпадений

    Возвращает:
        Список кортежей с позициями совпадений в формате:
        [(начальная_позиция, конечная_позиция), ...]
        где позиции заданы как "строка.символ"
    """
    matches = []
    lines = text.splitlines()
    for i, line in enumerate(lines):
        for match in re.finditer(pattern, line):
            matches.append((f"{i + 1}.{match.start()}", f"{i + 1}.{match.end()}"))
    return matches


def highlight(event: Optional[tk.Event] = None) -> None:
    """
    Подсвечивает синтаксис в текстовом поле кода.

    Аргументы:
        event: Событие tkinter (необязательное)
    """
    global previousText
    text = code_input.get("1.0", tk.END)
    if text == previousText:
        return

    for tag in code_input.tag_names():
        code_input.tag_remove(tag, "1.0", tk.END)

    i = 0
    for pattern, color in HIGHLIGHT_PATTERNS:
        for start, end in search_re(pattern, text):
            code_input.tag_add(f"tag{i}", start, end)
            code_input.tag_config(f"tag{i}", foreground=color)
            i += 1

    previousText = text


def highlight_error_line(line_number: Optional[int]) -> None:
    """
    Подсвечивает строку с ошибкой в редакторе кода.

    Аргументы:
        line_number: Номер строки с ошибкой (или None)
    """
    code_input.tag_remove("error_line", "1.0", tk.END)
    if line_number is None:
        return
    start = f"{line_number}.0"
    end = f"{line_number}.end"
    code_input.tag_add("error_line", start, end)
    code_input.tag_config("error_line", background="#FFCCCC")


def submit_code() -> None:
    """Обрабатывает отправку кода на проверку."""
    user_code = code_input.get("1.0", tk.END)
    with open(USER_CODE_FILE, "w", encoding="utf-8") as f:
        f.write(user_code)
    try:
        valid, result, error_line = validate_user_code(user_code, EXAMPLES)
        highlight_error_line(error_line)
        if not valid:
            messagebox.showerror("Ошибка", result)
            return
    except TimeoutError as e:
        messagebox.showerror("Ошибка", str(e))
    except Exception as e:
        messagebox.showerror("Ошибка", f"Неожиданная ошибка:\n{e}")

    output_text.config(state=tk.NORMAL)
    output_text.delete("1.0", tk.END)
    output_text.insert(tk.END, f"Тесты и метрики:\n{result}\n")
    output_text.config(state=tk.DISABLED)


def refresh_task() -> None:
    """Обновляет задание и примеры."""
    global TASK, EXAMPLES
    TASK, EXAMPLES = get_task()
    task_label.config(text=TASK.strip())
    examples_label.config(
        text="\n".join([f"Input: {i} → Output: {o}" for i, o in EXAMPLES])
    )


def create_gui() -> None:
    """
    Создает и настраивает графический интерфейс приложения.

    Содержит:
    - Описание задачи
    - Примеры ввода/вывода
    - Редактор кода с подсветкой синтаксиса
    - Кнопки управления
    - Поле вывода результатов
    """
    window = tk.Tk()
    window.title("Async Test Framework")
    window.geometry("1000x800")
    window.configure(bg=BG_COLOR)

    # Описание задачи
    tk.Label(
        window,
        text="Описание задачи",
        font=("Arial", 14, "bold"),
        bg=BG_COLOR,
        fg=FG_COLOR,
    ).pack(pady=(10, 0))

    global task_label
    task_label = tk.Label(
        window,
        text=TASK.strip(),
        wraplength=900,
        justify="left",
        bg=BG_COLOR,
        fg=FG_COLOR,
    )
    task_label.pack(padx=10)

    # Примеры
    tk.Label(
        window, text="Примеры", font=("Arial", 12, "bold"), bg=BG_COLOR, fg=FG_COLOR
    ).pack(pady=(10, 0))

    global examples_label
    examples_label = tk.Label(
        window,
        text="\n".join([f"Input: {i} → Output: {o}" for i, o in EXAMPLES]),
        wraplength=900,
        justify="left",
        bg=BG_COLOR,
        fg=FG_COLOR,
    )
    examples_label.pack(padx=10)

    # Редактор кода
    tk.Label(
        window,
        text="Введите код функции",
        font=("Arial", 12, "bold"),
        bg=BG_COLOR,
        fg=FG_COLOR,
    ).pack(pady=(10, 0))

    global code_input
    code_input = tk.Text(
        window,
        background=CODE_COLORS["background"],
        foreground=CODE_COLORS["normal"],
        insertbackground=CODE_COLORS["normal"],
        relief=tk.SUNKEN,
        borderwidth=2,
        font=CODE_COLORS["font"],
        height=20,
    )
    code_input.pack(fill=tk.BOTH, expand=1, padx=10)
    code_input.bind("<KeyRelease>", highlight)

    # Кнопки управления
    button_frame = tk.Frame(window, bg=BG_COLOR)
    button_frame.pack(pady=10)
    tk.Button(
        button_frame,
        text="Проверить",
        command=submit_code,
        bg="lightgreen",
        fg="black",
        width=15,
    ).pack(side="left", padx=10)
    tk.Button(
        button_frame,
        text="Новое задание",
        command=refresh_task,
        bg="lightblue",
        fg="black",
        width=15,
    ).pack(side="left", padx=10)

    # Поле вывода
    tk.Label(
        window, text="Результат", font=("Arial", 12, "bold"), bg=BG_COLOR, fg=FG_COLOR
    ).pack(pady=(10, 0))

    global output_text
    output_text = tk.Text(
        window,
        height=12,
        width=100,
        bg="white",
        fg="black",
        state=tk.DISABLED,
        relief=tk.SUNKEN,
        borderwidth=2,
    )
    output_text.pack(padx=10, pady=(0, 10))

    highlight()
    window.mainloop()


if __name__ == "__main__":
    create_gui()
