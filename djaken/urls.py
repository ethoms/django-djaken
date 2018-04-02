from django.conf.urls import url

from . import views

app_name = 'djaken'

urlpatterns = [
    url(r'^$', views.login, name='login'),
    url(r'^logout/$', views.logout, name='logout'),
    url(r'^all_notes/$', views.all_notes, name='all_notes'),
    url(r'^all_notes/toggle_relevant/$', views.all_notes, kwargs={'toggle_relevant':True}, name='all_notes_toggle_relevant'),
    url(r'^all_notes/sort_by_relevant/$', views.all_notes, kwargs={'sort_by':'relevant'}, name='all_notes_sort_by_relevant'),
    url(r'^all_notes/sort_by_modified/$', views.all_notes, kwargs={'sort_by':'modified'}, name='all_notes_sort_by_modified'),
    url(r'^all_notes/sort_by_created/$', views.all_notes, kwargs={'sort_by':'created'}, name='all_notes_sort_by_created'),
    url(r'^new_note/$', views.new_note, name='new_note'),
    url(r'^view_note/(?P<pk>[0-9]+)', views.view_note, name='view_note'),
    url(r'^view_note/toggle_relevant/(?P<pk>[0-9]+)/$', views.view_note, kwargs={'toggle_relevant':True}, name='view_note_toggle_relevant'),
    url(r'^edit_note/(?P<pk>[0-9]+)/$', views.edit_note, name='edit_note'),
    url(r'^unlock_note/(?P<pk>[0-9]+)/$', views.unlock_note, name='unlock_note'),
    url(r'^save_note/(?P<pk>[0-9]+)/$', views.save_note, name='save_note'),
]
