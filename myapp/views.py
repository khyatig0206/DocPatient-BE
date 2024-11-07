from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from .serializers import DoctorSerializer, RegisterSerializer,CategorySerializer,LoginSerializer,BlogPostSerializer,UserDetailsSerializer, AppointmentDetailSerializer,BlogCreateSerializer
from rest_framework.decorators import api_view
from .models import Appointment, BlogPost, Category,Doctor,CustomUser
from google_auth_oauthlib.flow import Flow
from django.conf import settings
from django.shortcuts import redirect
import os
from google.oauth2.credentials import Credentials as OAuthCredentials
from googleapiclient.discovery import build

from django.db.models import Q
from django.contrib.auth import login, logout
from django.conf import settings
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request


class LoginView(APIView):
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data['user']
            login(request, user) 
            profile = user.profile  # Access the user's profile through the related name
            full_name = f"{user.first_name} {user.last_name}"
            profile_picture_url = profile.profile_picture.url
            user_id = user.id

            is_patient = user.is_patient
            flow = Flow.from_client_config(
                {
                    "web": {
                        "client_id": os.environ["GOOGLE_CLIENT_ID"],
                        "client_secret": os.environ["GOOGLE_CLIENT_SECRET"],
                        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                        "token_uri": "https://oauth2.googleapis.com/token",
                        "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
                        "redirect_uris": ["https://doc-patient-fe.vercel.app/auth/google/callback"]
                    }
                },
                scopes=['https://www.googleapis.com/auth/calendar'],
                redirect_uri='https://doc-patient-fe.vercel.app/auth/google/callback'
            )
            # Generate the authorization URL
            auth_url, _ = flow.authorization_url(prompt='consent')
            # You can add token generation logic here if you're using token-based authentication.
            return Response({"auth_url": auth_url,
                            "full_name": full_name,
                            "profile_picture": profile_picture_url,
                            "user_id": user_id,
                             "is_patient":is_patient }, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class GoogleCalendarCallbackView(APIView):
    def get(self, request):
        code = request.GET.get('code')
        flow = Flow.from_client_config(
                {
                    "web": {
                        "client_id": os.environ["GOOGLE_CLIENT_ID"],
                        "client_secret": os.environ["GOOGLE_CLIENT_SECRET"],
                        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                        "token_uri": "https://oauth2.googleapis.com/token",
                        "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
                        "redirect_uris": ["https://doc-patient-fe.vercel.app/auth/google/callback"]
                    }
                },
            scopes=['https://www.googleapis.com/auth/calendar'],
            redirect_uri='https://doc-patient-fe.vercel.app/auth/google/callback'  
        )
        flow.fetch_token(code=code)
        credentials = flow.credentials

        # Save the access token in the session or database for later API calls
        request.session['access_token'] = credentials.token

        return Response({"message": "Logged In Successfully", "access_token": credentials.token}, status=status.HTTP_200_OK)

class RegisterUserView(APIView):
    def post(self, request, *args, **kwargs):
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "Registration successful"}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class LogoutView(APIView):
    def post(self, request):
        if 'access_token' in request.session:
            del request.session['access_token']
        logout(request)  
        return Response({"message": "User logged out successfully"}, status=status.HTTP_200_OK)
  
@api_view(['GET'])
def get_all_categories(request):
    categories = Category.objects.all()
    serializer = CategorySerializer(categories, many=True)
    return Response(serializer.data)

@api_view(['GET'])
def get_all_blogposts(request):
    # Get pagination parameters
    offset = int(request.query_params.get('offset', 0))
    limit = int(request.query_params.get('limit', 4))
    total_count = BlogPost.objects.filter(draft=False).count()
    # Fetch the blog posts based on offset and limit
    blogposts = BlogPost.objects.filter(draft=False).order_by('-created_at')[offset:offset + limit]
    serializer = BlogPostSerializer(blogposts, many=True)

    return Response({
        'total_count': total_count,
        'blogposts': serializer.data
    })


@api_view(['GET'])
def get_filtered_blogposts(request):

    offset = int(request.query_params.get('offset', 0))
    limit = int(request.query_params.get('limit', 6))
    

    category_ids = request.query_params.getlist('categories[]') 
    if category_ids:
        blogposts = BlogPost.objects.filter(categories__id__in=category_ids, draft=False).distinct()
    else:
        blogposts = BlogPost.objects.filter(draft=False)
    total_count = blogposts.count()
    blogposts = blogposts.order_by('-created_at')[offset:offset + limit]
    serializer = BlogPostSerializer(blogposts, many=True)
    categories = Category.objects.all()
    categories_serializer = CategorySerializer(categories, many=True)

    return Response({
        'total_count': total_count,
        'blogposts': serializer.data,
        'categories': categories_serializer.data
    })

@api_view(['GET'])
def get_filtered_doctors(request):
    offset = int(request.query_params.get('offset', 0))
    limit = int(request.query_params.get('limit', 6))

    location_query = request.query_params.get('location', '')

    category_ids = request.query_params.getlist('categories[]')

    # Start with all doctors
    doctors = Doctor.objects.all()

    # Filter by categories if any are provided
    if category_ids:
        doctors = doctors.filter(categories__id__in=category_ids).distinct()

    # Apply location filtering
    if location_query:
        doctors = doctors.filter(
            Q(profile__city__icontains=location_query) |
            Q(profile__state__icontains=location_query) |
            Q(profile__address__icontains=location_query)
        )

    # Get total count before pagination
    total_count = doctors.count()

    # Apply ordering and pagination
    doctors = doctors[offset:offset + limit]

    # Serialize doctor data
    serializer = DoctorSerializer(doctors, many=True)

    # Get all categories and serialize
    categories = Category.objects.all()
    categories_serializer = CategorySerializer(categories, many=True)

    return Response({
        'total_count': total_count,
        'doctors': serializer.data,
        'categories': categories_serializer.data
    }, status=status.HTTP_200_OK)



class UserDetailsView(APIView):

    def get(self, request, *args, **kwargs):
        user_id = request.query_params.get('user_id')  # Get the user ID from query parameters

        try:
            user = CustomUser.objects.get(id=user_id)
        except CustomUser.DoesNotExist:
            return Response({"detail": "User not found."}, status=status.HTTP_404_NOT_FOUND)

        # Serialize user details based on their role (patient/doctor)
        serializer = UserDetailsSerializer(user)
        return Response(serializer.data, status=status.HTTP_200_OK)
    

class AppointmentBookingView(APIView):
    def post(self, request):
        access_token = request.data.get('access_token')
        if not access_token :
            return Response({"message": "No access token found. Please log in via Google."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            
            credentials = Credentials(token=access_token)
            patient_id=request.data.get('user_id')
            patient = CustomUser.objects.get(id=patient_id) 
            doctor_id = request.data.get('doctor_id')
            date = request.data.get('date')
            start_time = request.data.get('start_time')
            end_time = request.data.get('end_time')

            
            doctor = CustomUser.objects.get(id=doctor_id)
            appointment = Appointment.objects.create(
                patient=patient,
                doctor=doctor,
                date=date,
                start_time=start_time,
                end_time=end_time,
            )

            # Now create the Google Calendar event
            service = build('calendar', 'v3', credentials=credentials)
            event = {
                'summary': f"Appointment with Dr. {doctor.get_full_name()}",
                'location': doctor.profile.doctor_profile.establishment_name,
                'description': f"Patient: {patient.get_full_name()}",
                'start': {
                    'dateTime': f"{date}T{start_time}:00",
                    'timeZone': 'Asia/Kolkata',  # Use the correct time zone
                },
                'end': {
                    'dateTime': f"{date}T{end_time}:00",
                    'timeZone': 'Asia/Kolkata',  # Use the correct time zone
                },
                'attendees': [
                    {'email': patient.email},
                    {'email': doctor.email},
                ],
            }
            google_event = service.events().insert(calendarId='primary', body=event).execute()
            appointment.google_event_link = google_event.get('htmlLink')
            appointment.save()

            return Response({"message":"Appointment created successfully"}, status=status.HTTP_201_CREATED)
        
        except Exception as e:
            return Response({"message": f"Error: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)
        


class PatientAppointmentsView(APIView):
    def get(self, request):
        user_id = request.query_params.get('user_id')
        if not user_id:
            return Response({"error": "User ID not provided."}, status=400)

        try:
            # Fetch all appointments for the given patient (user)
            appointments = Appointment.objects.filter(patient_id=user_id).order_by('-date')
            serializer = AppointmentDetailSerializer(appointments, many=True)
            return Response(serializer.data, status=200)

        except Exception as e:
            return Response({"error": str(e)}, status=500)


class DocAppointmentsView(APIView):
    def get(self, request):
        user_id = request.query_params.get('user_id')
        if not user_id:
            return Response({"error": "User ID not provided."}, status=400)

        try:
            # Fetch all appointments for the given patient (user)
            appointments = Appointment.objects.filter(doctor_id=user_id).order_by('-date')
            serializer = AppointmentDetailSerializer(appointments, many=True)
            return Response(serializer.data, status=200)

        except Exception as e:
            return Response({"error": str(e)}, status=500)
        

class CreateBlogPostView(APIView):
    def post(self, request, *args, **kwargs):
        user_id = request.query_params.get('userId')
        if not user_id:
            return Response({"error": "userId query parameter is required"}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            user = CustomUser.objects.get(id=user_id)
            doctor = Doctor.objects.get(profile__user=user) 
        except (CustomUser.DoesNotExist, Doctor.DoesNotExist):
            return Response({"error": "Doctor with the provided userId does not exist"}, status=status.HTTP_404_NOT_FOUND)

        serializer = BlogCreateSerializer(data=request.data)
        if serializer.is_valid():
            # Pass the author directly into save
            serializer.save(author=doctor)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserBlogPostsView(APIView):
    def get(self, request, *args, **kwargs):
        user_id = request.query_params.get('userId')
        
        if not user_id:
            return Response({"error": "userId query parameter is required"}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            # Fetch the user and doctor profile
            user = CustomUser.objects.get(id=user_id)
            doctor = Doctor.objects.get(profile__user=user)
        except CustomUser.DoesNotExist:
            return Response({"error": "User with the provided userId does not exist"}, status=status.HTTP_404_NOT_FOUND)
        except Doctor.DoesNotExist:
            return Response({"error": "Doctor profile not found for the provided userId"}, status=status.HTTP_404_NOT_FOUND)
        
        # Get all blog posts authored by the doctor
        all_posts = BlogPost.objects.filter(author=doctor)
        
        # Separate drafts and published posts
        published_posts = all_posts.filter(draft=False)
        draft_posts = all_posts.filter(draft=True)

        # Serialize the data
        published_serializer = BlogPostSerializer(published_posts, many=True)
        draft_serializer = BlogPostSerializer(draft_posts, many=True)
        
        # Response with published and draft posts
        return Response({
            "published_posts": published_serializer.data,
            "draft_posts": draft_serializer.data
        }, status=status.HTTP_200_OK)