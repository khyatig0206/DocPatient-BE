from django.contrib.auth.models import AbstractUser
from django.db import models
from Medi_BE import settings
from django.utils import timezone

class CustomUser(AbstractUser):
    is_patient = models.BooleanField(default=False)
    is_doctor = models.BooleanField(default=False)

class Category(models.Model):
    name = models.CharField(max_length=100)
    def __str__(self):
        return self.name
    
class Profile(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='profile')
    profile_picture = models.ImageField(upload_to='profile_pictures/', default='profile-default.png')
    address = models.CharField(max_length=255)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    pincode = models.IntegerField()

    def __str__(self):
        return self.user.email

class Doctor(models.Model):
    profile = models.OneToOneField(Profile, on_delete=models.CASCADE, related_name='doctor_profile')
    categories = models.ManyToManyField(Category, blank=True)  
    establishment_name = models.CharField(max_length=255, null=True, blank=True)
    license_number = models.CharField(max_length=100, null=True, blank=True)

    def __str__(self):
        return f"Dr. {self.profile.user.get_full_name()}"



class BlogPost(models.Model):
    author = models.ForeignKey(Doctor, on_delete=models.CASCADE)
    title = models.CharField(max_length=200, null=True, blank=True)
    image = models.ImageField(upload_to='blog_images/', null=True, blank=True)
    categories = models.ManyToManyField(Category, blank=True)
    summary = models.TextField(max_length=600, null=True, blank=True)
    content = models.TextField(null=True, blank=True)
    draft = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

class Appointment(models.Model):
    patient = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name="appointments_as_patient")
    doctor = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name="appointments_as_doctor")
    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField(null=True, blank=True)
    google_event_link = models.CharField(max_length=255, null=True, blank=True)

    def __str__(self):
        return f"Appointment with Dr. {self.doctor.get_full_name()} for {self.patient.get_full_name()} on {self.date} at {self.start_time}"