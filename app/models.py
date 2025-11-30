from django.db import models
from django.contrib.auth.models import User

from app.managers import DefaultManager, QuestionManager, AnswerManager


class UserProfile(models.Model):
    user = models.ForeignKey(User, verbose_name="Пользователь", on_delete=models.CASCADE)
    avatar = models.ImageField(verbose_name="Аватарка пользователя", upload_to='uploads/', null=True, blank=True)
    created_at = models.DateTimeField(verbose_name="Время создания профиля", auto_now_add=True)
    updated_at = models.DateTimeField(verbose_name="Время редактирования профиля", auto_now=True)

    class Meta:
        verbose_name = "Профиль пользователя"
        verbose_name_plural = "Профили пользователей"

    def __str__(self):
        return self.user.username


class Tag(models.Model):
    name = models.CharField(verbose_name="Имя тега", max_length=50, unique=True)

    class Meta:
        verbose_name = "Тег"
        verbose_name_plural = "Теги"

    def __str__(self):
        return self.name


class Question(models.Model):
    title = models.CharField(verbose_name="Вопрос", max_length=255)
    content = models.TextField(verbose_name="Описание вопроса", max_length=4000)
    author = models.ForeignKey(User, verbose_name="Автор вопроса", on_delete=models.SET_NULL, null=True, related_name="questions")
    tags = models.ManyToManyField(Tag, verbose_name="Теги вопроса", blank=True)
    created_at = models.DateTimeField(verbose_name="Время создания вопроса", auto_now_add=True)
    updated_at = models.DateTimeField(verbose_name="Время редактирования вопроса", auto_now=True)

    is_active = models.BooleanField(verbose_name="Активно?", help_text="Если TRUE - отображается пользователям", default=True)

    objects = QuestionManager()
    all_objects = DefaultManager()

    class Meta:
        verbose_name = "Вопрос"
        verbose_name_plural = "Вопросы"

    def __str__(self):
        return self.title


class Answer(models.Model):
    content = models.TextField(verbose_name="Контент", max_length=4000)
    author = models.ForeignKey(User, verbose_name="Автор ответа", on_delete=models.SET_NULL, null=True)
    question = models.ForeignKey("app.Question", verbose_name="Вопрос", on_delete=models.CASCADE, related_name="answers")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    is_active = models.BooleanField(verbose_name="Активно?", help_text="Если TRUE - отображается пользователям", default=True)

    objects = AnswerManager()
    all_objects = DefaultManager()

    class Meta:
        verbose_name = "Ответ"
        verbose_name_plural = "Ответы"

    def __str__(self):
        return f"Ответ #{self.id} к вопросу #{self.question_id}"


class QuestionLike(models.Model):
    question = models.ForeignKey("app.Question", verbose_name="Вопрос", on_delete=models.CASCADE)
    user = models.ForeignKey(User, verbose_name="Пользователь", on_delete=models.CASCADE)

    class Meta:
        unique_together = ['user', 'question']
        verbose_name = "Оценка вопроса"
        verbose_name_plural = "Оценки вопроса"

    def __str__(self):
        return f"Лайк пользователя #{self.user_id} к вопросу #{self.question_id}"


class AnswerLike(models.Model):
    answer = models.ForeignKey("app.Answer", verbose_name="Ответ", on_delete=models.CASCADE)
    user = models.ForeignKey(User, verbose_name="Пользователь", on_delete=models.CASCADE)

    class Meta:
        unique_together = ['user', 'answer']
        verbose_name = "Оценка ответа"
        verbose_name_plural = "Оценки ответа"

    def __str__(self):
        return f"Лайк пользователя #{self.user_id} к ответу #{self.answer_id}"