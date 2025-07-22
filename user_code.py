async def process_data(data):
    # Фильтруем четные числа, возводим их в квадрат и суммируем
    sum_of_squares = sum(x ** 2 for x in data if x % 2 == 0)
    return sum_of_squares
