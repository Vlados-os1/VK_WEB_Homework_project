from django.urls import path
from app.views import (
    IndexView, HotQuestionsView, TagQuestionsView, QuestionDetailView,
    LoginFormView, SignupFormView, SettingsFormView,
    AskQuestionFormView, LogoutView,
    AjaxVoteQuestionView, AjaxVoteAnswerView, AjaxMarkCorrectView,
    AjaxUnmarkCorrectView, SearchAutocompleteView,
)

app_name = 'app'

urlpatterns = [
    path('', IndexView.as_view(), name='index'),
    path('hot/', HotQuestionsView.as_view(), name='hot'),
    path('tag/<str:tag_name>/', TagQuestionsView.as_view(), name='tag'),
    path('question/<int:question_id>/', QuestionDetailView.as_view(), name='question'),
    path('login/', LoginFormView.as_view(), name='login'),
    path('signup/', SignupFormView.as_view(), name='signup'),
    path('settings/', SettingsFormView.as_view(), name='settings'),
    path('ask/', AskQuestionFormView.as_view(), name='ask'),
    path('logout/', LogoutView.as_view(), name='logout'),

    path('ajax/question/vote/', AjaxVoteQuestionView.as_view(), name='ajax_vote_question'),
    path('ajax/answer/vote/', AjaxVoteAnswerView.as_view(), name='ajax_vote_answer'),
    path('ajax/mark-correct/', AjaxMarkCorrectView.as_view(), name='ajax_mark_correct'),
    path('ajax/unmark-correct/', AjaxUnmarkCorrectView.as_view(), name='ajax_unmark_correct'),
    path('search/autocomplete/', SearchAutocompleteView.as_view(), name='search_autocomplete'),
]