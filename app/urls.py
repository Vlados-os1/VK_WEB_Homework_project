from django.urls import path
from app import views

app_name = 'app'

urlpatterns = [
    path('', views.index_view, name='index'),
    path('hot/', views.hot_questions_view, name='hot'),
    path('tag/<str:tag_name>/', views.tag_questions_view, name='tag'),
    path('question/<int:question_id>/', views.question_detail_view, name='question'),
    path('login/', views.login_view, name='login'),
    path('signup/', views.signup_view, name='signup'),
    path('settings/', views.settings_view, name='settings'),
    path('ask/', views.ask_question_view, name='ask'),
    path('logout', views.logout_view, name='logout'),
    path('question/<int:question_id>/vote/', views.vote_question_view, name='vote_question'),
    path('answers/<int:answer_id>/vote/', views.vote_answer_view, name='vote_answer'),
]