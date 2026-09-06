from django.urls import path

from . import views

urlpatterns = [
    # CRUD
    path('students/', views.students_list_create, name='students-list-create'),
    path('students/<int:student_id>/', views.student_detail, name='student-detail'),
    path('courses/', views.courses_list, name='courses-list'),

    # Temporal database
    path('students/<int:student_id>/history/', views.student_history_view, name='student-history'),

    # Stored procedures
    path('procedures/student-details/<int:student_id>/', views.procedure_student_details,
         name='procedure-student-details'),
    path('procedures/average-gpa/', views.procedure_average_gpa, name='procedure-average-gpa'),

    # Views
    path('views/student-summary/', views.view_student_summary, name='view-student-summary'),

    # Indexing
    path('indexes/<str:collection_name>/', views.indexes_view, name='indexes-view'),
]
