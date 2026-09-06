"""MongoEngine documents for the College DBMS demonstration project."""

import datetime
import mongoengine as me


class Student(me.Document):
    # Keep the academic ID as a normal MongoDB field.  Do NOT make it the
    # MongoDB _id field: aggregation pipelines and the other collections
    # intentionally join on student_id.
    student_id = me.SequenceField(unique=True)
    name = me.StringField(required=True, max_length=100)
    email = me.EmailField(required=True, unique=True)
    age = me.IntField(min_value=1)
    gpa = me.DecimalField(precision=2, min_value=0, max_value=4)
    created_at = me.DateTimeField(default=datetime.datetime.utcnow)

    meta = {
        'collection': 'students',
        'indexes': ['email', 'gpa'],
    }

    def __str__(self):
        return f'{self.student_id}: {self.name}'


class Course(me.Document):
    course_id = me.SequenceField(unique=True)
    course_name = me.StringField(required=True, max_length=100)
    credits = me.IntField(min_value=1, max_value=6)
    instructor = me.StringField(required=True, max_length=100)

    meta = {
        'collection': 'courses',
        'indexes': ['course_name'],
    }

    def __str__(self):
        return f'{self.course_id}: {self.course_name}'


class Enrollment(me.Document):
    enrollment_id = me.SequenceField(unique=True)
    student_id = me.IntField(required=True)
    course_id = me.IntField(required=True)
    enrollment_date = me.DateField(default=datetime.date.today)
    grade = me.StringField(max_length=2, null=True)

    meta = {
        'collection': 'enrollments',
        'indexes': [
            'student_id',
            'course_id',
            ('student_id', 'course_id'),
        ],
    }


class StudentHistory(me.Document):
    """Temporal/audit versions written by MongoEngine signals."""

    history_id = me.SequenceField(unique=True)
    student_id = me.IntField(required=True)
    name = me.StringField()
    email = me.StringField()
    age = me.IntField()
    gpa = me.DecimalField(precision=2)
    valid_from = me.DateTimeField(default=datetime.datetime.utcnow)
    valid_to = me.DateTimeField(null=True)
    operation = me.StringField(max_length=10, choices=('INSERT', 'UPDATE', 'DELETE'))

    meta = {
        'collection': 'student_history',
        'indexes': [
            ('student_id', 'valid_from', 'valid_to'),
        ],
    }
