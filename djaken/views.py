from django.utils.translation import ugettext as _, ugettext_lazy
from django.contrib.auth import logout as auth_logout, REDIRECT_FIELD_NAME
from django.core.urlresolvers import reverse
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.views import generic
from django.views.decorators.cache import cache_control
from djaken.models import Note
from django.conf import settings
from django.db.models import Q
import ast

"""
Message examples
        messages.info(request, 'Hello World')
        messages.warning(request, 'Oh my gosh!')
        messages.error(request, 'Oh no!')
"""

BRANDING_TITLE = getattr(settings, "DJAKEN_BRANDING_TITLE", ugettext_lazy('Djaken Notes'))

def get_user_is_staff(request):
    return request.user.is_staff

def get_user_is_logged_in(request):
    return request.user.is_active

def login(request, extra_context=None):

    if request.method == 'GET' and get_user_is_staff(request):
        # Already logged-in, redirect to notes listing page
        return redirect('djaken:all_notes')

    from django.contrib.auth.views import login
 
    # Since this module gets imported in the application's root package,
    # it cannot import models from other applications at the module level,
    # and django.contrib.admin.forms eventually imports User.

    from django.contrib.admin.forms import AdminAuthenticationForm

    context = {
        'site_title': ugettext_lazy('Djaken'),
        'site_header': BRANDING_TITLE, 
        'page_title': ugettext_lazy('Log in'),
        'user_is_staff': get_user_is_staff(request),
        'user_is_logged_in': get_user_is_logged_in(request),
        'login_error_text': ugettext_lazy('The username and password is incorrect, please try again.'),
        'app_path': request.get_full_path(), 
    }

    if (REDIRECT_FIELD_NAME not in request.GET and REDIRECT_FIELD_NAME not in request.POST):
        context[REDIRECT_FIELD_NAME] = reverse('djaken:all_notes', current_app='djaken')

    context.update(extra_context or {})
    
    defaults = {
        'extra_context': context,
        'authentication_form': AdminAuthenticationForm,
        'template_name': 'djaken/login.html',
    }

    request.current_app = 'djaken'
    return login(request, **defaults)

def logout(request, extra_context=None):

    context = {}
    context.update(extra_context or {})

    defaults = {
        'extra_context': context,
    }
 
    request.current_app = 'djaken'

    auth_logout(request)
    return redirect('djaken:login') 

class AllNotes(generic.DetailView):

    def get(self, request, **kwargs):

        options = dict(kwargs)
        print("options = ", options)

        ## Set some defaults
        sort_order = ['-relevant','-modified','-created']
        only_relevant = True
        search_text = ""

        query_string_flat = request.META['QUERY_STRING'].replace('%20', ' ').replace('%27',"'").replace('%5B','[').replace('%5D',']')

        if query_string_flat != "":
            query_strings = query_string_flat.split('&', query_string_flat.count('&'))

            for query_string in query_strings:
                if 'sort_order=' in query_string:
                    try:
                        sort_order_string = query_string.split('=',1)[1]
                        sort_order = ast.literal_eval(sort_order_string) 
                    except:
                        pass
                if 'only_relevant=' in query_string:
                    try:
                        only_relevant_string = query_string.split('=',1)[1]
                        only_relevant = ast.literal_eval(only_relevant_string) 
                    except:
                        pass
                if 'search=' in query_string:
                    try:
                        search_string = query_string.split('=',1)[1]
                        search_text = str(search_string)
                    except:
                        pass

        if 'toggle_relevant' in options.keys():
            if only_relevant == True:
                only_relevant = False
            else:
                only_relevant = True

        if 'sort_by' in options.keys():
            sort_by = options['sort_by']
            if sort_by in sort_order:
                sort_order.remove(sort_by)
                sort_order.insert(0,"-" + sort_by)
            elif "-" + sort_by in sort_order:
                sort_order.remove("-" + sort_by)
                sort_order.insert(0,sort_by)
        
        if request.user.is_active:
            if only_relevant == True:
                if search_text != "":
                    self.notes = Note.objects.filter( Q(relevant=True) & Q(author=request.user) & (Q(title__icontains=search_text) | Q(content__icontains=search_text)) ).order_by(*sort_order)
                else:
                    self.notes = Note.objects.filter(relevant=True, author=request.user).order_by(*sort_order)
            else:
                if search_text != "":
                    self.notes = Note.objects.filter( Q(author=request.user) & (Q(title__icontains=search_text) | Q(content__icontains=search_text)) ).order_by(*sort_order)
                else:
                    self.notes = Note.objects.filter(author=request.user).order_by(*sort_order)
            return render(request, 'djaken/all_notes.html', self.get_context_data(request, only_relevant, sort_order, search_text))
        else:
            return redirect('djaken:login')

    def get_context_data(self, request, only_relevant, sort_order, search_text):
        context = {
            'site_title': ugettext_lazy('Djaken'),
            'site_header': BRANDING_TITLE,
            'page_title': ugettext_lazy('All Notes'),
            'content_title': ugettext_lazy('All Notes'),
            'user_is_staff': get_user_is_staff(request),
            'user_is_logged_in': get_user_is_logged_in(request),
            'app_path': request.get_full_path(),
            'only_relevant': only_relevant,
            'sort_order': sort_order,
            'notes': self.notes,
            'search_text': search_text,
        }
        return context
            
class ViewNote(generic.DetailView):

    next_url = None

    @cache_control(max_age=0, no_cache=True, no_store=True, must_revalidate=True)
    def get(self, request, pk, **kwargs):

        options = dict(kwargs)

        if request.user.is_active:
            self.note = get_object_or_404(Note, pk=pk, author=request.user)
            if 'toggle_relevant' in options.keys():
                if self.note.relevant == True:
                    self.note.relevant = False
                else:
                    self.note.relevant = True
                self.note.save(True)
            if self.note.is_encrypted:
                self.next_url = 'djaken/view_note.html'
                return render(request, 'djaken/unlock_note.html', self.get_context_data(request))
            else:
                return render(request, 'djaken/view_note.html', self.get_context_data(request))
        else:
            return redirect('djaken:login')    

    def get_context_data(self, request):
        context = {
            'site_title': ugettext_lazy('Djaken'),
            'site_header': BRANDING_TITLE,
            'page_title': ugettext_lazy('View Note'),
            'content_title': self.note.title,
            'user_is_staff': get_user_is_staff(request),
            'user_is_logged_in': get_user_is_logged_in(request),
            'app_path': request.get_full_path(),
            'next_url': self.next_url,
            'note': self.note,
            'note_content_html': self.note.content_html,
        }
        return context

class EditNote(generic.DetailView):

    next_url = None

    @cache_control(max_age=0, no_cache=True, no_store=True, must_revalidate=True)
    def get(self, request, pk):

        if request.user.is_active:
            self.note = get_object_or_404(Note, pk=pk, author=request.user)
            if self.note.is_encrypted:
                self.next_url = 'djaken/edit_note.html' 
                return render(request, 'djaken/unlock_note.html', self.get_context_data(request))
            else:
                return render(request, 'djaken/edit_note.html', self.get_context_data(request))
        else:
            return redirect('djaken:login')

    def get_context_data(self, request):
        context = {
            'site_title': ugettext_lazy('Djaken'),
            'site_header': BRANDING_TITLE,
            'page_title': ugettext_lazy('Edit Note'),
            'content_title': self.note.title,
            'user_is_staff': request.user.is_staff,
            'user_is_logged_in': request.user.is_active,
            'app_path': request.get_full_path(),
            'next_url': self.next_url,
            'note': self.note,
            'note_content': self.note.content,
        }
        return context

class UnlockNote(generic.DetailView):

    next_url = None
                
    @cache_control(max_age=0, no_cache=True, no_store=True, must_revalidate=True)
    def post(self, request, pk):

        if request.user.is_active:
            self.note = get_object_or_404(Note, pk=pk, author=request.user)
            url = request.POST['next_url']
            encryption_key = request.POST['encrypt_pass']

            success, unencrypted_content, unencrypted_content_html = self.note.get_unencrypted_content(encryption_key)

            if success:
                if url == "djaken/edit_note.html":
                    page_title = ugettext_lazy('Edit Note')
                if url == "djaken/view_note.html":
                    page_title = ugettext_lazy('View Note')
                return render(request, url, self.get_context_data(request, page_title, unencrypted_content, unencrypted_content_html))
            else:
                messages.error(request, ugettext_lazy("ERROR: Could not decrypt the note! Perhaps the supplied encryption password was wrong."))
                if url == "djaken/edit_note.html":
                    return redirect('djaken:edit_note', pk=pk)
                if url == "djaken/view_note.html":
                    return redirect('djaken:view_note', pk=pk)
        else:
            return redirect('djaken:login')

    def get_context_data(self, request, page_title, unencrypted_content, unencrypted_content_html):
        context = {  
            'site_title': ugettext_lazy('Djaken'),
            'site_header': BRANDING_TITLE,
            'page_title': page_title,
            'content_title': self.note.title,
            'user_is_staff': request.user.is_staff,
            'user_is_logged_in': request.user.is_active,
            'app_path': request.get_full_path(),
            'next_url': self.next_url,
            'note': self.note,
            'note_content': unencrypted_content, 
            'note_content_html': unencrypted_content_html, 
        }   
        return context


class SaveNote(generic.View):

    def post(self, request, pk):

        if request.user.is_active:
            self.note = get_object_or_404(Note, pk=pk, author=request.user)
            new_title = request.POST['note_title']
            new_content = request.POST['note_content']
            is_encrypted =  bool(request.POST.get('is_encrypted', False))
            encryption_key = request.POST['encrypt_pass']

            self.note.title = new_title
            self.note.content = new_content
            self.note.is_encrypted = is_encrypted
            self.note.encryption_key = encryption_key
            self.note.save()

            messages.info(request, ugettext_lazy("Note saved successfully!"))
            if is_encrypted:
                messages.warning(request, ugettext_lazy("WARNING: don't forget the encryption password!"))
            if request.POST['continue_after_save'] == "True":
                return redirect('djaken:edit_note', pk=pk)
            else:
                return redirect('djaken:view_note', pk=pk)
        else:
            return redirect('djaken:login')

class NewNote(generic.View):

    def get(self, request):
        if request.user.is_active:
            self.note = Note(title=ugettext_lazy('New note...'), author=request.user)
            self.note.save()
            messages.info(request, ugettext_lazy("New note created! Give it a new title."))
            return render(request, 'djaken/edit_note.html', self.get_context_data(request))
        else:
            return redirect('djaken:login')

    def get_context_data(self, request):
        context = {
            'site_title': ugettext_lazy('Djaken'),
            'site_header': BRANDING_TITLE,
            'page_title': ugettext_lazy('New Note'),
            'content_title': ugettext_lazy('New note...'),
            'user_is_staff': request.user.is_staff,
            'user_is_logged_in': request.user.is_active,
            'app_path': request.get_full_path(),
            'note': self.note,
        }
        return context


"""
def view_note(request, pk):
 
    if request.method == 'GET' and get_user_is_logged_in(request):
        note = get_object_or_404(Note, pk=pk, author=request.user)
        context = {
            'site_title': ugettext_lazy('Djaken'),
            'site_header': BRANDING_TITLE,
            'page_title': ugettext_lazy('View Note'),
            'content_title': note.title,
            'user_is_staff': get_user_is_staff(request),
            'user_is_logged_in': get_user_is_logged_in(request),
            'app_path': request.get_full_path(),
            'note': note,
        }
        return render(request, 'djaken/view_note.html', context)
    else:
        return redirect('djaken:login')
"""
