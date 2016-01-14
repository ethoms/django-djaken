from django.contrib import admin
from djaken.models import Note

class FilterUserAdmin(admin.ModelAdmin): 

    def get_queryset(self, request): 
        qs = super(FilterUserAdmin, self).get_queryset(request)
        if request.user.is_superuser:
            return qs
        else:
            return qs.filter(author = request.user)


    def save_model(self, request, obj, form, change):
        obj.author = request.user
        obj.save()


    def has_change_permission(self, request, obj=None):
        if not obj:
            return True    # So they can see the change list page
        if request.user.is_superuser or obj.author == request.user:
            return True
        else:
            return False


    has_delete_permission = has_change_permission

class NoteAdmin(FilterUserAdmin):
    exclude = ("author",)
    list_display = ['title', 'created', 'modified', 'relevant', 'author']
    list_filter = ['title', 'created', 'modified', 'relevant', ('author', admin.RelatedOnlyFieldListFilter)]
    search_fields = ['title','content']
    date_hierarchy = 'created'
    #save_on_top = True

admin.site.register(Note, NoteAdmin)
