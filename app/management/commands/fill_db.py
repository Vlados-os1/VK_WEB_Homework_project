from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from app.models import Question, UserProfile, Answer, Tag, QuestionLike, AnswerLike
import random

FAKE_QUESTION_CONTENT = """
Lorem ipsum dolor sit amet consectetur adipisicing elit. Ab reiciendis
architecto temporibus exercitationem error dolores nihil cumque unde 
iste eos! Maiores iste voluptatem quia tempore ullam accusantium est,
provident odit?
"""

FAKE_ANSWER_CONTENT = """
Lorem ipsum dolor sit amet consectetur adipisicing elit. Ab reiciendis
architecto temporibus exercitationem error dolores nihil cumque unde 
iste eos! Maiores iste voluptatem quia tempore ullam accusantium est,
provident odit?
"""


class Command(BaseCommand):
    help = 'Fill database with test data'

    def add_arguments(self, parser):
        parser.add_argument('ratio', type=int, help='Ratio for generating data', default=10000)

    def handle(self, *args, **options):
        ratio = options['ratio']

        self.stdout.write(f'Starting database fill with ratio: {ratio}')

        users_count = self.create_users(ratio)
        tags_count = self.create_tags(ratio)
        questions_count = self.create_questions(ratio * 10)
        answers_count = self.create_answers(ratio * 100)
        question_likes_count = self.create_question_likes(ratio * 200)
        answer_likes_count = self.create_answer_likes(ratio * 200)

        self.stdout.write(
            self.style.SUCCESS(
                f'Database filled successfully!\n'
                f'Users: {users_count}\n'
                f'Tags: {tags_count}\n'
                f'Questions: {questions_count}\n'
                f'Answers: {answers_count}\n'
                f'Question likes: {question_likes_count}\n'
                f'Answer likes: {answer_likes_count}'
            )
        )

    def create_users(self, count):
        """Создание пользователей и их профилей"""
        existing_count = User.objects.count()
        users = []
        user_profiles = []

        for i in range(count):
            username = f'user_{existing_count + i + 1}'
            email = f'{username}@example.com'

            user = User(
                username=username,
                email=email,
                password='testpassword123'
            )
            users.append(user)

        created_users = User.objects.bulk_create(users, batch_size=1000)

        for user in created_users:
            profile = UserProfile(
                user=user,
                login=user.username,
                nickname=f'nickname_{user.username}',
                avatar=None
            )
            user_profiles.append(profile)

        UserProfile.objects.bulk_create(user_profiles, batch_size=1000)
        return len(created_users)

    def create_tags(self, count):
        """Создание тегов"""
        existing_count = Tag.objects.count()
        tags = []
        for i in range(count):
            name = f'tag_{existing_count + i + 1}'
            tags.append(Tag(name=name))

        created_tags = Tag.objects.bulk_create(tags, batch_size=1000)
        return len(created_tags)

    def create_questions(self, count):
        """Создание вопросов"""
        users = list(User.objects.all())
        tags = list(Tag.objects.all())

        if not users:
            self.stdout.write(self.style.WARNING('No users found. Please create users first.'))
            return 0

        existing_count = Question.objects.count()
        questions = []

        for i in range(count):
            questions.append(Question(
                title=f'Question #{existing_count + i + 1}',
                content=FAKE_QUESTION_CONTENT,
                author=random.choice(users),
                is_active=True
            ))

        created_questions = Question.objects.bulk_create(questions, batch_size=1000)

        for question in created_questions:
            question_tags = random.sample(tags, min(random.randint(1, 5), len(tags)))
            question.tags.set(question_tags)

        return len(created_questions)

    def create_answers(self, count):
        """Создание ответов"""
        users = list(User.objects.all())
        questions = list(Question.objects.all())

        if not users or not questions:
            self.stdout.write(self.style.WARNING('No users or questions found.'))
            return 0

        answers = []
        for i in range(count):
            answers.append(Answer(
                content=FAKE_ANSWER_CONTENT,
                author=random.choice(users),
                question=random.choice(questions)
            ))

        created_answers = Answer.objects.bulk_create(answers, batch_size=1000)
        return len(created_answers)

    def create_question_likes(self, count):
        """Создание лайков вопросов"""
        users = list(User.objects.all())
        questions = list(Question.objects.all())

        if not users or not questions:
            self.stdout.write(self.style.WARNING('No users or questions found for likes.'))
            return 0

        likes_to_create = []
        used_pairs = set()

        for i in range(count):
            user = random.choice(users)
            question = random.choice(questions)
            pair = (user.id, question.id)

            if pair not in used_pairs:
                likes_to_create.append(QuestionLike(
                    user=user,
                    question=question
                ))
                used_pairs.add(pair)

        created_likes = QuestionLike.objects.bulk_create(likes_to_create, batch_size=2000)
        return len(created_likes)

    def create_answer_likes(self, count):
        """Создание лайков ответов"""
        users = list(User.objects.all())
        answers = list(Answer.objects.all())

        if not users or not answers:
            self.stdout.write(self.style.WARNING('No users or answers found for likes.'))
            return 0

        likes_to_create = []
        used_pairs = set()

        for i in range(count):
            user = random.choice(users)
            answer = random.choice(answers)
            pair = (user.id, answer.id)

            if pair not in used_pairs:
                likes_to_create.append(AnswerLike(
                    user=user,
                    answer=answer
                ))
                used_pairs.add(pair)

        created_likes = AnswerLike.objects.bulk_create(likes_to_create, batch_size=2000)
        return len(created_likes)