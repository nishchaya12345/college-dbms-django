"""Database services: aggregation-based procedures, native MongoDB view and indexes."""

from decimal import Decimal
from pymongo import MongoClient
from django.conf import settings


def get_db():
    client = MongoClient(settings.MONGO_URI, serverSelectionTimeoutMS=5000)
    return client[settings.MONGO_DB_NAME]


def _json_value(value):
    """Convert BSON numeric/date values into values Django JsonResponse can encode."""
    if value is None:
        return None
    # Decimal128 exposes to_decimal(); Decimal is handled as well.
    if hasattr(value, 'to_decimal'):
        return float(value.to_decimal())
    if isinstance(value, Decimal):
        return float(value)
    return value


def _json_row(row):
    return {key: _json_value(value) for key, value in row.items()}


# --------------------------------------------------------------------
# Stored procedure equivalent: get_student_details
# --------------------------------------------------------------------
def get_student_details(student_id):
    db = get_db()
    pipeline = [
        {'$match': {'student_id': int(student_id)}},
        {'$lookup': {
            'from': 'enrollments',
            'localField': 'student_id',
            'foreignField': 'student_id',
            'as': 'enrollments',
        }},
        {'$unwind': {
            'path': '$enrollments',
            'preserveNullAndEmptyArrays': True,
        }},
        {'$lookup': {
            'from': 'courses',
            'localField': 'enrollments.course_id',
            'foreignField': 'course_id',
            'as': 'course_info',
        }},
        {'$unwind': {
            'path': '$course_info',
            'preserveNullAndEmptyArrays': True,
        }},
        {'$project': {
            '_id': 0,
            'student_id': 1,
            'name': 1,
            'email': 1,
            'gpa': 1,
            'course_name': '$course_info.course_name',
            'grade': '$enrollments.grade',
        }},
    ]
    return [_json_row(row) for row in db.students.aggregate(pipeline)]


# --------------------------------------------------------------------
# Stored procedure equivalent: calculate_average_gpa
# --------------------------------------------------------------------
def calculate_average_gpa():
    db = get_db()
    pipeline = [
        {'$match': {'gpa': {'$ne': None}}},
        {'$group': {
            '_id': None,
            'average_gpa': {'$avg': '$gpa'},
            'min_gpa': {'$min': '$gpa'},
            'max_gpa': {'$max': '$gpa'},
            'total_students': {'$sum': 1},
        }},
        {'$project': {'_id': 0}},
    ]
    result = list(db.students.aggregate(pipeline))
    return _json_row(result[0]) if result else {}


# --------------------------------------------------------------------
# Native MongoDB view: student_summary
# --------------------------------------------------------------------
def create_student_summary_view():
    """Create/recreate the native read-only MongoDB view safely."""
    db = get_db()
    existing = db.list_collection_names()
    if 'student_summary' in existing:
        db.drop_collection('student_summary')

    db.command({
        'create': 'student_summary',
        'viewOn': 'students',
        'pipeline': [
            {'$lookup': {
                'from': 'enrollments',
                'localField': 'student_id',
                'foreignField': 'student_id',
                'as': 'enrollments',
            }},
            {'$project': {
                '_id': 0,
                'student_id': 1,
                'name': 1,
                'email': 1,
                'gpa': 1,
                'total_courses': {'$size': '$enrollments'},
            }},
        ],
    })


def ensure_student_summary_view():
    """Create the native view only when it does not already exist."""
    db = get_db()
    if 'student_summary' not in db.list_collection_names():
        create_student_summary_view()


def query_student_summary_view():
    ensure_student_summary_view()
    db = get_db()
    return [_json_row(row) for row in db.student_summary.find({}, {'_id': 0})]


# --------------------------------------------------------------------
# Index helpers
# --------------------------------------------------------------------
def show_indexes(collection_name):
    allowed = {'students', 'courses', 'enrollments', 'student_history'}
    if collection_name not in allowed:
        raise ValueError(f'Unsupported collection: {collection_name}')
    return list(get_db()[collection_name].list_indexes())
