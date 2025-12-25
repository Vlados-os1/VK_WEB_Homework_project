from django.core.management.base import BaseCommand
from django.core.cache import cache
from django.db.models import Count
from django.utils import timezone
from datetime import timedelta
from app.models import Tag, Question


class Command(BaseCommand):
    help = 'Updates popular tags cache (last 3 months)'

    def handle(self, *args, **options):
        three_months_ago = timezone.now() - timedelta(days=90)

        popular_tags = Tag.objects.filter(
            question__created_at__gte=three_months_ago,
            question__is_active=True
        ).annotate(
            question_count=Count('question')
        ).order_by('-question_count')[:10]

        tags_list = [tag.name for tag in popular_tags]

        # минута
        cache.set('popular_tags', tags_list, 60)

        self.stdout.write(
            self.style.SUCCESS(f'Successfully updated popular tags cache: {tags_list}')
        )