class TaskManager:
    def __init__(self, assignments):
        self.assignments = assignments

    def display_tasks(self):
        for task, user in self.assignments.items():
            print(f"{task} is assigned to {user}")

class ExtendedTaskManager(TaskManager):
    def display_tasks(self):
        print("Extended Task List:")
        super().display_tasks()

def collect_tasks():
    return ["task1", "task2", "task3"]

def prioritize_tasks(tasks):
    return sorted(tasks)

def process_tasks():
    tasks = collect_tasks()
    return prioritize_tasks(tasks)

def assign_tasks(tasks):
    assignments = {task: f"User{index}" for index, task in enumerate(tasks, 1)}
    return assignments

def manage_tasks():
    assignments = assign_tasks(process_tasks())
    manager = ExtendedTaskManager(assignments)
    manager.display_tasks()

def main():
    manage_tasks()

main()
