from django.conf.urls import url

from . import views

app_name = 'djaken'

urlpatterns = [
    url(r'^$', views.login, name='login'),
    url(r'^logout/$', views.logout, name='logout'),
    url(r'^all_notes/$', views.AllNotes.as_view(), name='all_notes'),
    url(r'^all_notes/toggle_relevant/$', views.AllNotes.as_view(), kwargs={'toggle_relevant':True}, name='all_notes_toggle_relevant'),
    url(r'^all_notes/sort_by_relevant/$', views.AllNotes.as_view(), kwargs={'sort_by':'relevant'}, name='all_notes_sort_by_relevant'),
    url(r'^all_notes/sort_by_modified/$', views.AllNotes.as_view(), kwargs={'sort_by':'modified'}, name='all_notes_sort_by_modified'),
    url(r'^all_notes/sort_by_created/$', views.AllNotes.as_view(), kwargs={'sort_by':'created'}, name='all_notes_sort_by_created'),
    url(r'^new_note/$', views.NewNote.as_view(), name='new_note'),
    url(r'^view_note/(?P<pk>[0-9]+)/$', views.ViewNote.as_view(), name='view_note'),
    url(r'^view_note/toggle_relevant/(?P<pk>[0-9]+)/$', views.ViewNote.as_view(), kwargs={'toggle_relevant':True}, name='view_note_toggle_relevant'),
    url(r'^edit_note/(?P<pk>[0-9]+)/$', views.EditNote.as_view(), name='edit_note'),
    url(r'^unlock_note/(?P<pk>[0-9]+)/$', views.UnlockNote.as_view(), name='unlock_note'),
    url(r'^save_note/(?P<pk>[0-9]+)/$', views.SaveNote.as_view(), name='save_note'),
]
