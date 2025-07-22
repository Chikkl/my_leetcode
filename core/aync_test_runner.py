import asyncio
import time
import traceback
from typing import (
    Any,
    Callable,
    Coroutine,
    Dict,
    List,
    Optional,
    Tuple,
    TypeVar,
    Union,
)

InputType = TypeVar("InputType")
OutputType = TypeVar("OutputType")
ErrorType = Union[str, None]


async def run_single_test(
    user_func: Callable[[InputType], Coroutine[Any, Any, OutputType]],
    input_data: InputType,
    expected_output: OutputType,
    timeout: float = 3.0,
) -> Dict[
    str,
    Union[
        InputType, OutputType, Optional[OutputType], bool, Optional[float], ErrorType
    ],
]:
    """
    Запускает один тест для асинхронной пользовательской функции.

    Аргументы:
        user_func: Асинхронная функция для тестирования, принимающая InputType и возвращающая OutputType
        input_data: Входные данные для теста типа InputType
        expected_output: Ожидаемый результат работы функции типа OutputType
        timeout: Максимальное время выполнения в секундах (по умолчанию 3.0)

    Возвращает:
        Словарь с результатами теста:
        {
            'input': InputType,  # исходные входные данные
            'expected': OutputType,  # ожидаемый результат
            'result': Optional[OutputType],  # фактический результат или None при ошибке
            'passed': bool,  # True если тест пройден
            'time': Optional[float],  # время выполнения в секундах или None при ошибке
            'error': ErrorType  # сообщение об ошибке или None
        }
    """
    try:
        start = time.perf_counter()
        result = await asyncio.wait_for(user_func(input_data), timeout=timeout)
        duration = time.perf_counter() - start
        passed = result == expected_output
        return {
            "input": input_data,
            "expected": expected_output,
            "result": result,
            "passed": passed,
            "time": duration,
            "error": None,
        }
    except asyncio.TimeoutError:
        return {
            "input": input_data,
            "expected": expected_output,
            "result": None,
            "passed": False,
            "time": None,
            "error": "TimeoutError: выполнение превысило лимит времени",
        }
    except Exception:
        tb = traceback.format_exc()
        return {
            "input": input_data,
            "expected": expected_output,
            "result": None,
            "passed": False,
            "time": None,
            "error": tb,
        }


async def run_all_tests(
    user_func: Callable[[InputType], Coroutine[Any, Any, OutputType]],
    test_cases: List[Tuple[InputType, OutputType]],
) -> List[
    Dict[
        str,
        Union[
            InputType,
            OutputType,
            Optional[OutputType],
            bool,
            Optional[float],
            ErrorType,
        ],
    ]
]:
    """
    Запускает набор тестов для асинхронной пользовательской функции.

    Аргументы:
        user_func: Асинхронная функция для тестирования
        test_cases: Список кортежей с тест-кейсами в формате (входные_данные, ожидаемый_результат)

    Возвращает:
        Список словарей с результатами тестов (структура как в run_single_test)
    """
    tasks = [run_single_test(user_func, inp, out) for inp, out in test_cases]
    results = await asyncio.gather(*tasks)
    return results
