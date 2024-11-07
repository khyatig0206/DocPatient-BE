from django.urls import path
from .views import RegisterUserView,get_all_categories,LoginView,GoogleCalendarCallbackView,LogoutView,get_all_blogposts,get_filtered_blogposts,get_filtered_doctors,UserDetailsView,AppointmentBookingView,PatientAppointmentsView,DocAppointmentsView,CreateBlogPostView,UserBlogPostsView

urlpatterns = [
    path('register/', RegisterUserView.as_view(), name='register'),
    path('categories/', get_all_categories, name='categories'),
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('auth/google/callback/', GoogleCalendarCallbackView.as_view(), name='google_calendar_callback'),
    path('blogposts/', get_all_blogposts, name='blogpost-list'),
    path('filtered_blogposts/', get_filtered_blogposts, name='filtered_blogposts'),
    path('doctors/', get_filtered_doctors, name='doctors-list'),
    path('user-details/', UserDetailsView.as_view(), name='user-details'),
    path('book-appointment/', AppointmentBookingView.as_view(), name='book-appointment'),
    path('appointments/', PatientAppointmentsView.as_view(), name='appointments'),
    path('doc-appointments/', DocAppointmentsView.as_view(), name='doc-appointments'),
    path('create-blog/', CreateBlogPostView.as_view(), name='create-blog'),
    path('user-blogs/', UserBlogPostsView.as_view(), name='user-blogs'),
]