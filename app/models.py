from django.db import models
from django.contrib.auth.models import User

from app.managers import DefaultManager, QuestionManager, AnswerManager


class UserProfile(models.Model):
    user = models.ForeignKey(User, verbose_name="Пользователь", on_delete=models.CASCADE)
    login = models.CharField(verbose_name="Логин пользователя", max_length=150, unique=True)
    nickname = models.CharField(verbose_name="Имя пользователя", max_length=150)
    avatar = models.ImageField(verbose_name="Аватарка пользователя", upload_to='uploads/', null=True, blank=True)
    created_at = models.DateTimeField(verbose_name="Время создания профиля", auto_now_add=True)
    updated_at = models.DateTimeField(verbose_name="Время редактирования профиля", auto_now=True)

    class Meta:
        db_table = 'userprofile'
        verbose_name = "Профиль пользователя"
        verbose_name_plural = "Профили пользователей"

    def __str__(self):
        return self.nickname or self.login


class Tag(models.Model):
    name = models.CharField(verbose_name="Имя тега", max_length=50, unique=True)

    class Meta:
        db_table = 'tag'
        verbose_name = "Тег"
        verbose_name_plural = "Теги"

    def __str__(self):
        return self.name


class Question(models.Model):
    title = models.CharField(verbose_name="Вопрос", max_length=255)
    content = models.TextField(verbose_name="Описание вопроса", max_length=4000)
    author = models.ForeignKey(User, verbose_name="Автор вопроса", on_delete=models.SET_NULL, null=True, related_name="user_posts")
    tags = models.ManyToManyField(Tag, verbose_name="Теги вопроса", blank=True)
    created_at = models.DateTimeField(verbose_name="Время создания вопроса", auto_now_add=True)
    updated_at = models.DateTimeField(verbose_name="Время редактирования вопроса", auto_now=True)

    is_active = models.BooleanField(verbose_name="Активно?", help_text="Если TRUE - отображается пользователям", default=True)

    objects = QuestionManager()
    all_objects = DefaultManager()

    class Meta:
        db_table = 'question'
        verbose_name = "Вопрос"
        verbose_name_plural = "Вопросы"

    def __str__(self):
        return self.title

class Answer(models.Model):
    content = models.TextField(verbose_name="Контент", max_length=4000)
    author = models.ForeignKey(User, verbose_name="Автор ответа", on_delete=models.SET_NULL, null=True)
    question = models.ForeignKey("app.Question", verbose_name="Вопрос", on_delete=models.CASCADE, related_name="questions")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    is_active = models.BooleanField(verbose_name="Активно?", help_text="Если TRUE - отображается пользователям", default=True)

    objects = AnswerManager()
    all_objects = DefaultManager()

    class Meta:
        db_table = 'answer'
        verbose_name = "Ответ"
        verbose_name_plural = "Ответы"

    def __str__(self):
        return f"Answer to {self.question.title}"

class QuestionLike(models.Model):
    question = models.ForeignKey("app.Question", verbose_name="Вопрос", on_delete=models.CASCADE)
    user = models.ForeignKey(User, verbose_name="Пользователь", on_delete=models.CASCADE)

    class Meta:
        db_table = 'questionlike'
        unique_together = ['user', 'question']
        verbose_name = "Оценка вопроса"
        verbose_name_plural = "Оценки вопроса"

    def __str__(self):
        return f"{self.user} liked {self.question}"


class AnswerLike(models.Model):
    answer = models.ForeignKey("app.Answer", verbose_name="Ответа", on_delete=models.CASCADE)
    user = models.ForeignKey(User, verbose_name="Пользователь", on_delete=models.CASCADE)

    class Meta:
        db_table = 'answerlike'
        unique_together = ['user', 'answer']
        verbose_name = "Оценка ответа"
        verbose_name_plural = "Оценки ответа"

    def __str__(self):
        return f"{self.user} liked answer to {self.answer.question.title}"
