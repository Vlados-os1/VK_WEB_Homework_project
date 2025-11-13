import random

from django.views.generic import TemplateView
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.shortcuts import redirect, get_object_or_404
from django.http import HttpRequest, HttpResponse
from django.contrib import messages, auth
from django.conf import settings
from django.db.models import Count, Q
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator

from app.models import Question, Answer, Tag, QuestionLike, AnswerLike, UserProfile

def paginate(objects_list, request: HttpRequest, per_page=3):
    paginator = Paginator(objects_list, per_page)
    page_number = request.GET.get('page', 1)

    try:
        page = paginator.page(page_number)
    except PageNotAnInteger:
        page = paginator.page(1)
    except EmptyPage:
        page = paginator.page(paginator.num_pages)

    return page

class BaseView(TemplateView):
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        popular_tags = Tag.objects.annotate(
            question_count=Count('question')
        ).order_by('-question_count')[:10]

        best_members = UserProfile.objects.annotate(
            answer_count=Count('user__answer'),
            question_count=Count('user__user_posts')
        ).order_by('-answer_count', '-question_count')[:5]

        context.update({
            'members': [member.nickname for member in best_members],
            'tags': [tag.name for tag in popular_tags],
            'user': {
                'is_authenticated': self.request.user.is_authenticated,
                'username': self.request.user.username if self.request.user.is_authenticated else 'Guest'
            },
            'USER_FILES_URL': settings.USER_FILES_URL,
        })
        return context


class IndexView(BaseView):
    template_name = 'index.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        questions = Question.objects.new_questions()

        page = paginate(questions, self.request, 3)
        context['page'] = page
        context['questions'] = page.object_list

        return context


class HotQuestionsView(BaseView):
    template_name = 'index.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        questions = Question.objects.best_questions()

        page = paginate(questions, self.request, 3)
        context['page'] = page
        context['questions'] = page.object_list

        return context


class TagQuestionsView(BaseView):
    template_name = 'index.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        tag_name = kwargs.get('tag_name')
        context['tag_name'] = tag_name

        questions = Question.objects.with_tags([tag_name])

        page = paginate(questions, self.request, 3)
        context['page'] = page
        context['questions'] = page.object_list

        return context


class QuestionDetailView(BaseView):
    template_name = 'question.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        question_id = kwargs.get('question_id')
        question = get_object_or_404(Question, id=question_id)

        answers = Answer.objects.best_answers(question_id=question_id)

        page = paginate(answers, self.request, 4)
        context['page'] = page
        context['answers'] = page.object_list
        context['answers_count'] = answers.count()
        context['question'] = question

        if self.request.user.is_authenticated:
            context['user_liked_question'] = QuestionLike.objects.filter(
                question=question, user=self.request.user
            ).exists()

        return context


class AskQuestionView(BaseView):
    template_name = 'ask.html'

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context

    def post(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('app:login')

        title = request.POST.get('title')
        text = request.POST.get('text')
        tags_input = request.POST.get('tags')

        if title and text:
            question = Question.objects.create(
                title=title,
                content=text,
                author=request.user
            )

            if tags_input:
                tag_names = [tag.strip() for tag in tags_input.split(',')]
                for tag_name in tag_names:
                    tag, created = Tag.objects.get_or_create(name=tag_name)
                    question.tags.add(tag)

            return redirect('app:question', question_id=question.id)

        messages.error(request, "Please fill all required fields")
        return self.render_to_response(self.get_context_data())


class SettingsView(BaseView):
    template_name = 'settings.html'

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        try:
            user_profile = UserProfile.objects.get(user=self.request.user)
            context['user_profile'] = user_profile
        except UserProfile.DoesNotExist:
            context['user_profile'] = None

        return context

    def post(self, request, *args, **kwargs):
        login = request.POST.get("login")
        email = request.POST.get("email")
        nickname = request.POST.get("nickname")

        if any([login, email, nickname]):
            if email and UserProfile.objects.filter(email=email).exclude(id=request.user.id).exists():
                messages.error(request, "Sorry, this email address already registered!")
                return self.render_to_response(self.get_context_data())

            if email:
                request.user.email = email
            if login:
                request.user.username = login
            request.user.save()

            user_profile, created = UserProfile.objects.get_or_create(user=request.user)
            if nickname:
                user_profile.nickname = nickname
            if login:
                user_profile.login = login
            user_profile.save()

            messages.success(request, "Settings updated successfully!")
            return redirect('app:index')

        return self.render_to_response(self.get_context_data())


class LoginView(BaseView):
    template_name = 'login.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context

    def post(self, request, *args, **kwargs):
        username = request.POST.get("login")
        password = request.POST.get("password")

        if username and password:
            if password != "123":
                messages.error(request, "Invalid password! Try '123'.")
                return redirect('app:login')
            else:
                users = UserProfile.objects.all()
                if users.exists():
                    random_user = random.choice(users)
                    auth.login(request, random_user.user)
                    return redirect('app:index')
                else:
                    messages.error(request, "No users available.")
                    return redirect('app:login')

        messages.error(request, "Please fill all fields")
        return self.render_to_response(self.get_context_data())


class SignupView(BaseView):
    template_name = 'signup.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context

    def post(self, request, *args, **kwargs):
        username = request.POST.get("login")
        email = request.POST.get("email")
        nickname = request.POST.get("nickname")
        password = request.POST.get("password")
        repeat_password = request.POST.get("repeat_password")

        if all([username, email, password, repeat_password]):
            if password != repeat_password:
                messages.error(request, "Passwords don't match!")
                return self.render_to_response(self.get_context_data())

            if User.objects.filter(username=username).exists():
                messages.error(request, "Username already exists!")
                return self.render_to_response(self.get_context_data())

            if User.objects.filter(email=email).exists():
                messages.error(request, "Email already registered!")
                return self.render_to_response(self.get_context_data())

            user = User.objects.create_user(
                username=username,
                email=email,
                password=password
            )

            UserProfile.objects.create(
                user=user,
                login=username,
                nickname=nickname or username
            )

            auth.login(request, user)
            return redirect('app:index')

        messages.error(request, "Please fill all required fields")
        return self.render_to_response(self.get_context_data())


class VoteQuestionView(BaseView):

    @method_decorator(login_required)
    def post(self, request, *args, **kwargs):
        question_id = kwargs.get('question_id')
        vote_type = request.POST.get('vote_type')

        question = get_object_or_404(Question, id=question_id)

        existing_like = QuestionLike.objects.filter(
            question=question, user=request.user
        ).first()

        if vote_type in ['up', 'up_a']:
            if not existing_like:
                QuestionLike.objects.create(question=question, user=request.user)
        elif vote_type in ['down', 'down_a']:
            if existing_like:
                existing_like.delete()

        if vote_type and vote_type[-1] != 'a':
            return redirect('app:index')

        return redirect('app:question', question_id=question_id)


class VoteAnswerView(BaseView):

    @method_decorator(login_required)
    def post(self, request, *args, **kwargs):
        answer_id = kwargs.get('answer_id')
        vote_type = request.POST.get('vote_type')

        answer = get_object_or_404(Answer, id=answer_id)
        question_id = answer.question.id

        existing_like = AnswerLike.objects.filter(
            answer=answer, user=request.user
        ).first()

        if vote_type == 'up':
            if not existing_like:
                AnswerLike.objects.create(answer=answer, user=request.user)
        elif vote_type == 'down':
            if existing_like:
                existing_like.delete()

        return redirect('app:question', question_id=question_id)


class LogoutView(BaseView):
    def get(self, request, *args, **kwargs):
        auth.logout(request)
        return redirect('app:index')