from rest_framework import serializers
from .models import CustomUser, Doctor, Category, Profile , BlogPost
from django.contrib.auth.hashers import make_password
from django.contrib.auth import authenticate





class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name']

class CustomUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ['id', 'first_name', 'last_name', 'username', 'email', 'password', 'is_patient', 'is_doctor']
        extra_kwargs = {
            'password': {'write_only': True}  # Ensures the password is write-only and not exposed in responses
        }


class ProfileSerializer(serializers.ModelSerializer):
    user = CustomUserSerializer()

    class Meta:
        model = Profile
        fields = ['user', 'profile_picture', 'address', 'city', 'state', 'pincode']



class DoctorSerializer(serializers.ModelSerializer):
    user = ProfileSerializer()
    categories = CategorySerializer(many=True)  # Serialize multiple categories

    class Meta:
        model = Doctor
        fields = ['user', 'categories', 'establishment_name' , 'license_number']


# Serializer for BlogPost
class BlogPostSerializer(serializers.ModelSerializer):
    author = DoctorSerializer(read_only=True)  # Author details (read-only, as it's set automatically)
    category = CategorySerializer()  # Nested category details

    class Meta:
        model = BlogPost
        fields = ['id', 'author', 'title', 'image', 'category', 'summary', 'content', 'draft', 'created_at']
    
class RegisterSerializer(serializers.ModelSerializer):
    profile_picture = serializers.ImageField(required=False, default='/profile-default.png')
    address = serializers.CharField(max_length=255, required=True)
    city = serializers.CharField(max_length=100, required=True)
    state = serializers.CharField(max_length=100, required=True)
    pincode = serializers.IntegerField(required=True)
    select_role = serializers.ChoiceField(choices=[('patient', 'Patient'), ('doctor', 'Doctor')], required=True)
    
    # Doctor specific fields
    categories = serializers.PrimaryKeyRelatedField(queryset=Category.objects.all(), many=True, required=False)
    establishment_name = serializers.CharField(max_length=255, required=False)
    license_number = serializers.CharField(max_length=100, required=False)

    email = serializers.EmailField(required=True)
    first_name = serializers.CharField(max_length=100, required=True)
    last_name = serializers.CharField(max_length=100, required=True)
    
    class Meta:
        model = CustomUser
        fields = [
            'first_name', 'last_name', 'username', 'email', 'password', 'select_role',
            'profile_picture', 'address', 'city', 'state', 'pincode',
            'categories', 'establishment_name', 'license_number'
        ]
        extra_kwargs = {
            'password': {'write_only': True}
        }

    def create(self, validated_data):
        # Extract user details
        role = validated_data.pop('select_role')
        categories = validated_data.pop('categories', [])
        establishment_name = validated_data.pop('establishment_name', None)
        license_number = validated_data.pop('license_number', None)
        profile_picture = validated_data.get('profile_picture') or '/profile-default.png'

        # Create user
        user = CustomUser.objects.create(
            username=validated_data['username'],
            email=validated_data['email'],
            first_name=validated_data['first_name'],
            last_name=validated_data['last_name'],
            password=make_password(validated_data['password']),
            is_patient=(role == 'patient'),
            is_doctor=(role == 'doctor')
        )

        # Create profile
        profile = Profile.objects.create(
            user=user,
            profile_picture=profile_picture,
            address=validated_data['address'],
            city=validated_data['city'],
            state=validated_data['state'],
            pincode=validated_data['pincode']
        )

        # If user is a doctor, create the doctor record
        if role == 'doctor':
            doctor = Doctor.objects.create(
                profile=profile,
                establishment_name=establishment_name,
                license_number=license_number
            )
            doctor.categories.set(categories)

        return user
    



class LoginSerializer(serializers.Serializer):
    username = serializers.CharField(required=True)
    password = serializers.CharField(required=True)

    def validate(self, attrs):
        user = authenticate(username=attrs['username'], password=attrs['password'])
        if user is None:
            raise serializers.ValidationError("Invalid username or password.")
        attrs['user'] = user
        return attrs  
    
# class AppointmentSerializer(serializers.ModelSerializer):
#     patient = CustomUserSerializer()
#     doctor = CustomUserSerializer()

#     class Meta:
#         model = Appointment
#         fields = ['id', 'patient', 'doctor', 'speciality', 'date', 'start_time', 'end_time', 'google_event_id']