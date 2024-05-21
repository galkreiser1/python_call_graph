def process_data(data):
    #Bug: mistakenly calls process_results instead of preparing_data
    prepared_data = process_results(data)
    return prepared_data

def prepare_data(data):
    cleaned_data = [d for d in data if d > 0]
    return cleaned_data

def process_results(data):
    #Bug: calls process_data, creating a mutual recursion
    results = process_data(data)
    return sum(results)

def main():
    data = [10, -1, 20, 5, -3]
    processed = process_data(data)
    print(f"Processed Data: {processed}")

main()
