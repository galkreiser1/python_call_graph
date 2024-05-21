def validate_data(data):
    if len(data) < 5:
        return False
    return True

def clean_data(data):
    return [x.strip() for x in data if x]

def analyze_data(data):
    if not validate_data(data):
        print("Data is invalid.")
    else:
        print("Data is valid.")
    return sum(map(int, data)) / len(data)

def main():
    data = [" 23", "42 ", " 36", "", "18"]
    cleaned_data = clean_data(data)
    result = analyze_data(data)  # Bug here, should pass cleaned_data
    print("Average:", result)

main()
