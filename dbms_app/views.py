import json

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from mongoengine import ValidationError, NotUniqueError

from . import services
from .models import Student, Course, StudentHistory


def _student_to_dict(s):
    return {
        'student_id': s.student_id,
        'name': s.name,
        'email': s.email,
        'age': s.age,
        'gpa': float(s.gpa) if s.gpa is not None else None,
        'created_at': s.created_at.isoformat() if s.created_at else None,
    }


def _history_to_dict(h):
    return {
        'history_id': h.history_id,
        'student_id': h.student_id,
        'name': h.name,
        'email': h.email,
        'age': h.age,
        'gpa': float(h.gpa) if h.gpa is not None else None,
        'valid_from': h.valid_from.isoformat() if h.valid_from else None,
        'valid_to': h.valid_to.isoformat() if h.valid_to else None,
        'operation': h.operation,
    }


def _parse_json(request):
    try:
        return json.loads(request.body or '{}')
    except json.JSONDecodeError:
        raise ValueError('Request body must contain valid JSON.')


def _error(message, status=400):
    return JsonResponse({'error': message}, status=status)


# ---------------------------- CRUD ----------------------------------
@csrf_exempt
@require_http_methods(['GET', 'POST'])
def students_list_create(request):
    if request.method == 'GET':
        students = Student.objects.all().order_by('student_id')
        return JsonResponse([_student_to_dict(s) for s in students], safe=False)

    try:
        data = _parse_json(request)
        student = Student(
            name=data.get('name'),
            email=data.get('email'),
            age=data.get('age'),
            gpa=data.get('gpa'),
        )
        student.validate()
        student.save()
        return JsonResponse(_student_to_dict(student), status=201)
    except (ValueError, ValidationError, NotUniqueError) as exc:
        return _error(str(exc))


@csrf_exempt
@require_http_methods(['GET', 'PUT', 'DELETE'])
def student_detail(request, student_id):
    student = Student.objects(student_id=student_id).first()
    if not student:
        return _error('Student not found', 404)

    if request.method == 'GET':
        return JsonResponse(_student_to_dict(student))

    if request.method == 'PUT':
        try:
            data = _parse_json(request)
            for field in ('name', 'email', 'age', 'gpa'):
                if field in data:
                    setattr(student, field, data[field])
            student.validate()
            student.save()
            return JsonResponse(_student_to_dict(student))
        except (ValueError, ValidationError, NotUniqueError) as exc:
            return _error(str(exc))

    deleted_id = student.student_id
    student.delete()
    return JsonResponse({'deleted': deleted_id})


@require_http_methods(['GET'])
def courses_list(request):
    courses = Course.objects.all().order_by('course_id')
    return JsonResponse([
        {
            'course_id': c.course_id,
            'course_name': c.course_name,
            'credits': c.credits,
            'instructor': c.instructor,
        } for c in courses
    ], safe=False)


# ------------------------ TEMPORAL DATABASE --------------------------
@require_http_methods(['GET'])
def student_history_view(request, student_id):
    history = StudentHistory.objects(student_id=student_id).order_by('-valid_from')
    return JsonResponse([_history_to_dict(h) for h in history], safe=False)


# ------------------------- STORED PROCEDURES --------------------------
@require_http_methods(['GET'])
def procedure_student_details(request, student_id):
    return JsonResponse(services.get_student_details(student_id), safe=False)


@require_http_methods(['GET'])
def procedure_average_gpa(request):
    return JsonResponse(services.calculate_average_gpa())


# ------------------------------ VIEWS ----------------------------------
@require_http_methods(['GET'])
def view_student_summary(request):
    return JsonResponse(services.query_student_summary_view(), safe=False)


# ----------------------------- INDEXES ----------------------------------
@require_http_methods(['GET'])
def indexes_view(request, collection_name):
    try:
        idxs = services.show_indexes(collection_name)
        return JsonResponse(
            [{'name': i.get('name'), 'key': dict(i.get('key', {}))} for i in idxs],
            safe=False,
        )
    except ValueError as exc:
        return _error(str(exc), 400)
