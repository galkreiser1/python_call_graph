import ast
import networkx as nx
import astor
import json
from networkx.readwrite import json_graph
import sys
import matplotlib.pyplot as plt
import builtins

MAX_ITERATION = 50


class GraphBuilder(ast.NodeVisitor):
    def __init__(self, module_name='main'):
        self.graph = nx.DiGraph()
        self.current_function = None
        self.changed = True
        self.function_lists = {}
        self.lambda_counter = 0
        self.lambda_set = set()
        self.module_functions = {}
        self.current_module = module_name
        self.imported_functions = {}
        self.current_class = None
        self.known_classes = set()
        self.instance_map = {}
        self.func_aliases = {}
        self.builtin_types = {'list', 'dict', 'set', 'tuple', 'str', 'int', 'float'}
        self.lambda_aliases = {}
        self.class_aliases = {}

    def visit_Import(self, node):
        for alias in node.names:
            alias_name = alias.asname if alias.asname else alias.name
            self.graph.add_node(alias_name, type='module', lineno=node.lineno)
            self.module_functions[alias_name] = []

    def visit_ImportFrom(self, node):
        module = node.module
        for alias in node.names:
            alias_name = alias.asname if alias.asname else alias.name
            full_name = f'{node.module}.{alias_name}'
            self.graph.add_node(full_name, type='function', lineno=node.lineno)
            self.module_functions.setdefault(module, []).append(alias.name)
            self.imported_functions[alias_name] = (node.module, alias_name)
            self.func_aliases[alias_name] = alias_name

    def visit_FunctionDef(self, node):

        self.func_aliases[node.name] = node.name
        func_name = self.get_full_name(node.name)
        prev_function = self.current_function
        self.current_function = func_name
        if self.current_module:
            if func_name not in self.graph:
                self.graph.add_node(func_name, type='function', lineno=node.lineno)
                self.changed = True
            elif node.decorator_list:
                for decorator in node.decorator_list:
                    if isinstance(decorator, ast.Name):
                        self.graph.add_edge(decorator.id, func_name, type='decorates')
        if self.current_class:
            class_full_name = f'{self.current_module}.{self.current_class}'
            if not self.graph.has_edge(class_full_name, func_name):
                self.graph.add_edge(class_full_name, func_name, type='contains')
                self.changed = True

        self.generic_visit(node)
        self.current_function = prev_function

    def visit_Assign(self, node):
        """Handles variable assignments within functions"""
        from_node = self.current_function if self.current_function else self.current_module
        if isinstance(node.value, ast.Name) and self.is_function(self.get_full_name(node.value.id)):
            for target in node.targets:
                if isinstance(target, ast.Subscript) and isinstance(target.value, ast.Name):
                    func_name = self.get_full_name(node.value.id)
                    if not self.graph.has_edge(from_node, func_name):
                        self.graph.add_edge(from_node, func_name, type='potential_call')
                        self.changed = True
        if isinstance(node.value, ast.Call) and isinstance(node.value.func, ast.Name):
            func_name = node.value.func.id
            if func_name in self.known_classes:
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        self.instance_map[target.id] = func_name
        if isinstance(node.value, ast.Name) and node.value.id in self.class_aliases:
            for target in node.targets:
                if isinstance(target, ast.Name):
                    self.class_aliases[target.id] = self.class_aliases[node.value.id]
        if isinstance(node.value, ast.Lambda):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    lambda_label = f"{from_node}.lambda"
                    try:
                        lambda_source = astor.to_source(node).split('=')[1].strip()
                        lambda_label += f": {lambda_source}"
                    except Exception as e:
                        print(f"Error converting lambda to source: {e}")
                    self.graph.add_edge(self.get_full_name(target.id), lambda_label, type='defines')
                    if lambda_label in self.lambda_aliases:  # Direct alias of a function
                        self.lambda_aliases[target.id] = lambda_label
        # Handling list assignments
        if isinstance(node.value, ast.List):
            for elt in node.value.elts:
                if isinstance(elt, ast.Name):
                    to_node = self.get_full_name(elt.id)
                    if self.is_function(to_node):
                        if not self.graph.has_edge(from_node, to_node):
                            self.graph.add_edge(from_node, to_node, type='potential_call')
                            self.changed = True

        # Assignment from one variable to another
        if isinstance(node.value, ast.Name):
            source = node.value.id
            if not any(isinstance(t, ast.Subscript) for t in node.targets):
                targets = []
                for t in node.targets:
                    if hasattr(t, 'id'):
                        targets.append(t.id)
                for target in targets:
                    if source in self.func_aliases:
                        self.func_aliases[target] = self.func_aliases[source]
        # Assignment from a function call
        if isinstance(node.value, ast.Call):
            if isinstance(node.value.func, ast.Name):
                called_func = node.value.func.id
                targets = []
                for t in node.targets:
                    if hasattr(t, 'id'):
                        targets.append(t.id)
                for target in targets:
                    self.func_aliases[target] = called_func
        if isinstance(node.value, ast.Tuple) and all(isinstance(el, ast.Name) for el in node.value.elts):
            source_functions = [el.id for el in node.value.elts]
            if isinstance(node.targets[0], ast.Tuple) and len(node.targets[0].elts) == len(source_functions):
                target_names = [target.id for target in node.targets[0].elts]
                for target_name, func_name in zip(target_names, source_functions):
                    # Assign the function name to the target variable
                    self.func_aliases[target_name] = func_name

        self.generic_visit(node)

    def visit_Call(self, node):
        # Handles function calls

        from_function = self.current_function if self.current_function else self.current_module
        if isinstance(node.func, ast.Attribute) and \
                isinstance(node.func.value, ast.Call) and \
                isinstance(node.func.value.func, ast.Name) and \
                node.func.value.func.id == "super":

            method_or_function_name = node.func.attr
            resolved_method = self.resolve_method(self.current_class, method_or_function_name, True)
            if resolved_method and not self.graph.has_edge(self.current_function, resolved_method):
                self.graph.add_edge(f"{self.current_function}", resolved_method, type='call')
                self.changed = True

        if isinstance(node.func, ast.Name):
            func_name = node.func.id
            if func_name in self.func_aliases:
                # Call through an alias
                actual_func = self.func_aliases[func_name]
                full_name = self.get_full_name(actual_func)
                self.graph.add_edge(from_function, full_name, type='call')
            elif func_name in self.imported_functions:
                module_name, _ = self.imported_functions[func_name]
                full_name = f"{module_name}.{func_name}"
                if not self.graph.has_edge(from_function, full_name):
                    self.graph.add_edge(from_function, full_name, type='call')
                    self.change = True
            elif func_name in self.lambda_aliases:
                lambda_label = self.lambda_aliases[func_name]
                qualified_name = f"{from_function}.{func_name}"
                if self.graph.has_edge(qualified_name, lambda_label):
                    self.graph.remove_edge(qualified_name, lambda_label)
                    self.graph.remove_node(qualified_name)

                if not self.graph.has_edge(from_function, lambda_label):
                    self.graph.add_edge(from_function, lambda_label, type='call')
                    self.change = True
            elif func_name != "range" and func_name != "super":
                full_name = self.get_full_name(func_name)
                init_method = ''
                if func_name in self.known_classes:
                    init_method = self.resolve_method(func_name, '__init__')
                if self.current_function:
                    if not self.graph.has_edge(self.current_function, full_name):
                        self.graph.add_edge(self.current_function, full_name, type='call')
                        self.change = True
                    if init_method and not self.graph.has_edge(self.current_function, init_method):
                        self.graph.add_edge(self.current_function, init_method, type='call')
                        self.change = True
                elif not self.current_class:
                    if not self.graph.has_edge(self.current_module, full_name):
                        self.graph.add_edge(self.current_module, full_name, type='call')
                        self.change = True
                    if init_method and not self.graph.has_edge(self.current_module, init_method):
                        self.graph.add_edge(self.current_module, init_method, type='call')
                        self.change = True
            # Handling functions as arguments to other functions.
        if isinstance(node.func, ast.Name) and node.func.id in self.graph.nodes():
            callee_function = node.func.id
            full_name = self.get_full_name(callee_function)
            for arg in node.args:
                arg_full_name = ""
                if arg.id in self.imported_functions:
                    module_name, _ = self.imported_functions[arg.id]
                    arg_full_name = f"{module_name}.{arg.id}"
                else:
                    arg_full_name = self.get_full_name(arg.id)
                if isinstance(arg, ast.Name) and arg_full_name in self.graph.nodes():
                    if not self.graph.has_edge(full_name, arg_full_name):
                        self.graph.add_edge(full_name, arg_full_name, type='dynamic-call')
                        self.change = True
        # Handling list of functions
        if isinstance(node.func, ast.Subscript) and isinstance(node.func.value, ast.Name):
            list_name = node.func.value.id
            if list_name in self.function_lists:
                # Add edges for all functions in the list as potential calls
                for func_name in self.function_lists[list_name]:
                    full_name = self.get_full_name(func_name)
                    if not self.graph.has_edge(from_function, full_name):
                        self.graph.add_edge(from_function, full_name, type='dynamic-call')
                        self.changed = True

        if isinstance(node.func, ast.Attribute) and (
                isinstance(node.func.value, ast.Name) or isinstance(node.func.value, ast.Str) or (
        node.func.value, ast.Num)):
            instance_or_module_name = node.func.value
            method_or_function_name = node.func.attr

            if isinstance(node.func.value, ast.Name) or hasattr(node.func.value, 'id'):
                instance_or_module_name = node.func.value.id

            if instance_or_module_name == 'self' and self.current_class:
                # Ensure that self-references within a class do not create separate nodes
                resolved_method = self.resolve_method(self.current_class, method_or_function_name)
                if resolved_method and not self.graph.has_edge(from_function, resolved_method):
                    self.graph.add_edge(from_function, resolved_method, type='call')
                    self.changed = True

            # Check if the name refers to a known class instance
            elif instance_or_module_name in self.instance_map or instance_or_module_name in self.known_classes:
                qualified_name = f"{instance_or_module_name}.{method_or_function_name}"
                if self.graph.has_edge(from_function, qualified_name):
                    self.graph.remove_edge(from_function, qualified_name)
                    self.graph.remove_node(qualified_name)
                    # self.changed = True
                class_name = self.instance_map[
                    instance_or_module_name] if instance_or_module_name in self.instance_map else instance_or_module_name
                if class_name:
                    resolved_method = self.resolve_method(class_name, method_or_function_name)
                    if resolved_method and not self.graph.has_edge(from_function, resolved_method):
                        self.graph.add_edge(from_function, resolved_method, type='call')
                        self.changed = True
            # Check if the name refers to a known module
            elif self.graph.has_node(instance_or_module_name) and self.graph.nodes[instance_or_module_name].get(
                    'type') == "module":
                qualified_name = f'{node.func.value.id}.{method_or_function_name}'
                self.graph.add_edge(from_function, qualified_name, type='call')
                self.graph.remove_node(instance_or_module_name)
            else:
                qualified_name = f'{instance_or_module_name}.{method_or_function_name}'
                if method_or_function_name in dir(builtins):
                    qualified_name = f"<builtin>.{method_or_function_name}"
                else:
                    for var_type in self.builtin_types:
                        if hasattr(getattr(builtins, var_type, None), method_or_function_name):
                            qualified_name = f"<builtin>.{method_or_function_name}"
                if qualified_name and not self.graph.has_edge(from_function, qualified_name) and not isinstance(
                        instance_or_module_name, ast.Call):
                    self.graph.add_edge(from_function, qualified_name, type='call')
                    self.changed = True

            # Check for append operations
        if isinstance(node.func, ast.Attribute) and node.func.attr == 'append':
            if isinstance(node.func.value, ast.Name):  # the variable name of the list
                func_name = node.args[0].id
                full_name = self.get_full_name(func_name)
                if isinstance(node.args[0], ast.Name) and self.is_function(full_name):
                    # Append function to the list
                    if not self.graph.has_edge(from_function, full_name):
                        self.graph.add_edge(from_function, full_name, type='potential_call')
                        self.changed = True

        self.generic_visit(node)

    def visit_Lambda(self, node):
        # Handle lambda functions
        lambda_label = ""
        from_node = self.current_function if self.current_function else self.current_module
        lambda_label = f"{from_node}.lambda"
        try:
            lambda_source = astor.to_source(node).strip()
            lambda_label += f": {lambda_source}"
        except Exception as e:
            print(f"Error converting lambda to source: {e}")

        lambda_id = f"lambda_{id(node)}"

        if lambda_id not in self.lambda_set:
            self.lambda_set.add(lambda_id)
            self.graph.add_node(lambda_label, type='lambda', lineno=node.lineno)
            self.changed = True

            if not self.graph.has_edge(from_node, lambda_label):
                # Add an edge from the current function to this lambda to denote that the function uses this lambda
                self.graph.add_edge(from_node, lambda_label, type='uses-lambda')
                self.changed = True

        self.lambda_aliases[lambda_label] = lambda_label

        self.generic_visit(node)  # Visit the body of the lambda

    def visit_ClassDef(self, node):
        # Handles class definitions, treating methods with full names
        self.class_aliases[node.name] = node.name
        class_full_name = f"{self.current_module}.{node.name}" if self.current_module else node.name
        if node.name not in self.known_classes:
            self.known_classes.add(node.name)
            self.changed = True
        self.current_class = node.name  # Set the current class context
        self.graph.add_node(class_full_name, type='class', lineno=node.lineno)

        # Handle inheritance
        for base in node.bases:
            parent_class_name = None
            if isinstance(base, ast.Name):
                # Check if the base class name is an imported class or locally defined
                if base.id in self.imported_functions:
                    module, _ = self.imported_functions[base.id]
                    parent_class_name = f'{module}.{base.id}'
                else:
                    # Assume the base class is in the same module if not specifically imported
                    parent_class_name = f"{self.current_module}.{base.id}"
            elif isinstance(base, ast.Attribute):
                # inheriting from a class in a specific module
                parent_class_name = f"{base.value.id}.{base.attr}"
            # If a parent class name was resolved, add an edge for the inheritance relationship
            if parent_class_name:
                if not self.graph.has_edge(class_full_name, parent_class_name):
                    self.graph.add_edge(class_full_name, parent_class_name, type='inherits')
                    self.changed = True

        for item in node.body:
            self.visit(item)
        self.current_class = None

    def visit_Raise(self, node):
        from_node = self.current_function if self.current_function else self.current_module
        if node.exc:
            if isinstance(node.exc, ast.Call) and isinstance(node.exc.func, ast.Name):
                if self.graph.has_edge(f'{from_node}', f'{from_node}.{node.exc.func.id}'):
                    self.graph.remove_edge(f'{from_node}', f'{from_node}.{node.exc.func.id}')
                exception_class = self.class_aliases[node.exc.func.id]
                full_name = f'{self.current_module}.{exception_class}'
                if not self.graph.has_edge(from_node, full_name):
                    self.graph.add_edge(from_node, full_name, type='call')
                    # self.changed = True

            elif isinstance(node.exc, ast.Call):
                exception_name = node.exc.func.id
                full_name = self.get_full_name(exception_name)
                if not self.graph.has_edge(from_node, full_name):
                    self.graph.add_edge(from_node, full_name, type='call')
                    self.changed = True
        self.generic_visit(node)

    def visit_Return(self, node):
        self.generic_visit(node)

    def visit_If(self, node):
        self.generic_visit(node)

    def visit_For(self, node):
        self.generic_visit(node)

    def visit_While(self, node):
        self.generic_visit(node)

    def get_full_name(self, func_name):
        arg_full_name = ""
        if func_name in dir(builtins):
            return f"<builtin>.{func_name}"
        if func_name in self.imported_functions:
            module_name, _ = self.imported_functions[func_name]
            arg_full_name = f"{module_name}.{func_name}"
        else:
            if self.current_class:
                arg_full_name = f"{self.current_module}.{self.current_class}.{func_name}"
            else:
                arg_full_name = f"{self.current_module}.{func_name}"
        return arg_full_name

    def resolve_method(self, class_name, method_name, is_super=False):

        # Resolves the correct method using the graph's class hierarchy using BFS
        visited = set()
        queue = [f'{self.current_module}.{class_name}']
        while queue:
            current_class = queue.pop(0)

            if current_class in visited:
                continue
            visited.add(current_class)

            potential_method_node = f"{current_class}.{method_name}"
            if potential_method_node in self.graph.nodes and not is_super:
                return potential_method_node
            is_super = False

            parent_edges = [(edge[0], edge[1]) for edge in self.graph.edges(current_class) if
                            self.graph.edges[edge]['type'] == 'inherits']
            parents = [edge[1] for edge in parent_edges]
            queue.extend(parents)
        return None

    def is_function(self, name):
        return any(n == name and d.get('type') == 'function' for n, d in self.graph.nodes(data=True))

    def build_graph(self, code):
        # Builds the graph from the given code until a fixed point is reached
        tree = ast.parse(code)
        i = 0
        while self.changed:
            self.changed = False
            self.visit(tree)
            i += 1
            if i > MAX_ITERATION:
                break
        return self.graph

    def serialize_graph(self, graph):
        adjacency_dict = {}
        for node in graph.nodes():
            adjacency_dict[node] = [nbr for nbr in graph[node]]
        return json.dumps(adjacency_dict, indent=4)


def main():
    code = ""
    if len(sys.argv) > 1:
        file_path = sys.argv[1]
        with open(file_path, 'r') as file:
            code = file.read()
        builder = GraphBuilder()
        ir_graph = builder.build_graph(code)
        nx.draw(ir_graph, with_labels=True, node_color='lightblue', font_weight='bold', node_size=2000)
        plt.title('Intermediate Representation (IR) Graph')
        plt.show()
        # data = json_graph.node_link_data(ir_graph)
        # print(json.dumps(data))
    else:
        builder = GraphBuilder()
        ir_graph = builder.build_graph(code)
        nx.draw(ir_graph, with_labels=True, node_color='lightblue', font_weight='bold', node_size=2000)
        plt.title('Intermediate Representation (IR) Graph')
        plt.show()


if __name__ == '__main__':
    main()