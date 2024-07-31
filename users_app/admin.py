from .models import CustomUser, CustomUserConfirmation, Note, Tab, Follow
from django.contrib import admin


class CustomUserAdmin(admin.ModelAdmin):
    list_display = ['username', 'auth_status', 'auth_type', 'phone_number', 'email', 'province']


class FollowAdmin(admin.ModelAdmin):
    list_display = ['follower', 'following']


class CustomUserConfirmationAdmin(admin.ModelAdmin):
    list_display = ('user', 'code', 'verify_type', 'expiration_time', 'is_confirmed', 'created_time')


class TabAdmin(admin.ModelAdmin):
    list_display = ('id', 'owner', 'name', 'tab_sequence_number')


class NoteAdmin(admin.ModelAdmin):
    list_display = ('id', 'owner', 'body', 'isPinned', 'note_sequence_number', 'category')


admin.site.register(CustomUser, CustomUserAdmin)
admin.site.register(Follow, FollowAdmin)
admin.site.register(CustomUserConfirmation, CustomUserConfirmationAdmin)
admin.site.register(Note, NoteAdmin)
admin.site.register(Tab, TabAdmin)
