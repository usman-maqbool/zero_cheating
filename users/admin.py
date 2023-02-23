from django.contrib import admin
from django.contrib.auth import admin as auth_admin
from django.contrib.auth import get_user_model
from .models import UserExpertise, Profile, BusinessProfile, UpsellText, IndustryExperience, Expertise, Industry
from users.forms import UserChangeForm, UserCreationForm

User = get_user_model()


@admin.register(User)
class UserAdmin(auth_admin.UserAdmin):

    form = UserChangeForm
    add_form = UserCreationForm
    fieldsets = (
                    ("User", {"fields": ("name", "user_type", "profile_picture")}),
                    ("Approve status", {"fields": ("approve",)}),
                ) + auth_admin.UserAdmin.fieldsets
    list_display = ["id", "email", "name", "is_superuser", "user_type", "approve", "notification_email",
                    "notification_app"]
    ordering = ["-id"]
    search_fields = ["name", "email"]
    list_per_page = 50


class ProfileAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'user_type', 'hourly_rate', 'user_availability', 'verified']
    search_fields = ["user_availability", "verified", "hourly_rate"]
    list_per_page = 50

    def user_type(self, obj):
        return obj.user.user_type

    class Meta:
        model = Profile
        fields = '__all__'


@admin.register(Expertise)
class ExpertiseAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'create_at']


class UserExpertiseAdmin(admin.ModelAdmin):

    list_display = ['id', 'expertise', 'profile']

    class Meta:
        model = UserExpertise
        fields = '__all__'


admin.site.register(UserExpertise, UserExpertiseAdmin)
admin.site.register(Profile, ProfileAdmin)
admin.site.register(BusinessProfile)
admin.site.register(UpsellText)
admin.site.register(IndustryExperience)
admin.site.register(Industry)