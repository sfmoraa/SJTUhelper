from django.contrib import admin

# Register your models here.
print("admin running")
admin.site.site_header='SJTUhelper'
admin.site.site_title='SJTUhelper'
admin.site.index_title='SquitJTUhelper'




from .models import users

class users_Manager(admin.ModelAdmin):
    list_display = ['id','username','password','created_time','update_time']

admin.site.register(users,users_Manager)
