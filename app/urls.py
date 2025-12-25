from django.urls import path
from app.views import (
    IndexView, HotQuestionsView, TagQuestionsView, QuestionDetailView,
    LoginView, SignupView, SettingsView, AskQuestionView, LogoutView,
    AjaxVoteQuestionView, AjaxVoteAnswerView, AjaxMarkCorrectView,
    AjaxUnmarkCorrectView, SearchAutocompleteView,
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

    path('ajax/question/vote/', AjaxVoteQuestionView.as_view(), name='ajax_vote_question'),
    path('ajax/answer/vote/', AjaxVoteAnswerView.as_view(), name='ajax_vote_answer'),
    path('ajax/mark-correct/', AjaxMarkCorrectView.as_view(), name='ajax_mark_correct'),
    path('ajax/unmark-correct/', AjaxUnmarkCorrectView.as_view(), name='ajax_unmark_correct'),
    path('search/autocomplete/', SearchAutocompleteView.as_view(), name='search_autocomplete'),
]