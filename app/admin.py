from django.contrib import admin

from app.models import Question, QuestionLike, AnswerLike, Answer, UserProfile

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    ...


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    raw_id_fields = ['author']


@admin.register(Answer)
class AnswerAdmin(admin.ModelAdmin):
    ...


@admin.register(QuestionLike)
class QuestionLikeAdmin(admin.ModelAdmin):
    ...


@admin.register(AnswerLike)
class AnswerLikeAdmin(admin.ModelAdmin):
    ...
