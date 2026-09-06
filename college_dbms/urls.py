from django.contrib import admin
from django.urls import path, include

from dbms_app import web_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('dbms_app.urls')),

    # User-friendly HTML pages
    path('', web_views.home, name='page-home'),
    path('students/', web_views.students_page, name='page-students'),
    path('students/<int:student_id>/edit/', web_views.student_edit_page, name='page-student-edit'),
    path('students/<int:student_id>/delete/', web_views.student_delete_page, name='page-student-delete'),
    path('students/<int:student_id>/history/', web_views.student_history_page, name='page-student-history'),
    path('courses/', web_views.courses_page, name='page-courses'),
    path('enrollments/', web_views.enrollments_page, name='page-enrollments'),
    path('procedures/', web_views.procedures_page, name='page-procedures'),
    path('views/', web_views.views_page, name='page-views'),
    path('indexes/', web_views.indexes_page, name='page-indexes'),
]
