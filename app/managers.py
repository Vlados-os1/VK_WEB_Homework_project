from django.db import models
from django.contrib.auth.models import User
from django.db.models import Count, Q
from django.contrib.postgres.search import SearchVector, SearchQuery, SearchRank


class SearchManagerMixin:

    def search(self, query):
        if not query or not hasattr(self, 'psql_field_weights'):
            return self.get_queryset().none()

        search_vector = None
        for field, weight in self.psql_field_weights.items():
            if search_vector is None:
                search_vector = SearchVector(field, weight=weight)
            else:
                search_vector += SearchVector(field, weight=weight)

        search_query = SearchQuery(query)

        queryset = self.get_queryset().annotate(
            rank=SearchRank(search_vector, search_query),
            search_vector=search_vector
        ).filter(
            search_vector=search_query
        ).order_by('-rank')

        return queryset


class DefaultManager(models.Manager):
    def active(self):
        return self.filter(is_active=True)


class QuestionManager(SearchManagerMixin, DefaultManager):
    psql_field_weights = {'title': "A", 'content': "B"}
    use_in_migrations = True

    def best_questions(self):
        return self.active().select_related('author').prefetch_related('tags').annotate(
            likes_count=Count('questionlike', distinct=True),
            answers_count=Count('answers', distinct=True),
            total_rating=models.F('likes_count') + models.F('answers_count')
        ).order_by('-total_rating', '-created_at')

    def new_questions(self):
        return self.active().select_related('author').prefetch_related('tags').order_by('-created_at')

    def with_tags(self, tag_names):
        return self.active().select_related('author').prefetch_related('tags').filter(
            tags__name__in=tag_names).distinct()

    def hot_questions(self):
        return self.active().select_related('author').prefetch_related('tags').annotate(
            answers_count=Count('answers', distinct=True)
        ).order_by('-answers_count', '-created_at')

    def unanswered_questions(self):
        return self.active().select_related('author').prefetch_related('tags').annotate(
            answers_count=Count('answers')
        ).filter(answers_count=0).order_by('-created_at')

    def with_user_activity(self):
        return self.active().select_related('author').prefetch_related('tags').annotate(
            likes_count=Count('questionlike'),
            answers_count=Count('answers'),
            author_name=models.F('author__username')
        )


class AnswerQuerySet(models.QuerySet):
    def best_answers(self):
        return self.select_related('author').annotate(
            likes_count=Count('answerlike')
        ).order_by('-likes_count', '-created_at')

class AnswerManager(DefaultManager):
    def get_queryset(self):
        return AnswerQuerySet(self.model, using=self._db)

    def best_answers(self):
        return self.get_queryset().best_answers()

    def for_question(self, question_id):
        return self.select_related('author').filter(question_id=question_id).order_by('-created_at')
