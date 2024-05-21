import os
import json
from graph_builder import GraphBuilder



def load_expected_output(filename):
    with open(filename, 'r') as file:
        return json.load(file)

def compare_graphs(generated, expected):
    generated_keys = set(generated.keys())
    expected_keys = set(expected.keys())

    soundness = all(set(expected[key]).issubset(set(generated.get(key, []))) for key in expected_keys)
    completeness = all(set(generated[key]).issubset(set(expected.get(key, []))) for key in generated_keys)

    return soundness, completeness


def run_benchmark(test_directory):
    test_path = os.path.join(test_directory, "main.py")
    expected_output_path = os.path.join(test_directory, "callgraph.json")

    with open(test_path, 'r') as file:
        test_code = file.read()

    builder = GraphBuilder()
    graph = builder.build_graph(test_code)
    generated_output = builder.serialize_graph(graph)

    output_path = os.path.join(test_directory, "generated_callgraph.json")
    with open(output_path, 'w') as f:
        f.write(generated_output)

    expected_output = load_expected_output(expected_output_path)
    generated_data = json.loads(generated_output)

    return compare_graphs(generated_data, expected_output)



if __name__ == "__main__":
    base_dir = './benchmarks/benchmarks'
    categories = [d for d in os.listdir(base_dir) if os.path.isdir(os.path.join(base_dir, d))]

    print_test_stats = True

    
    for category in categories:
        category_dir = os.path.join(base_dir, category)
        tests = [os.path.join(category_dir, d) for d in os.listdir(category_dir) if
                 os.path.isdir(os.path.join(category_dir, d))]

        sound_results = []
        complete_results = []
        for test_dir in tests:
            sound_result, complete_result = run_benchmark(test_dir)
            if(print_test_stats):
                print(f'test: {test_dir} || sound: {sound_result} || complete: {complete_result}')
            sound_results.append(sound_result)
            complete_results.append(complete_result)

        total_tests = len(sound_results)
        sound_correct = sum(sound_results)
        complete_correct = sum(complete_results)
        print(f"Total Tests in {category}: {total_tests}")
        print(f"Soundness in {category}: {sound_correct}/{total_tests} - {sound_correct / total_tests * 100:.2f}%")
        print(f"Completeness in {category}: {complete_correct}/{total_tests} - {complete_correct / total_tests * 100:.2f}%\n")