import asyncio
import cProfile
import io
import multiprocessing
import pstats
import threading
from typing import (
    Any,
    Callable,
    Coroutine,
    Dict,
    List,
    Literal,
    Optional,
    Tuple,
    Union,
)

from core.aync_test_runner import InputType, OutputType, run_all_tests
from user_code import process_data

ProcessResult = Tuple[Literal["result", "error", "timeout"], Union[OutputType, str]]
ProfileResult = Tuple[Any, str]


def run_user_code_in_process(
    queue: multiprocessing.Queue, user_code_str: str, input_data: InputType
) -> None:
    """
    Запускает user_code.process_data(input_data) в отдельном процессе.

    Аргументы:
        queue: Очередь для передачи результата
        user_code_str: Строка с кодом пользователя (если нужно динамически загружать)
        input_data: Входные данные для функции process_data

    Результат (кортеж (статус, результат)) помещается в очередь:
        - ("result", результат) при успешном выполнении
        - ("error", сообщение_ошибки) при возникновении исключения
    """
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(process_data(input_data))
        queue.put(("result", result))
    except Exception as e:
        queue.put(("error", str(e)))


def run_with_timeout(
    user_code_str: str, input_data: InputType, timeout_sec: float
) -> ProcessResult:
    """
    Запускает выполнение пользовательского кода с ограничением по времени.

    Аргументы:
        user_code_str: Строка с кодом пользователя
        input_data: Входные данные для обработки
        timeout_sec: Максимальное время выполнения в секундах

    Возвращает:
        Кортеж (статус, результат):
        - ("result", результат) при успешном выполнении
        - ("error", сообщение_ошибки) при ошибке
        - ("timeout", сообщение) при превышении времени
    """
    queue = multiprocessing.Queue()
    p = multiprocessing.Process(
        target=run_user_code_in_process, args=(queue, user_code_str, input_data)
    )
    p.start()

    def join_process():
        p.join(timeout_sec)
        if p.is_alive():
            p.terminate()
            p.join()

    thread = threading.Thread(target=join_process)
    thread.start()
    thread.join(timeout_sec + 0.1)

    if p.is_alive():
        p.terminate()
        p.join()
        return "timeout", "Превышено время выполнения"

    if not queue.empty():
        return queue.get()
    else:
        return "error", "Нет результата"


def run_cprofile(
    func: Callable[..., OutputType], *args: Any, **kwargs: Any
) -> ProfileResult:
    """
    Запускает функцию с профилированием cProfile.

    Аргументы:
        func: Функция для профилирования
        *args: Позиционные аргументы для функции
        **kwargs: Именованные аргументы для функции

    Возвращает:
        Кортеж (результат_функции, строковое_представление_статистики)
    """
    profiler = cProfile.Profile()
    profiler.enable()
    result = func(*args, **kwargs)
    profiler.disable()

    s = io.StringIO()
    ps = pstats.Stats(profiler, stream=s).sort_stats("cumulative")
    ps.print_stats(10)
    stats_output = s.getvalue()
    return result, stats_output


async def run_async_func(
    coro_func: Callable[[InputType], Coroutine[Any, Any, OutputType]], arg: InputType
) -> OutputType:
    """
    Запускает асинхронную функцию с заданным аргументом.

    Аргументы:
        coro_func: Асинхронная функция для выполнения
        arg: Аргумент для передачи в функцию

    Возвращает:
        Результат выполнения асинхронной функции
    """
    return await coro_func(arg)


def validate_user_code(
    user_code: str, test_cases: List[Tuple[Any, Any]]
) -> Tuple[bool, str, Optional[int]]:
    """
    Валидирует пользовательский код и запускает тесты.

    Аргументы:
        user_code: Строка с кодом пользователя
        test_cases: Список тест-кейсов в формате [(вход, ожидаемый_результат)]

    Возвращает:
        Кортеж (успех, отчет, номер_строки_с_ошибкой):
        - успех: True если все тесты пройдены
        - отчет: Текстовый отчет о выполнении тестов
        - номер_строки: None или номер строки с синтаксической ошибкой
    """
    local_vars: Dict[str, Any] = {}
    try:
        exec(user_code, {}, local_vars)
        user_func = local_vars.get("process_data")
        if not asyncio.iscoroutinefunction(user_func):
            return (
                False,
                "Функция process_data должна быть асинхронной (async def)",
                None,
            )
    except SyntaxError as e:
        return False, f"Синтаксическая ошибка: {e.msg} в строке {e.lineno}", e.lineno
    except Exception as e:
        return False, f"Ошибка при загрузке функции: {e}", None

    try:
        results = asyncio.run(run_all_tests(user_func, test_cases))
    except Exception as e:
        return False, f"Ошибка выполнения тестов: {e}", None

    all_passed = True
    report_lines = []
    for i, res in enumerate(results, 1):
        status = "✅" if res["passed"] else "❌"
        if not res["passed"]:
            all_passed = False
        time_info = f"{res['time']:.3f} с" if res["time"] else "—"
        report_lines.append(f"Тест {i}: {status} Время: {time_info}")
        if not res["passed"]:
            if res["error"]:
                report_lines.append(f"Ошибка:\n{res['error']}")
            else:
                report_lines.append(
                    f"Ожидалось: {res['expected']}, получили: {res['result']}"
                )

    return all_passed, "\n".join(report_lines), None
