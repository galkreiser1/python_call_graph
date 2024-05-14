import ast
import networkx as nx
import astor
import json
from networkx.readwrite import json_graph
import sys

class IRGraphBuilder(ast.NodeVisitor):
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
        self.known_classes = set()  # Set of known classes
        self.instance_map = {}  # Map from variable names to their classes

    def visit_Import(self, node):
        for alias in node.names:
            self.graph.add_node(alias.name, type='module')
            self.module_functions[alias.name] = []

    def visit_ImportFrom(self, node):
        module = node.module
        for alias in node.names:
            alias_name = alias.asname if alias.asname else alias.name
            full_name = f'{node.module}.{alias_name}'
            self.graph.add_node(full_name, type='function')
            self.module_functions.setdefault(module, []).append(alias.name)
            self.imported_functions[alias_name] = (node.module, alias_name)
            # if self.current_function:
            #     # Edge from current function to imported function
            #     self.graph.add_edge(self.current_function, full_name, type='calls')

    def visit_FunctionDef(self, node):
        """Visits a function definition, creating a graph node and setting the current function context."""

        func_name = self.get_full_name(node.name)
        prev_function = self.current_function
        self.current_function = func_name
        if self.current_module:
            if func_name not in self.graph:
                self.graph.add_node(func_name, type='function')
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
        """Handles variable assignments within functions."""
        from_node = self.current_function if self.current_function else self.current_module
        if isinstance(node.value, ast.Name) and self.is_function(self.get_full_name(node.value.id)):
            for target in node.targets:
                if isinstance(target, ast.Subscript) and isinstance(target.value, ast.Name):
                    func_name = self.get_full_name(node.value.id)
                    if not self.graph.has_edge(from_node,func_name):
                        self.graph.add_edge(from_node, func_name, type='potential_call')
                        self.changed = True
        if isinstance(node.value, ast.Call) and isinstance(node.value.func, ast.Name):
            func_name = node.value.func.id
            if func_name in self.known_classes:
                # Assume the assignment is creating an instance of a class
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        self.instance_map[target.id] = func_name  # Map variable to class name
        if isinstance(node.value, ast.Lambda):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    lambda_label = f"{from_node}.lambda"
                    # Optionally, try to convert the lambda expression to source code for labeling
                    try:
                        lambda_source = astor.to_source(node).split('=')[1].strip()
                        print(f'lambda source: {lambda_source}')
                        lambda_label += f": {lambda_source}"
                    except Exception as e:
                        print(f"Error converting lambda to source: {e}")
                    self.graph.add_edge(self.get_full_name(target.id), lambda_label, type='defines')

        if isinstance(node.value, ast.List):
            for elt in node.value.elts:
                if isinstance(elt, ast.Name):  # This assumes the elements are directly function names
                    to_node = self.get_full_name(elt.id)
                    if self.is_function(to_node):
                        # Only create edges if the function exists in the graph
                        if not self.graph.has_edge(from_node,to_node):
                            self.graph.add_edge(from_node, to_node, type='potential_call')
                            self.changed = True
        self.generic_visit(node)

    def visit_Call(self, node):
        """Handles function calls, creating graph edges from the current function to the called function."""

        from_function = self.current_function if self.current_function else self.current_module
        if isinstance(node.func, ast.Attribute) and \
                isinstance(node.func.value, ast.Call) and \
                isinstance(node.func.value.func, ast.Name) and \
                node.func.value.func.id == "super":

            method_or_function_name = node.func.attr
            resolved_method = self.resolve_method(self.current_class, method_or_function_name, True)
            if resolved_method and not self.graph.has_edge(self.current_function, resolved_method):
                self.graph.add_edge(f"{self.current_function}", resolved_method, type='calls')
                self.changed = True


        if isinstance(node.func, ast.Name):
            func_name = node.func.id
            if func_name in self.imported_functions:
                module_name, _ = self.imported_functions[func_name]
                full_name = f"{module_name}.{func_name}"
                if not self.graph.has_edge(from_function, full_name):
                    self.graph.add_edge(from_function, full_name, type='calls')
                    self.change = True
            elif func_name != "range" and func_name != "super":
                full_name = self.get_full_name(func_name)
                if self.current_function:
                    if not self.graph.has_edge(self.current_function, full_name):
                        self.graph.add_edge(self.current_function, full_name, type='calls')
                        self.change = True
                elif not self.current_class:
                    if not self.graph.has_edge(self.current_module, full_name):
                        self.graph.add_edge(self.current_module, full_name, type='calls')
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
                    # This assumes that the function definition exists for these function names,
                    # marking them as potential dynamic calls from within the callee function.
                    if not self.graph.has_edge(full_name, arg_full_name):
                        self.graph.add_edge(full_name, arg_full_name, type='dynamic-call')
                        self.change = True
        if isinstance(node.func, ast.Subscript) and isinstance(node.func.value, ast.Name):
            # Example: func_list[index]()
            list_name = node.func.value.id
            if list_name in self.function_lists:
                # Add edges for all functions in the list as potential calls
                for func_name in self.function_lists[list_name]:
                    full_name = self.get_full_name(func_name)
                    if not self.graph.has_edge(from_function, full_name):
                        self.graph.add_edge(from_function, full_name, type='dynamic-call')
                        self.changed = True

        if isinstance(node.func, ast.Attribute) and isinstance(node.func.value, ast.Name):
            instance_or_module_name = node.func.value.id
            method_or_function_name = node.func.attr

            if instance_or_module_name == 'self' and self.current_class:
                # Ensure that self-references within a class do not create separate nodes
                resolved_method = self.resolve_method(self.current_class, method_or_function_name)
                if resolved_method and not self.graph.has_edge(from_function, resolved_method):
                    self.graph.add_edge(from_function, resolved_method, type='calls')
                    self.changed = True

            # Check if the name refers to a known class instance
            elif instance_or_module_name in self.instance_map:
                class_name = self.instance_map[instance_or_module_name]
                if class_name:
                    resolved_method = self.resolve_method(class_name, method_or_function_name)
                    if resolved_method and not self.graph.has_edge(from_function, resolved_method):
                        self.graph.add_edge(from_function, resolved_method, type='calls')
                        self.changed = True
                # qualified_name = f"{self.current_module}.{class_name}.{method_or_function_name}"
                # if not self.graph.has_edge(self.current_function, qualified_name):
                #     self.graph.add_edge(self.current_function, qualified_name, type='calls')
                #     self.changed = True
            else:
                qualified_name = f"{instance_or_module_name}.{method_or_function_name}"
                if not self.graph.has_edge(from_function, qualified_name):
                    self.graph.add_edge(from_function, qualified_name, type='calls')
                    self.changed = True

            # Check for append operations
        if isinstance(node.func, ast.Attribute) and node.func.attr == 'append':
            if isinstance(node.func.value, ast.Name):  # the variable name of the list
                func_name = node.args[0].id
                full_name = self.get_full_name(func_name)
                if isinstance(node.args[0], ast.Name) and self.is_function(full_name):
                    # Append function to the list
                    if not self.graph.has_edge(from_function,full_name):
                        self.graph.add_edge(from_function, full_name, type='potential_call')
                        self.changed = True

        self.generic_visit(node)

    def visit_Lambda(self, node):
        """Handle lambda functions by creating a more informative node."""
        lambda_label = ""
        from_node = self.current_function if self.current_function else self.current_module
        lambda_label = f"{from_node}.lambda"
        # Optionally, try to convert the lambda expression to source code for labeling
        try:
            lambda_source = astor.to_source(node).strip()
            lambda_label += f": {lambda_source}"
        except Exception as e:
            print(f"Error converting lambda to source: {e}")


        lambda_id = f"lambda_{id(node)}"


        if lambda_id not in self.lambda_set:
            self.lambda_set.add(lambda_id)
            self.graph.add_node(lambda_label, type='lambda')
            self.changed = True

            if not self.graph.has_edge(from_node, lambda_label):
                # Add an edge from the current function to this lambda to denote that the function uses this lambda
                self.graph.add_edge(from_node, lambda_label, type='uses-lambda')
                self.changed = True

        self.generic_visit(node)  # Visit the body of the lambda

    def visit_ClassDef(self, node):
        """Handles class definitions, treating methods with full names."""
        class_full_name = f"{self.current_module}.{node.name}" if self.current_module else node.name
        if node.name not in self.known_classes:
            self.known_classes.add(node.name)
            self.changed = True
        self.current_class = node.name  # Set the current class context
        self.graph.add_node(class_full_name, type='class')

        # Handle inheritance: check each base class specified in the class definition
        for base in node.bases:
            parent_class_name = None
            if isinstance(base, ast.Name):  # Simple case: inheriting from a class in the same module or imported
                # Check if the base class name is an imported class or locally defined
                if base.id in self.imported_functions:
                    module,_ = self.imported_functions[base.id]
                    parent_class_name = f'{module}.{base.id}'
                else:
                    # Assume the base class is in the same module if not specifically imported
                    parent_class_name = f"{self.current_module}.{base.id}"
            elif isinstance(base, ast.Attribute):  # More complex case: inheriting from a class in a specific module
                # Directly use the attribute notation to construct the full class name
                parent_class_name = f"{base.value.id}.{base.attr}"
        # If a parent class name was resolved, add an edge for the inheritance relationship
            if parent_class_name:
                if not self.graph.has_edge(class_full_name, parent_class_name):
                    self.graph.add_edge(class_full_name, parent_class_name, type='inherits')
                    self.changed = True

        for item in node.body:
            self.visit(item)  # Visit methods within the class
        self.current_class = None



    def visit_Return(self, node):
        """Handles return statements, potentially creating edges back to the function from returned variables."""
        if isinstance(node.value, ast.Name):
            self.graph.add_edge(node.value.id, self.current_function, type='returns')
        self.generic_visit(node)

    def visit_If(self, node):
        """Visits if statements, over-approximating by considering all branches."""
        self.generic_visit(node)

    def visit_For(self, node):
        """Visits for loops, over-approximating by considering the loop body under all circumstances."""
        self.generic_visit(node)

    def visit_While(self, node):
        """Visits while loops, over-approximating by considering the loop body regardless of the loop condition."""
        self.generic_visit(node)

    def get_full_name(self, func_name):
        arg_full_name = ""
        if func_name in self.imported_functions:
            module_name, _ = self.imported_functions[func_name]
            arg_full_name = f"{module_name}.{func_name}"
        else:
            if self.current_class:
                arg_full_name = f"{self.current_module}.{self.current_class}.{func_name}"
            else:
                arg_full_name = f"{self.current_module}.{func_name}"
        return arg_full_name

    def resolve_method(self, class_name, method_name, is_super = False):
        """
        Resolves the correct method using the graph's class hierarchy. It follows the order
        of inheritance as specified in the class definition.
        """
        visited = set()
        queue = [f'{self.current_module}.{class_name}']  # Start with the current class
        while queue:
            current_class = queue.pop(0)

            if current_class in visited:
                continue
            visited.add(current_class)

            # Check if current class defines this method
            potential_method_node = f"{current_class}.{method_name}"
            if potential_method_node in self.graph.nodes and not is_super:
                return potential_method_node
            is_super = False

            # Enqueue parent classes according to their declared order
            # Retrieve edges where current_class is the child
            parent_edges = [(edge[0], edge[1]) for edge in self.graph.edges(current_class) if
                            self.graph.edges[edge]['type'] == 'inherits']
            # Important: Reverse to maintain the left-to-right order specified in class definition
            parents = [edge[1] for edge in parent_edges]
            queue.extend(parents)
        return None

    def is_function(self, name):
        """Check if a name corresponds to a function in the graph."""
        return any(n == name and d.get('type') == 'function' for n, d in self.graph.nodes(data=True))

    def build_graph(self, code):
        """Parses the provided code into an AST and builds the graph by visiting the AST."""
        tree = ast.parse(code)
        i=0
        while self.changed:
            self.changed = False
            self.visit(tree)
            i+=1
            if i>1000:
                break
        return self.graph
    

def main():
    code = ""
    if len(sys.argv) > 1:
        file_path = sys.argv[1]
        with open(file_path, 'r') as file:
            code = file.read()
        builder = IRGraphBuilder()
        ir_graph = builder.build_graph(code)
        data = json_graph.node_link_data(ir_graph)
        print(json.dumps(data))
    else:
        return 
    


if __name__ == '__main__':
    main()