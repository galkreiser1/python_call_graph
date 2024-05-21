def process_data(func, data):
    return [func(x) for x in data]

numbers = [1, 2, 3]
result = process_data(lambda x: x**3, numbers)