from django.utils.translation import ugettext as _, ugettext_lazy
from django.contrib.auth import logout as auth_logout, REDIRECT_FIELD_NAME
from django.core.urlresolvers import reverse
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.views.decorators.cache import never_cache
from django.conf import settings
from django.db.models import Q
import ast
from djaken.models import Note
from djaken.models import Image

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

@never_cache
def all_notes(request, **kwargs):

    next_url = None
    render_html_path = 'djaken/all_notes.html'

    if get_user_is_logged_in(request):
        if request.method == 'GET':

            options = dict(kwargs)  
            print("all_notes::get: options = ", options)

            # Set some defaults
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

            if only_relevant == True:
                if search_text != "":
                    notes = Note.objects.filter( Q(relevant=True) & Q(author=request.user) & (Q(title__icontains=search_text) | Q(content__icontains=search_text)) ).order_by(*sort_order)
                else:
                    notes = Note.objects.filter(relevant=True, author=request.user).order_by(*sort_order)
            else:
                if search_text != "":
                    notes = Note.objects.filter( Q(author=request.user) & (Q(title__icontains=search_text) | Q(content__icontains=search_text)) ).order_by(*sort_order)
                else:
                    notes = Note.objects.filter(author=request.user).order_by(*sort_order)

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
                'notes': notes,
                'search_text': search_text,
            }

            return render(request, render_html_path, context)

    else:
        return redirect('djaken:login')

@never_cache
def view_note(request, pk, **kwargs):

    next_url = None
    render_html_path = None
 
    if get_user_is_logged_in(request):
        if request.method == 'GET':

            options = dict(kwargs)  
            print("view_note::get: options = ", options)

            note = get_object_or_404(Note, pk=pk, author=request.user)
            if 'toggle_relevant' in options.keys():
                if note.relevant == True:
                    note.relevant = False
                else:
                    note.relevant = True
                note.save(True)
            if note.is_encrypted:
                next_url = 'djaken/view_note.html'
                render_html_path = 'djaken/unlock_note.html'
            else:
                render_html_path = 'djaken/view_note.html'
            context = {
                'site_title': ugettext_lazy('Djaken'),
                'site_header': BRANDING_TITLE,
                'page_title': ugettext_lazy('View Note'),
                'content_title': note.title,
                'user_is_staff': get_user_is_staff(request),
                'user_is_logged_in': get_user_is_logged_in(request),
                'app_path': request.get_full_path(),
                'next_url': next_url,
                'note': note,
                'note_content_html': note.content_html,
            }
            return render(request, render_html_path, context)
    else:
        return redirect('djaken:login')

@never_cache
def edit_note(request, pk, **kwargs):

    next_url = None
    render_html_path = None

    if get_user_is_logged_in(request):
        if request.method == 'GET':

            options = dict(kwargs)
            print("edit_note::get: options = ", options)

            note = get_object_or_404(Note, pk=pk, author=request.user)
            if 'toggle_relevant' in options.keys():
                if note.relevant == True:
                    note.relevant = False
                else:
                    note.relevant = True
                note.save(True)
            if note.is_encrypted:
                next_url = 'djaken/edit_note.html'
                render_html_path = 'djaken/unlock_note.html'
            else:
                render_html_path = 'djaken/edit_note.html'
            context = {
                'site_title': ugettext_lazy('Djaken'),
                'site_header': BRANDING_TITLE,
                'page_title': ugettext_lazy('Edit Note'),
                'content_title': note.title,
                'user_is_staff': get_user_is_staff(request),
                'user_is_logged_in': get_user_is_logged_in(request),
                'app_path': request.get_full_path(),
                'next_url': next_url,
                'note': note,
                'note_content': note.content,
            }
            return render(request, render_html_path, context)
    else:
        return redirect('djaken:login')

@never_cache
def unlock_note(request, pk, **kwargs):

    next_url = None
    render_html_path = None

    if get_user_is_logged_in(request):

        if request.method == 'GET':

            options = dict(kwargs)
            print("unlock_note::get: options = ", options)

            return redirect('/view_note/' + pk + '/')

        if request.method == 'POST':

            print("unlock_note::post:")

            note = get_object_or_404(Note, pk=pk, author=request.user)
            render_html_path = request.POST['next_url']
            encryption_key = request.POST['encrypt_pass']
            success, unencrypted_content, unencrypted_content_html = note.get_unencrypted_content(encryption_key)

            if success:
                if render_html_path == "djaken/edit_note.html":
                    page_title = ugettext_lazy('Edit Note')
                if render_html_path == "djaken/view_note.html":
                    page_title = ugettext_lazy('View Note')
            else:
                messages.error(request, ugettext_lazy("ERROR: Could not decrypt the note! Perhaps the supplied encryption password was wrong."))
                if render_html_path == "djaken/edit_note.html":
                    return redirect('djaken:edit_note', pk=pk)
                if render_html_path == "djaken/view_note.html":
                    return redirect('djaken:view_note', pk=pk)
 
            context = {
                'site_title': ugettext_lazy('Djaken'),
                'site_header': BRANDING_TITLE,
                'page_title': page_title,
                'content_title': note.title,
                'user_is_staff': get_user_is_staff(request),
                'user_is_logged_in': get_user_is_logged_in(request),
                'app_path': request.get_full_path(),
                'next_url': next_url,
                'note': note,
                'note_content': unencrypted_content,
                'note_content_html': unencrypted_content_html,
            }
            return render(request, render_html_path, context)
    else:
        return redirect('djaken:login')

@never_cache
def save_note(request, pk, **kwargs):

    next_url = None

    if get_user_is_logged_in(request):

        if request.method == 'GET':

            options = dict(kwargs)
            print("save_note::get: options = ", options)

            return redirect('/view_note/' + pk + '/')

        if request.method == 'POST':

            print("save_note::post:")

            note = get_object_or_404(Note, pk=pk, author=request.user)
            new_title = request.POST['note_title']
            new_content = request.POST['note_content']
            image_data = request.POST['preview_image_data']
            is_encrypted =  bool(request.POST.get('is_encrypted', False))
            encryption_key = request.POST['encrypt_pass']

            note.title = new_title
            note.is_encrypted = is_encrypted
            note.encryption_key = encryption_key

            if image_data is not "":
                image = note.image_set.create(image_data=image_data)
                note.image_data_dict[str(image.id)] = image_data
                new_content += "\r\n\r\n.. image:: [[[" + str(image.id) + "]]]\r\n    :alt: Image #" + str(image.id) + "\r\n\r\n"

            note.content = new_content
            note.save()

            messages.info(request, ugettext_lazy("Note saved successfully!"))
            if is_encrypted:
                messages.warning(request, ugettext_lazy("Don't forget the encryption password!"))
            if request.POST['continue_after_save'] == "True":
                return redirect('djaken:edit_note', pk=pk)
            else:
                return redirect('djaken:view_note', pk=pk)

    else:
        return redirect('djaken:login')

@never_cache
def new_note(request, **kwargs):

    next_url = None
    render_html_path = 'djaken/edit_note.html'

    if get_user_is_logged_in(request):
        if request.method == 'GET':

            options = dict(kwargs)
            print("new_note::get: options = ", options)

            note = Note(title=ugettext_lazy('New note...'), author=request.user)
            note.save()
            messages.info(request, ugettext_lazy("New note created! Give it a new title."))

            context = {
                'site_title': ugettext_lazy('Djaken'),
                'site_header': BRANDING_TITLE,
                'page_title': ugettext_lazy('New Note'),
                'content_title': ugettext_lazy('New note...'),
                'user_is_staff': get_user_is_staff(request),
                'user_is_logged_in': get_user_is_logged_in(request),
                'app_path': request.get_full_path(),
                'note': note,
            }

            return render(request, render_html_path, context)
    else:
        return redirect('djaken:login')

