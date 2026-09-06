"""
"Triggers" for the college DBMS demo.

MongoDB has no native trigger language like MySQL, so the same
AFTER INSERT / AFTER UPDATE / AFTER DELETE behaviour from the original
project is reproduced with MongoEngine's signal framework:

    post_save (created=True)   -> AFTER INSERT trigger
    post_save (created=False)  -> AFTER UPDATE trigger
    pre_delete                 -> AFTER DELETE trigger

Each handler writes a version into StudentHistory, exactly like the
original student_after_insert / student_after_update /
student_after_delete triggers did.
"""

import datetime

from mongoengine import signals

from .models import Student, StudentHistory, Enrollment


def _close_open_history(student_id):
    """Set valid_to = now on whichever history row is still 'open'
    for this student (mirrors: UPDATE student_history SET valid_to = ...
    WHERE student_id = ... AND valid_to IS NULL)."""
    StudentHistory.objects(student_id=student_id, valid_to=None).update(
        set__valid_to=datetime.datetime.utcnow()
    )


def student_after_insert_or_update(sender, document, **kwargs):
    created = kwargs.get('created', False)

    if created:
        # ---- AFTER INSERT trigger ----
        StudentHistory(
            student_id=document.student_id,
            name=document.name,
            email=document.email,
            age=document.age,
            gpa=document.gpa,
            operation='INSERT',
        ).save()
    else:
        # ---- AFTER UPDATE trigger ----
        _close_open_history(document.student_id)
        StudentHistory(
            student_id=document.student_id,
            name=document.name,
            email=document.email,
            age=document.age,
            gpa=document.gpa,
            operation='UPDATE',
        ).save()


def student_after_delete(sender, document, **kwargs):
    # ---- AFTER DELETE trigger ----
    now = datetime.datetime.utcnow()
    _close_open_history(document.student_id)
    # A deleted version is itself closed: there is no current version after
    # the student has been removed.
    StudentHistory(
        student_id=document.student_id,
        name=document.name,
        email=document.email,
        age=document.age,
        gpa=document.gpa,
        valid_from=now,
        valid_to=now,
        operation='DELETE',
    ).save()

    # ON DELETE CASCADE equivalent: remove this student's enrollments too.
    Enrollment.objects(student_id=document.student_id).delete()


signals.post_save.connect(
    student_after_insert_or_update,
    sender=Student
)
signals.pre_delete.connect(
    student_after_delete,
    sender=Student
)
