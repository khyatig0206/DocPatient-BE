from django.urls import path
from .views import RegisterUserView,get_all_categories,LoginView,GoogleCalendarCallbackView

urlpatterns = [
    path('register/', RegisterUserView.as_view(), name='register'),
    path('categories/', get_all_categories, name='categories'),
    path('login/', LoginView.as_view(), name='login'),
    path('auth/google/callback/', GoogleCalendarCallbackView.as_view(), name='google_calendar_callback'),

]