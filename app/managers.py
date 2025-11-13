from django.db import models
from django.contrib.auth.models import User
from django.db.models import Count, Q


class DefaultManager(models.Manager):
    def active(self):
        return self.filter(is_active=True)


class QuestionManager(DefaultManager):
    def best_questions(self):
        return self.active().annotate(
            likes_count=Count('questionlike', distinct=True),
            answers_count=Count('questions', distinct=True),
            total_rating=models.F('likes_count') + models.F('answers_count')
        ).order_by('-total_rating', '-created_at')

    def new_questions(self):
        return self.active().order_by('-created_at')

    def with_tags(self, tag_names):
        return self.active().filter(tags__name__in=tag_names).distinct()

    def hot_questions(self):
        return self.active().annotate(
            answers_count=Count('questions', distinct=True)
        ).order_by('-answers_count', '-created_at')

    def unanswered_questions(self):
        return self.active().annotate(
            answers_count=Count('questions')
        ).filter(answers_count=0).order_by('-created_at')

    def with_user_activity(self):
        return self.active().annotate(
            likes_count=Count('questionlike'),
            answers_count=Count('questions'),
            author_name=models.F('author__username')
        )


class AnswerManager(DefaultManager):
    def best_answers(self, question_id=None):
        queryset = self.annotate(
            likes_count=Count('answerlike')
        ).order_by('-likes_count', '-created_at')

        if question_id:
            queryset = queryset.filter(question_id=question_id)

        return queryset

    def for_question(self, question_id):
        return self.filter(question_id=question_id).order_by('-created_at')
