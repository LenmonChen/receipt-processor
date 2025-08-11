class Student:
    student_id = 1
    def hello(self, name):
        print("Hello " + name)

# print(Student.student_id)
# print(id(Student.student_id))
# a = Student()
# print(id(a.student_id))
# a.student_id = 123
# print(a.student_id)
# print(id(a.student_id))
# print(getattr(Student, 'student_id'))
#
#
# print(Student.__dict__)


a = Student()
a.hello('Jack')