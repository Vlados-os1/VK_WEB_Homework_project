from django.core.management.base import BaseCommand
from django.core.cache import cache
from django.db.models import Count, Q
from django.utils import timezone
from datetime import timedelta
from django.contrib.auth.models import User


class Command(BaseCommand):
    help = 'Updates best members cache (last week)'

    def handle(self, *args, **options):
        one_week_ago = timezone.now() - timedelta(days=7)

        best_members = User.objects.filter(
            Q(questions__created_at__gte=one_week_ago) |
            Q(answer__created_at__gte=one_week_ago) |
            Q(questionlike__question__created_at__gte=one_week_ago) |
            Q(answerlike__answer__created_at__gte=one_week_ago)
        ).annotate(
            question_count=Count('questions', distinct=True),
            answer_count=Count('answer', distinct=True),
            question_like_count=Count('questionlike', distinct=True),
            answer_like_count=Count('answerlike', distinct=True),
            total_score=(
                    Count('questions', distinct=True) * 5 +
                    Count('answer', distinct=True) * 3 +
                    Count('questionlike', distinct=True) +
                    Count('answerlike', distinct=True)
            )
        ).order_by('-total_score')[:10]

        members_list = [member.username for member in best_members]

        # минута
        cache.set('best_members', members_list, 60)

        self.stdout.write(
            self.style.SUCCESS(f'Successfully updated best members cache: {members_list}')
        )