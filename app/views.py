from django.views.generic import TemplateView
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.shortcuts import redirect, get_object_or_404
from django.http import HttpRequest
from django.contrib import messages
from django.conf import settings
from django.db.models import Count
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.contrib.auth import login
from django.urls import reverse
from django.contrib.auth import logout

from app.models import Question, Answer, Tag, QuestionLike, AnswerLike, UserProfile
from app.forms import LoginForm, AskForm, AnswerForm, SignupForm, SettingsForm

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

        best_members = UserProfile.objects.select_related('user').annotate(
            answer_count=Count('user__answer'),
            question_count=Count('user__questions')
        ).order_by('-answer_count', '-question_count')[:5]

        context.update({
            'members': [member.user for member in best_members],
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
    paginate_by = 3

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        questions = Question.objects.new_questions()

        page = paginate(questions, self.request, self.paginate_by)
        context['page'] = page
        context['questions'] = page.object_list

        return context


class HotQuestionsView(BaseView):
    template_name = 'index.html'
    paginate_by = 3

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        questions = Question.objects.best_questions()

        page = paginate(questions, self.request, self.paginate_by)
        context['page'] = page
        context['questions'] = page.object_list

        return context


class TagQuestionsView(BaseView):
    template_name = 'index.html'
    paginate_by = 3

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        tag_name = kwargs.get('tag_name')
        tag = get_object_or_404(Tag, name=tag_name)

        questions = Question.objects.select_related('author').prefetch_related('tags').filter(tags=tag)

        page = paginate(questions, self.request, self.paginate_by)
        context['page'] = page
        context['questions'] = page.object_list
        context['tag_name'] = tag.name

        return context


class QuestionDetailView(BaseView):
    template_name = 'question.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        question_id = kwargs.get('question_id')
        question = get_object_or_404(Question.objects.select_related('author').prefetch_related('tags'), id=question_id)

        answers = Answer.objects.select_related('author').filter(question=question).order_by('-created_at')

        page = paginate(answers, self.request, per_page=3)

        context.update({
            'question': question,
            'answers': page.object_list,
            'page': page
        })

        if self.request.user.is_authenticated:
            context['answer_form'] = AnswerForm()

        return context

    def post(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect(f'{reverse("app:login")}?next={request.path}')

        question_id = kwargs.get('question_id')
        question = get_object_or_404(Question, id=question_id)

        form = AnswerForm(request.POST)
        if form.is_valid():
            answer = form.save(commit=False)
            answer.author = request.user
            answer.question = question
            answer.save()

            return redirect(f'{reverse("app:question", args=[question_id])}#answer-{answer.id}')

        context = self.get_context_data(**kwargs)
        context['answer_form'] = form
        return self.render_to_response(context)


class AskQuestionView(BaseView):
    template_name = 'ask.html'

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

    def get(self, request, *args, **kwargs):
        context = self.get_context_data()
        context['form'] = AskForm()
        return self.render_to_response(context)

    def post(self, request, *args, **kwargs):
        form = AskForm(request.POST)
        if form.is_valid():
            question = form.save(commit=False)
            question.author = request.user
            question.save()

            tags_input = form.cleaned_data.get('tags', '')
            if tags_input:
                tag_names = [tag.strip() for tag in tags_input.split(',')]
                for tag_name in tag_names:
                    tag, created = Tag.objects.get_or_create(name=tag_name)
                    question.tags.add(tag)

            return redirect('app:question', question_id=question.id)

        context = self.get_context_data()
        context['form'] = form
        return self.render_to_response(context)


class SettingsView(BaseView):
    template_name = 'settings.html'

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

    def get(self, request, *args, **kwargs):
        user_profile, created = UserProfile.objects.get_or_create(user=request.user)
        form = SettingsForm(instance=user_profile, user=request.user)
        context = self.get_context_data()
        context['form'] = form
        context['user_profile'] = user_profile
        return self.render_to_response(context)

    def post(self, request, *args, **kwargs):
        user_profile, created = UserProfile.objects.get_or_create(user=request.user)
        form = SettingsForm(
            request.POST,
            request.FILES,
            instance=user_profile,
            user=request.user
        )

        if form.is_valid():
            form.save()

            request.user.username = form.cleaned_data['login']
            request.user.email = form.cleaned_data['email']
            request.user.save()

            messages.success(request, "Settings updated successfully!")
            return redirect('app:settings')
        else:
            messages.error(request, "Please correct the errors below.")

        context = self.get_context_data()
        context['form'] = form
        context['user_profile'] = user_profile
        return self.render_to_response(context)


class LoginView(BaseView):
    template_name = 'login.html'

    def get(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect(self.get_success_url())
        context = self.get_context_data()
        context['form'] = LoginForm()
        return self.render_to_response(context)

    def post(self, request, *args, **kwargs):
        form = LoginForm(data=request.POST)
        if form.is_valid():
            login(request, form.get_user())
            next_url = request.GET.get('next', 'app:index')
            return redirect(next_url)

        context = self.get_context_data()
        context['form'] = form
        return self.render_to_response(context)

class SignupView(BaseView):
    template_name = 'signup.html'

    def get(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect('app:index')
        context = self.get_context_data()
        context['form'] = SignupForm()
        return self.render_to_response(context)

    def post(self, request, *args, **kwargs):
        form = SignupForm(request.POST)
        if form.is_valid():
            user = form.save()

            login(request, user)
            return redirect('app:index')

        context = self.get_context_data()
        context['form'] = form
        return self.render_to_response(context)


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
        next_url = request.GET.get('next', 'app:index')
        logout(request)
        return redirect(next_url)