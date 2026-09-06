import datetime

from django.core.management.base import BaseCommand

from dbms_app.models import Student, Course, Enrollment, StudentHistory
from dbms_app import services


class Command(BaseCommand):
    help = 'Reset the demo collections and populate a complete working dataset.'

    def handle(self, *args, **options):
        self.section('SETUP - Clearing collections')
        for model in (Student, Course, Enrollment, StudentHistory):
            model.drop_collection()
        self.stdout.write(self.style.SUCCESS('Collections cleared.'))

        self.section('CRUD - CREATE')
        students_data = [
            ('Nishchaya Bhomi', 'nischayabhomi04@gmail.com', 22, 3.90),
            ('Ram Shrestha', 'ramshrestha@gmail.com', 23, 3.65),
            ('Aarav Sharma', 'aarav.sharma@example.com', 21, 3.80),
            ('Sita Karki', 'sita.karki@example.com', 22, 3.55),
        ]
        for name, email, age, gpa in students_data:
            s = Student(name=name, email=email, age=age, gpa=gpa).save()
            self.stdout.write(f'  Inserted student {s.student_id}: {name}')

        courses_data = [
            ('Database Systems', 3, 'Dr. Smith'),
            ('Data Structures', 4, 'Dr. Johnson'),
            ('Web Development', 3, 'Dr. Brown'),
            ('Machine Learning', 4, 'Dr. Davis'),
        ]
        for course_name, credits, instructor in courses_data:
            c = Course(course_name=course_name, credits=credits, instructor=instructor).save()
            self.stdout.write(f'  Inserted course {c.course_id}: {course_name}')

        self.section('CRUD - READ')
        for s in Student.objects.all().order_by('student_id'):
            self.stdout.write(f'  {s.student_id}: {s.name} ({s.email}) GPA={s.gpa}')
        self.stdout.write('  Students with GPA > 3.5:')
        for s in Student.objects(gpa__gt=3.5).order_by('-gpa'):
            self.stdout.write(f'    {s.name}: {s.gpa}')

        self.section('CRUD - UPDATE + TEMPORAL HISTORY')
        nischaya = Student.objects(name='Nishchaya Bhomi').first()
        before = nischaya.gpa
        nischaya.gpa = 3.95
        nischaya.save()
        self.stdout.write(f'  Updated Nishchaya Bhomi GPA {before} -> {nischaya.gpa}')
        self.stdout.write(f'  History records: {StudentHistory.objects(student_id=nischaya.student_id).count()}')

        self.section('ENROLLMENTS')
        students = list(Student.objects.all().order_by('student_id'))
        courses = list(Course.objects.all().order_by('course_id'))
        pairs = [
            (students[0], courses[0], 'A'),
            (students[0], courses[1], 'A-'),
            (students[1], courses[0], 'B+'),
            (students[2], courses[2], 'A'),
            (students[3], courses[3], 'B+'),
        ]
        for student, course, grade in pairs:
            Enrollment(
                student_id=student.student_id,
                course_id=course.course_id,
                enrollment_date=datetime.date(2026, 1, 15),
                grade=grade,
            ).save()
        self.stdout.write(f'  Created {Enrollment.objects.count()} enrollments.')

        self.section('STORED PROCEDURES')
        self.stdout.write('  get_student_details:')
        for row in services.get_student_details(students[0].student_id):
            self.stdout.write(f'    {row}')
        self.stdout.write(f'  calculate_average_gpa: {services.calculate_average_gpa()}')

        self.section('NATIVE MONGODB VIEW')
        services.create_student_summary_view()
        for row in services.query_student_summary_view():
            self.stdout.write(f'  {row}')

        self.section('INDEXING')
        for model in (Student, Course, Enrollment, StudentHistory):
            model.ensure_indexes()
            self.stdout.write(f'  {model.__name__}: {len(services.show_indexes(model._meta.get("collection")))} indexes')

        self.section('CRUD - DELETE + CASCADE')
        delete_target = Student.objects(name='Sita Karki').first()
        deleted_id = delete_target.student_id
        delete_target.delete()
        self.stdout.write(
            f'  Deleted student {deleted_id}; remaining students={Student.objects.count()}, '
            f'enrollments={Enrollment.objects.count()}'
        )

        self.section('DEMO COMPLETE')
        self.stdout.write(self.style.SUCCESS(
            'College DBMS demo is ready. Open / and test Students, Enrollments, Procedures, Views and Indexes.'
        ))

    def section(self, title):
        self.stdout.write('\n' + '=' * 64)
        self.stdout.write(f' {title}')
        self.stdout.write('=' * 64)
