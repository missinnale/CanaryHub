from django.urls import path

from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('link_github', views.link_github, name='link_github'),
    path('canary_hub', views.get_github_authentication, name='canary_hub'),
    path('canary_hub/repositories', views.repositories, name='repositories'),
    path('canary_hub/repositories/create_hook', views.set_up_webhooks, name='create_hook'),
    path('canary_hub/repositories/view_repo_events', views.view_webhook_events, name='repo_events'),
    path('handle_webhook', views.handle_webhook, name='handle_webhook')
]