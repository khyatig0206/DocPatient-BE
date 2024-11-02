from django.contrib import admin

from .models import Profile,CustomUser,BlogPost,Category,Doctor
# Register your models here.

admin.site.register(CustomUser)
admin.site.register(Profile)
admin.site.register(Doctor)
admin.site.register(BlogPost)
admin.site.register(Category)