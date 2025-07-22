import time
import tracemalloc

import pytest
import pytest_asyncio

from core.logic import get_user_function, run_user_solution_with_timeout
from core.task_config import EXAMPLES, get_task

process_data = get_user_function()
assert process_data is not None, "Функция process_data не загружена из user_code.py"


@pytest_asyncio.fixture
async def processed_data(request):
    func, input_data = request.param
    return await func(input_data)


@pytest.mark.parametrize(
    "processed_data,expected",
    [((lambda d: process_data, inp), out) for inp, out in EXAMPLES],
    indirect=True,
)
@pytest.mark.asyncio
def test_user_function(processed_data, expected):
    assert processed_data == expected


@pytest.mark.asyncio
async def test_user_code_performance():
    TASK, EXAMPLES = get_task()

    MAX_TIME = 0.5 # секунды
    MAX_MEMORY_MB = 10 

    for inp, expected in EXAMPLES:
        tracemalloc.start()
        start_time = time.perf_counter()

        result = await run_user_solution_with_timeout(inp)

        end_time = time.perf_counter()
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()

        exec_time = end_time - start_time
        peak_mb = peak / (1024 * 1024)

        assert result == expected, f"Неверный результат для входа {inp}"
        assert exec_time <= MAX_TIME, (
            f"Превышено время выполнения: {exec_time:.3f} сек > {MAX_TIME}"
        )
        assert peak_mb <= MAX_MEMORY_MB, (
            f"Превышено использование памяти: {peak_mb:.2f} МБ > {MAX_MEMORY_MB}"
        )
