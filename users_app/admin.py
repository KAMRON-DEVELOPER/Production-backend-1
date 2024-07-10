from .models import CustomUser, CustomUserConfirmation, Note, NoteCategory
from django.contrib import admin


class CustomUserAdmin(admin.ModelAdmin):
    list_display = ['username', 'auth_status', 'auth_type', 'phone_number', 'province']


class CustomUserConfirmationAdmin(admin.ModelAdmin):
    list_display = ('user', 'code', 'verify_type', 'expiration_time', 'is_confirmed', 'created_time')


class NoteAdmin(admin.ModelAdmin):
    list_display = ('owner', 'text', 'isPinned', 'sequence_number', 'category', 'created_time', 'updated_time')


class NoteCategoryAdmin(admin.ModelAdmin):
    list_display = ('category_name', 'owner')


admin.site.register(CustomUser, CustomUserAdmin)
admin.site.register(CustomUserConfirmation, CustomUserConfirmationAdmin)
admin.site.register(Note, NoteAdmin)
admin.site.register(NoteCategory, NoteCategoryAdmin)
