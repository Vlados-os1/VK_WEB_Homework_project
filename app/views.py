import json
from django.views.generic import TemplateView
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.shortcuts import redirect, get_object_or_404
from django.http import HttpRequest, JsonResponse
from django.contrib import messages
from django.conf import settings
from django.db.models import Count
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.contrib.auth import login
from django.contrib.auth import logout
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.decorators.http import require_POST
from app.models import Question, Answer, Tag, QuestionLike, AnswerLike, UserProfile, CorrectAnswer
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

@method_decorator(require_POST, name='dispatch')
class AjaxVoteQuestionView(LoginRequiredMixin, TemplateView):
    login_url = '/login/'
    redirect_field_name = 'next'

    def post(self, request, *args, **kwargs):
        try:
            content_type = (request.content_type or '').split(';')[0].strip()
            if content_type != 'application/json':
                return JsonResponse({'error': 'Content-Type must be application/json'}, status=400)
            data = json.loads(request.body)
            question_id = data.get('question_id')
            vote_type = data.get('vote_type')
            if not question_id or vote_type not in ['up', 'down']:
                return JsonResponse({'error': 'Invalid parameters'}, status=400)
            question = get_object_or_404(Question, id=question_id)
            existing_like = QuestionLike.objects.filter(
                question=question, user=request.user
            ).first()
            if vote_type == 'up':
                if not existing_like:
                    QuestionLike.objects.create(question=question, user=request.user)
                    liked = True
                else:
                    existing_like.delete()
                    liked = False
            else:
                if existing_like:
                    existing_like.delete()
                liked = False
            new_count = question.questionlike_set.count()
            return JsonResponse({
                'success': True,
                'likes_count': new_count,
                'liked': liked,
                'question_id': question_id
            })
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)


@method_decorator(require_POST, name='dispatch')
class AjaxVoteAnswerView(LoginRequiredMixin, TemplateView):
    login_url = '/login/'
    redirect_field_name = 'next'

    def post(self, request, *args, **kwargs):
        try:
            content_type = (request.content_type or '').split(';')[0].strip()
            if content_type != 'application/json':
                return JsonResponse({'error': 'Content-Type must be application/json'}, status=400)
            data = json.loads(request.body)
            answer_id = data.get('answer_id')
            vote_type = data.get('vote_type')
            if not answer_id or vote_type not in ['up', 'down']:
                return JsonResponse({'error': 'Invalid parameters'}, status=400)
            answer = get_object_or_404(Answer, id=answer_id)
            existing_like = AnswerLike.objects.filter(
                answer=answer, user=request.user
            ).first()
            if vote_type == 'up':
                if not existing_like:
                    AnswerLike.objects.create(answer=answer, user=request.user)
                    liked = True
                else:
                    existing_like.delete()
                    liked = False
            else:
                if existing_like:
                    existing_like.delete()
                liked = False
            new_count = answer.answerlike_set.count()
            return JsonResponse({
                'success': True,
                'likes_count': new_count,
                'liked': liked,
                'answer_id': answer_id
            })
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)


@method_decorator(require_POST, name='dispatch')
class AjaxMarkCorrectView(LoginRequiredMixin, TemplateView):
    login_url = '/login/'
    redirect_field_name = 'next'

    def post(self, request, *args, **kwargs):
        try:
            content_type = (request.content_type or '').split(';')[0].strip()
            if content_type != 'application/json':
                return JsonResponse({'error': 'Content-Type must be application/json'}, status=400)

            data = json.loads(request.body)
            question_id = data.get('question_id')
            answer_id = data.get('answer_id')

            if not question_id or not answer_id:
                return JsonResponse({'error': 'Invalid parameters'}, status=400)
            question = get_object_or_404(Question, id=question_id)
            answer = get_object_or_404(Answer, id=answer_id)

            if question.author != request.user:
                return JsonResponse({'error': 'Only the author of the question can mark the correct answer.'},
                                   status=403)
            if answer.question != question:
                return JsonResponse({'error': 'The answer does not belong to the question.'}, status=400)

            CorrectAnswer.objects.filter(question=question).delete()
            CorrectAnswer.objects.create(
                question=question,
                answer=answer
            )

            return JsonResponse({
                'success': True,
                'question_id': question_id,
                'answer_id': answer_id
            })
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)


@method_decorator(require_POST, name='dispatch')
class AjaxUnmarkCorrectView(LoginRequiredMixin, TemplateView):
    login_url = '/login/'
    redirect_field_name = 'next'

    def post(self, request, *args, **kwargs):
        try:
            content_type = (request.content_type or '').split(';')[0].strip()

            if content_type != 'application/json':
                return JsonResponse({'error': 'Content-Type must be application/json'}, status=400)

            data = json.loads(request.body)
            question_id = data.get('question_id')

            if not question_id:
                return JsonResponse({'error': 'Invalid parameters'}, status=400)

            question = get_object_or_404(Question, id=question_id)
            if question.author != request.user:
                return JsonResponse({'error': 'Only the author of the question can unmark the correct answer.'},
                                   status=403)
            CorrectAnswer.objects.filter(question=question).delete()
            return JsonResponse({
                'success': True,
                'question_id': question_id
            })
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)


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

        if self.request.user.is_authenticated:
            question_ids = Question.objects.values_list('id', flat=True)
            user_liked_questions = QuestionLike.objects.filter(
                question_id__in=question_ids,
                user=self.request.user
            ).values_list('question_id', flat=True)

            answer_ids = Answer.objects.values_list('id', flat=True)
            user_liked_answers = AnswerLike.objects.filter(
                answer_id__in=answer_ids,
                user=self.request.user
            ).values_list('answer_id', flat=True)

            context['user_liked_questions'] = list(user_liked_questions)
            context['user_liked_answers'] = list(user_liked_answers)
        else:
            context['user_liked_questions'] = []
            context['user_liked_answers'] = []
        context.update({
            'members': [member.user for member in best_members],
            'tags': [tag.name for tag in popular_tags],
            'user': {
                'is_authenticated': self.request.user.is_authenticated,
                'username': self.request.user.username if self.request.user.is_authenticated else 'Guest'
            },
            'USER_FILES_URL': settings.USER_FILES_URL,
        })

        context['MEDIA_URL'] = settings.MEDIA_URL

        if self.request.user.is_authenticated:
            user_profile, created = UserProfile.objects.get_or_create(user=self.request.user)
            context['userprofile'] = user_profile
            context['user_profile'] = user_profile
        else:
            context['userprofile'] = None
            context['user_profile'] = None

        return context


class IndexView(BaseView):
    template_name = 'index.html'
    paginate_by = 3

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        questions = Question.objects.new_questions()
        user_liked_questions = context.get('user_liked_questions', [])
        for question in questions:
            question.is_liked_by_user = question.id in user_liked_questions
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


class QuestionDetailView(LoginRequiredMixin, BaseView):
    template_name = 'question.html'
    login_url = '/login/'
    redirect_field_name = 'next'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        question_id = kwargs.get('question_id')
        question = get_object_or_404(Question.objects.select_related('author').prefetch_related('tags'), id=question_id)

        is_author = False
        if self.request.user.is_authenticated:
            is_author = (question.author.id == self.request.user.id)

        answers = Answer.objects.select_related('author').filter(question=question).order_by('-created_at')

        correct_answer_id = None
        if hasattr(question, 'correct_answer'):
            correct_answer_id = question.correct_answer.answer_id

        user_liked_answers = context.get('user_liked_answers', [])
        user_liked_questions = context.get('user_liked_questions', [])

        question.is_liked_by_user = question.id in user_liked_questions

        for answer in answers:
            answer.is_correct = answer.id == correct_answer_id
            answer.is_liked_by_user = answer.id in user_liked_answers

        page = paginate(answers, self.request, per_page=3)

        context.update({
            'question': question,
            'answers': page.object_list,
            'page': page,
            'is_question_author': is_author
        })

        if self.request.user.is_authenticated:
            context['answer_form'] = AnswerForm()

        return context

    def post(self, request, *args, **kwargs):
        question_id = kwargs.get('question_id')
        question = get_object_or_404(Question, id=question_id)

        form = AnswerForm(request.POST)
        if form.is_valid():
            try:
                answer = form.save(author=request.user, question=question)
                return redirect(f'{reverse("app:question", args=[question_id])}#answer-{answer.id}')
            except Exception as e:
                messages.error(request, f"An error occurred while saving your answer: {str(e)}")

        context = self.get_context_data(**kwargs)
        context['answer_form'] = form
        return self.render_to_response(context)


class AskQuestionView(LoginRequiredMixin, BaseView):
    template_name = 'ask.html'
    login_url = '/login/'
    redirect_field_name = 'next'

    def get(self, request, *args, **kwargs):
        context = self.get_context_data()
        context['form'] = AskForm()
        return self.render_to_response(context)

    def post(self, request, *args, **kwargs):
        form = AskForm(request.POST)
        if form.is_valid():
            try:
                question = form.save(author=request.user)
                return redirect('app:question', question_id=question.id)
            except Exception as e:
                messages.error(request, f"An error occurred while saving your question: {str(e)}")

        context = self.get_context_data()
        context['form'] = form
        return self.render_to_response(context)


class SettingsView(LoginRequiredMixin, BaseView):
    template_name = 'settings.html'
    login_url = '/login/'
    redirect_field_name = 'next'

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
            next_url = request.GET.get('next', 'app:index')
            return redirect(next_url)
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
        form = SignupForm(request.POST, request.FILES)

        if form.is_valid():
            user = form.save()

            login(request, user)
            return redirect('app:index')

        context = self.get_context_data()
        context['form'] = form
        return self.render_to_response(context)


class LogoutView(BaseView):
    def get(self, request, *args, **kwargs):
        next_url = request.GET.get('next', 'app:index')
        logout(request)
        return redirect(next_url)