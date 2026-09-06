"""Server-rendered HTML pages for the College DBMS front-end."""

import datetime
from decimal import Decimal, InvalidOperation

from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_http_methods
from mongoengine import ValidationError, NotUniqueError

from . import services
from .models import Student, Course, Enrollment, StudentHistory


def _decimal(value):
    if value in (None, ''):
        return None
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError):
        return None


def _int(value):
    if value in (None, ''):
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def home(request):
    context = {
        'total_students': Student.objects.count(),
        'total_courses': Course.objects.count(),
        'total_enrollments': Enrollment.objects.count(),
        'avg_gpa': None,
    }
    stats = services.calculate_average_gpa()
    if stats.get('average_gpa') is not None:
        context['avg_gpa'] = round(float(stats['average_gpa']), 2)
    return render(request, 'dbms_app/home.html', context)


@require_http_methods(['GET', 'POST'])
def students_page(request):
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        email = request.POST.get('email', '').strip()
        age = _int(request.POST.get('age'))
        gpa = _decimal(request.POST.get('gpa'))

        try:
            student = Student(name=name, email=email, age=age, gpa=gpa)
            student.validate()
            student.save()
            messages.success(request, f'Added student "{student.name}" (ID {student.student_id}).')
            return redirect('page-students')
        except (ValidationError, NotUniqueError) as exc:
            messages.error(request, f'Could not add student: {exc}')

    students = Student.objects.all().order_by('student_id')
    return render(request, 'dbms_app/students.html', {'students': students})


@require_http_methods(['GET', 'POST'])
def student_edit_page(request, student_id):
    student = get_object_or_404(Student, student_id=student_id)

    if request.method == 'POST':
        student.name = request.POST.get('name', '').strip()
        student.email = request.POST.get('email', '').strip()
        student.age = _int(request.POST.get('age'))
        student.gpa = _decimal(request.POST.get('gpa'))
        try:
            student.validate()
            student.save()
            messages.success(request, f'Updated "{student.name}". History recorded automatically.')
            return redirect('page-students')
        except (ValidationError, NotUniqueError) as exc:
            messages.error(request, f'Could not update student: {exc}')

    return render(request, 'dbms_app/student_edit.html', {'student': student})


@require_http_methods(['POST'])
def student_delete_page(request, student_id):
    student = get_object_or_404(Student, student_id=student_id)
    name = student.name
    student.delete()
    messages.success(request, f'Deleted "{name}". Their enrollments were cascaded automatically.')
    return redirect('page-students')


@require_http_methods(['GET'])
def student_history_page(request, student_id):
    student = get_object_or_404(Student, student_id=student_id)
    history = StudentHistory.objects(student_id=student_id).order_by('-valid_from')
    return render(request, 'dbms_app/student_history.html', {
        'student': student,
        'history': history,
    })


@require_http_methods(['GET', 'POST'])
def courses_page(request):
    if request.method == 'POST':
        course_name = request.POST.get('course_name', '').strip()
        instructor = request.POST.get('instructor', '').strip()
        credits = _int(request.POST.get('credits'))
        try:
            course = Course(course_name=course_name, credits=credits, instructor=instructor)
            course.validate()
            course.save()
            messages.success(request, f'Added course "{course.course_name}" (ID {course.course_id}).')
            return redirect('page-courses')
        except (ValidationError, NotUniqueError) as exc:
            messages.error(request, f'Could not add course: {exc}')

    courses = Course.objects.all().order_by('course_id')
    return render(request, 'dbms_app/courses.html', {'courses': courses})


@require_http_methods(['GET', 'POST'])
def enrollments_page(request):
    students = Student.objects.all().order_by('name')
    courses = Course.objects.all().order_by('course_name')

    if request.method == 'POST':
        student_id = _int(request.POST.get('student_id'))
        course_id = _int(request.POST.get('course_id'))
        date_str = request.POST.get('enrollment_date')
        grade = request.POST.get('grade', '').strip().upper() or None

        try:
            if not Student.objects(student_id=student_id).first():
                raise ValueError('Selected student does not exist.')
            if not Course.objects(course_id=course_id).first():
                raise ValueError('Selected course does not exist.')
            if Enrollment.objects(student_id=student_id, course_id=course_id).first():
                raise ValueError('This student is already enrolled in that course.')

            enrollment_date = (
                datetime.datetime.strptime(date_str, '%Y-%m-%d').date()
                if date_str else datetime.date.today()
            )
            enrollment = Enrollment(
                student_id=student_id,
                course_id=course_id,
                enrollment_date=enrollment_date,
                grade=grade,
            )
            enrollment.validate()
            enrollment.save()
            messages.success(request, 'Enrollment created successfully.')
            return redirect('page-enrollments')
        except (ValueError, ValidationError, NotUniqueError) as exc:
            messages.error(request, f'Could not create enrollment: {exc}')

    student_lookup = {s.student_id: s.name for s in students}
    course_lookup = {c.course_id: c.course_name for c in courses}
    enrollments = []
    for e in Enrollment.objects.all().order_by('-enrollment_id'):
        enrollments.append({
            'enrollment_id': e.enrollment_id,
            'student_name': student_lookup.get(e.student_id, f'#{e.student_id}'),
            'course_name': course_lookup.get(e.course_id, f'#{e.course_id}'),
            'enrollment_date': e.enrollment_date,
            'grade': e.grade,
        })

    return render(request, 'dbms_app/enrollments.html', {
        'students': students,
        'courses': courses,
        'enrollments': enrollments,
    })


@require_http_methods(['GET'])
def procedures_page(request):
    gpa_stats = services.calculate_average_gpa()
    queried_id = request.GET.get('student_id')
    student_details = None
    invalid_id = False

    if queried_id:
        try:
            student_details = services.get_student_details(int(queried_id))
        except ValueError:
            invalid_id = True

    return render(request, 'dbms_app/procedures.html', {
        'gpa_stats': gpa_stats,
        'queried_id': queried_id,
        'student_details': student_details,
        'invalid_id': invalid_id,
    })


@require_http_methods(['GET', 'POST'])
def views_page(request):
    if request.method == 'POST':
        services.create_student_summary_view()
        messages.success(request, 'student_summary native MongoDB view rebuilt successfully.')
        return redirect('page-views')

    summary = services.query_student_summary_view()
    return render(request, 'dbms_app/views_page.html', {'summary': summary})


@require_http_methods(['GET'])
def indexes_page(request):
    collections = ('students', 'courses', 'enrollments', 'student_history')
    indexes = {
        collection: [
            {'name': i.get('name'), 'key': dict(i.get('key', {}))}
            for i in services.show_indexes(collection)
        ]
        for collection in collections
    }
    return render(request, 'dbms_app/indexes_page.html', {'indexes': indexes})
