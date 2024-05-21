def format_data(data):
    return [f"Data: {x}" for x in data]

def sort_data(data):
    return sorted(data, key=lambda x: x.split(":")[1].strip())

def display_data(data):
    for item in data:
        print(item)

def main():
    data = ["10", "2", "33", "25"]
    formatted_data = format_data(data)
    sorted_data = format_data(formatted_data)  # Bug here, should call sort_data
    display_data(sorted_data)

main()
