from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from .serializers import RegisterSerializer,CategorySerializer,LoginSerializer
from rest_framework.decorators import api_view
from .models import Category
from google_auth_oauthlib.flow import Flow
from django.conf import settings
from django.shortcuts import redirect
import os
from django.conf import settings



class LoginView(APIView):
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            flow = Flow.from_client_config(
                {
                    "web": {
                        "client_id": os.environ["GOOGLE_CLIENT_ID"],
                        "client_secret": os.environ["GOOGLE_CLIENT_SECRET"],
                        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                        "token_uri": "https://oauth2.googleapis.com/token",
                        "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
                        "redirect_uris": ["https://docpatient-be.onrender.com/auth/google/callback"]
                    }
                },
                scopes=['https://www.googleapis.com/auth/calendar'],
                redirect_uri='https://docpatient-be.onrender.com/auth/google/callback'
            )
            # Generate the authorization URL
            auth_url, _ = flow.authorization_url(prompt='consent')
            # You can add token generation logic here if you're using token-based authentication.
            return Response({"auth_url": auth_url}, status=status.HTTP_200_OK)
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
                        "redirect_uris": ["https://docpatient-be.onrender.com/auth/google/callback"]
                    }
                },
            scopes=['https://www.googleapis.com/auth/calendar'],
            redirect_uri='https://docpatient-be.onrender.com/auth/google/callback'  
        )
        flow.fetch_token(code=code)
        credentials = flow.credentials

        # Save the access token in the session or database for later API calls
        request.session['access_token'] = credentials.token

        return Response({"message": "Logged In Successfully"}, status=status.HTTP_200_OK)

class RegisterUserView(APIView):
    def post(self, request, *args, **kwargs):
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "Registration successful"}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


  
@api_view(['GET'])
def get_all_categories(request):
    categories = Category.objects.all()
    serializer = CategorySerializer(categories, many=True)
    return Response(serializer.data)


