class CourseRegistry:
    def __init__(self, course_list):
        self.course_list = course_list

    def display_courses(self):
        print("Available Courses:")
        for course in self.course_list:
            print(course)

def get_courses():
    return ["Mathematics", "Physics", "Chemistry"]

def register_course(course_list, new_course):
    if new_course not in course_list:
        course_list.append(new_course)
    return course_list

def setup_courses():
    available_courses = get_courses()
    updated_courses = register_course(available_courses, "Biology")
    registry = CourseRegistry(updated_courses)
    registry.display_courses()

def main():
    setup_courses()

main()
