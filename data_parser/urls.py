from django.contrib.auth import views as auth_views
from django.urls import path, include
from drf_yasg import openapi
from drf_yasg.views import get_schema_view

from .forms import UserLoginForm
from .views import *

app_name = 'data_parser'


urlpatterns = [
    path('login/',
         auth_views.LoginView.as_view(template_name="registration/login.html", authentication_form=UserLoginForm),
         name='login'),
    path('profile/', profile_view, name="profile"),
    path('register', RegisterView.as_view(), name="register"),
    path('password_reset/', WebPasswordResetView.as_view(), name="password_reset"),
    path('password_reset/done/', WebPasswordResetDoneView.as_view(), name="password_reset_done"),
    path('reset/<uidb64>/<token>/',
         WebPasswordResetConfirmView.as_view(),
         name='password_reset_confirm'),
    path('reset/done/',
         WebPasswordResetCompleteView.as_view(),
         name='password_reset_complete'),
    path('password_change/', WebPasswordChangeView.as_view(), name="password_change"),
    path('password_change/done/', WebPasswordChangeDoneView.as_view(), name="password_change_done"),
    path('view_links/', urls_view, name='view_links'),
    path('add_link/', add_link, name='add_link'),
    path('edit_link/<int:link_id>/', edit_link, name='edit_link'),
    path('view_link/<int:link_id>/', view_link, name='view_link'),
    path('delete_all_links/', delete_all_links, name='delete_all_links'),
    path('delete_selected_links/', delete_selected_links, name='delete_selected_links'),
    path('url_parser/', url_parser, name='url_parser'),
    path('url_parser/<path:url>/', url_parser_by_link, name='url_parser'),
    path('view_collections/', view_collections, name='view_collections'),
    path('view_collections/<str:collection_name>/', view_collection, name='view_collection'),
    path('delete_all_collections/', delete_all_collections, name='delete_all_collections'),
    path('delete_selected_collections/', delete_selected_collections, name='delete_selected_collections'),
    path('edit_collection/<int:collection_id>/', edit_collection, name='edit_collection'),
    path('view_top_users/', view_top_users, name='view_top_users'),
    path('', lambda request: redirect('profile/', permanent=True)),
]
