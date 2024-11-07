from rest_framework import serializers
from .models import CustomUser, Doctor, Category, Profile , BlogPost,Appointment
from django.contrib.auth.hashers import make_password
from django.contrib.auth import authenticate
from django.templatetags.static import static




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
    profile  = ProfileSerializer()
    categories = CategorySerializer(many=True) 

    class Meta:
        model = Doctor
        fields = ['profile', 'categories', 'establishment_name' , 'license_number']



class BlogCreateSerializer(serializers.ModelSerializer):
    categories = serializers.PrimaryKeyRelatedField(queryset=Category.objects.all(), many=True, required=False)

    class Meta:
        model = BlogPost
        fields = ['title', 'image', 'categories', 'summary', 'content', 'draft']

    def create(self, validated_data):
        categories = validated_data.pop('categories', [])
        blog_post = BlogPost.objects.create(**validated_data)
        if categories:
            blog_post.categories.set(categories)  # Set the many-to-many relationship
        return blog_post



class BlogPostSerializer(serializers.ModelSerializer):
    author_name = serializers.CharField(source='author.profile.user.get_full_name', read_only=True)
    truncated_summary = serializers.SerializerMethodField()
    categories = serializers.SerializerMethodField()

    class Meta:
        model = BlogPost
        fields = ['id', 'author_name', 'image', 'title', 'created_at', 'truncated_summary','categories']

    def get_truncated_summary(self, obj):
        return self.truncate_words(obj.summary, 15)

    def truncate_words(self, value, arg):
        if not value:
            return ''
        words = value.split()
        if len(words) > arg:
            return ' '.join(words[:arg]) + '...'
        return value
    
    def get_categories(self, obj):
        # Return a list of category names
        return [category.name for category in obj.categories.all()]
    

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
    


class UserDetailsSerializer(serializers.ModelSerializer):
    address = serializers.CharField(source='profile.address', read_only=True)
    city = serializers.CharField(source='profile.city', read_only=True)
    state = serializers.CharField(source='profile.state', read_only=True)
    pincode = serializers.IntegerField(source='profile.pincode', read_only=True)
    doctor_profile = serializers.SerializerMethodField()

    class Meta:
        model = CustomUser
        fields = ['id', 'first_name', 'last_name', 'username', 'email', 'is_patient', 'is_doctor', 
                   'address', 'city', 'state', 'pincode', 'doctor_profile']

    def get_doctor_profile(self, obj):
        if obj.is_doctor:
            doctor = Doctor.objects.filter(profile=obj.profile).first()
            if doctor:
                return {
                    'categories': [category.name for category in doctor.categories.all()],
                    'establishment_name': doctor.establishment_name,
                    'license_number': doctor.license_number
                }
        return None
    

class AppointmentDetailSerializer(serializers.ModelSerializer):
    doctor_name = serializers.SerializerMethodField()
    patient_name = serializers.SerializerMethodField()
    doctor_profile = serializers.SerializerMethodField()
    patient_profile = serializers.SerializerMethodField()
    establishment_name = serializers.SerializerMethodField()
    duration = serializers.SerializerMethodField()

    class Meta:
        model = Appointment
        fields = ['doctor_name','patient_name', 'doctor_profile','patient_profile','establishment_name', 'google_event_link', 'date', 'start_time', 'end_time', 'duration']

    def get_doctor_name(self, obj):
        return f"Dr. {obj.doctor.get_full_name()}"
    
    def get_patient_name(self, obj):
        return f"{obj.patient.get_full_name()}"

    def get_doctor_profile(self, obj):
        if obj.doctor.profile and obj.doctor.profile.profile_picture:
            return obj.doctor.profile.profile_picture.url
        else:
            # Return the default profile image from the static folder
            return static('media/profile-default.png')
        
    def get_patient_profile(self, obj):
        if obj.patient.profile and obj.patient.profile.profile_picture:
            return obj.patient.profile.profile_picture.url
        else:
            # Return the default profile image from the static folder
            return static('media/profile-default.png')

    def get_establishment_name(self, obj):
        return obj.doctor.profile.doctor_profile.establishment_name

    def get_duration(self, obj):
        if obj.start_time and obj.end_time:
            start = obj.start_time
            end = obj.end_time
            duration = (end.hour * 60 + end.minute) - (start.hour * 60 + start.minute)
            hours, minutes = divmod(duration, 60)
            return f"{hours} hours, {minutes} minutes"
        return None