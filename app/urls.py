from django.urls import path
from app.views import (
    IndexView, HotQuestionsView, TagQuestionsView, QuestionDetailView,
    LoginView, SignupView, SettingsView, AskQuestionView,
    LogoutView, VoteQuestionView, VoteAnswerView
)

app_name = 'app'

urlpatterns = [
    path('', IndexView.as_view(), name='index'),
    path('hot/', HotQuestionsView.as_view(), name='hot'),
    path('tag/<str:tag_name>/', TagQuestionsView.as_view(), name='tag'),
    path('question/<int:question_id>/', QuestionDetailView.as_view(), name='question'),
    path('login/', LoginView.as_view(), name='login'),
    path('signup/', SignupView.as_view(), name='signup'),
    path('settings/', SettingsView.as_view(), name='settings'),
    path('ask/', AskQuestionView.as_view(), name='ask'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('question/<int:question_id>/vote/', VoteQuestionView.as_view(), name='vote_question'),
    path('answer/<int:answer_id>/vote/', VoteAnswerView.as_view(), name='vote_answer'),
]