from django.urls import path

from .views import index, other_page, BBLoginView, profile, \
     BBLogoutView, ProfileEditView, PasswordEditView, RegisterView, \
     RegisterDoneView, user_activate, ProfileDeleteView, \
     BBPasswordResetView, BBPasswordResetDoneView, \
     BBPasswordResetConfirmView, BBPasswordResetCompleteView, \
     typing_test, typing_test_extended, bb_detail, \
     custom_typing_test, custom_test_settings, \
     multiplayer, learning_tests_view, learning_test \

app_name = 'main'
urlpatterns = [
    path('accounts/activate/<str:sign>/', user_activate, name='activate'),
    path('accounts/register/done/', RegisterDoneView.as_view(),
                                    name='register_done'),
    path('accounts/register/', RegisterView.as_view(), name='register'),
    path('accounts/logout/', BBLogoutView.as_view(), name='logout'),
    path('accounts/password/edit/', PasswordEditView.as_view(),
                                    name='password_edit'),
    path('accounts/password/reset/done/', BBPasswordResetDoneView.as_view(),
                                          name='password_reset_done'),
    path('accounts/password/reset/', BBPasswordResetView.as_view(),
                                     name='password_reset'),
    path('accounts/password/confirm/complete/',
                                    BBPasswordResetCompleteView.as_view(),
                                    name='password_reset_complete'),
    path('accounts/password/confirm/<uidb64>/<token>/',
                                    BBPasswordResetConfirmView.as_view(),
                                    name='password_reset_confirm'),
    path('accounts/profile/delete/', ProfileDeleteView.as_view(),
                                     name='profile_delete'),
    path('accounts/profile/edit/', ProfileEditView.as_view(),
                                   name='profile_edit'),
    path('accounts/profile/', profile, name='profile'),
    path('accounts/login/', BBLoginView.as_view(), name='login'),
    path('<int:rubric_pk>/<int:pk>/', bb_detail, name='bb_detail'), #delete
    path('custom/', custom_test_settings, name='custom_test'),
    path('custom/test/', custom_typing_test, name='custom_typing_test'),
    path('multiplayer/', multiplayer, name='multiplayer'),
    path('learning/', learning_tests_view, name='learning_tests'),
    path('learning/<str:test_id>/', learning_test, name='learning_test'),
    path('typing_test/', typing_test, name='typing_test'), #change name and parameter
    path('typing-test-extended/', typing_test_extended, name='typing_test_extended'),
    path('<str:page>/', other_page, name='other'), #delete
    path('', index, name='index'),
]