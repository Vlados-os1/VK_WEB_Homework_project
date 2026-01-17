import json
from django.core.cache import cache
from django.views.generic import TemplateView, FormView, View
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.shortcuts import redirect, get_object_or_404
from django.http import HttpRequest, JsonResponse
from django.contrib import messages
from django.conf import settings
from datetime import timedelta
from django.utils import timezone
from django.contrib.auth.models import User
from django.db.models import Q, Count
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.contrib.auth import login, logout
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.decorators.http import require_POST

from app.centrifugo_utils import generate_centrifuge_token, publish_to_centrifuge
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


class AsideMixin:
    def get_aside_context(self):
        context = {}

        popular_tags = cache.get('popular_tags')
        if popular_tags is None:
            three_months_ago = timezone.now() - timedelta(days=90)
            popular_tags_queryset = Tag.objects.filter(
                question__created_at__gte=three_months_ago,
                question__is_active=True
            ).annotate(
                question_count=Count('question')
            ).order_by('-question_count')[:10]

            popular_tags = [tag.name for tag in popular_tags_queryset]
            cache.set('popular_tags', popular_tags, 300)  # 5 минут

        context['tags'] = popular_tags

        best_members = cache.get('best_members')
        if best_members is None:
            one_week_ago = timezone.now() - timedelta(days=7)

            best_members_queryset = User.objects.filter(
                Q(questions__created_at__gte=one_week_ago) |
                Q(answer__created_at__gte=one_week_ago) |
                Q(questionlike__question__created_at__gte=one_week_ago) |
                Q(answerlike__answer__created_at__gte=one_week_ago)
            ).annotate(
                total_score=(
                        Count('questions', distinct=True) * 5 +
                        Count('answer', distinct=True) * 3 +
                        Count('questionlike', distinct=True) +
                        Count('answerlike', distinct=True)
                )
            ).order_by('-total_score')[:10]

            best_members = [member.username for member in best_members_queryset]
            cache.set('best_members', best_members, 300)  # 5 минут

        context['members'] = best_members

        context['MEDIA_URL'] = settings.MEDIA_URL
        context['USER_FILES_URL'] = settings.USER_FILES_URL

        if self.request.user.is_authenticated:
            user_profile, created = UserProfile.objects.get_or_create(user=self.request.user)
            context['userprofile'] = user_profile
            context['user_profile'] = user_profile
            context['user'] = {
                'is_authenticated': True,
                'username': self.request.user.username,
                'profile': user_profile
            }
        else:
            context['userprofile'] = None
            context['user_profile'] = None
            context['user'] = {
                'is_authenticated': False,
                'username': 'Guest'
            }

        return context

    def get_likes_context(self):
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

            return {
                'user_liked_questions': list(user_liked_questions),
                'user_liked_answers': list(user_liked_answers)
            }
        return {
            'user_liked_questions': [],
            'user_liked_answers': []
        }


@method_decorator(require_POST, name='dispatch')
class AjaxVoteQuestionView(LoginRequiredMixin, View):
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
class AjaxVoteAnswerView(LoginRequiredMixin, View):
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
class AjaxMarkCorrectView(LoginRequiredMixin, View):
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
class AjaxUnmarkCorrectView(LoginRequiredMixin, View):
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


class SearchAutocompleteView(View):
    def get(self, request, *args, **kwargs):
        query = request.GET.get('q', '').strip()

        if len(query) < 2:
            return JsonResponse({'results': []})

        cache_key = f'search_{hash(query)}'
        cached_results = cache.get(cache_key)

        if cached_results is not None:
            return JsonResponse({'results': cached_results})

        results = Question.objects.search(query)[:10]

        serialized_results = [
            {
                'id': q.id,
                'title': q.title,
                'content': q.content[:100] + '...' if len(q.content) > 100 else q.content,
                'url': reverse('app:question', args=[q.id])
            }
            for q in results
        ]

        cache.set(cache_key, serialized_results, 5 * 60)

        return JsonResponse({'results': serialized_results})


class IndexView(AsideMixin, TemplateView):
    template_name = 'index.html'
    paginate_by = 3

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        aside_context = self.get_aside_context()
        likes_context = self.get_likes_context()
        context.update(aside_context)
        context.update(likes_context)

        questions = Question.objects.new_questions()
        user_liked_questions = likes_context.get('user_liked_questions', [])
        for question in questions:
            question.is_liked_by_user = question.id in user_liked_questions
        page = paginate(questions, self.request, self.paginate_by)
        context['page'] = page
        context['questions'] = page.object_list

        return context


class HotQuestionsView(AsideMixin, TemplateView):
    template_name = 'index.html'
    paginate_by = 3

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        aside_context = self.get_aside_context()
        likes_context = self.get_likes_context()
        context.update(aside_context)
        context.update(likes_context)

        questions = Question.objects.best_questions()
        user_liked_questions = likes_context.get('user_liked_questions', [])

        for question in questions:
            question.is_liked_by_user = question.id in user_liked_questions

        page = paginate(questions, self.request, self.paginate_by)
        context['page'] = page
        context['questions'] = page.object_list

        return context


class TagQuestionsView(AsideMixin, TemplateView):
    template_name = 'index.html'
    paginate_by = 3

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        aside_context = self.get_aside_context()
        likes_context = self.get_likes_context()
        context.update(aside_context)
        context.update(likes_context)

        tag_name = kwargs.get('tag_name')
        tag = get_object_or_404(Tag, name=tag_name)

        questions = Question.objects.select_related('author').prefetch_related('tags').filter(tags=tag)
        user_liked_questions = likes_context.get('user_liked_questions', [])

        for question in questions:
            question.is_liked_by_user = question.id in user_liked_questions

        page = paginate(questions, self.request, self.paginate_by)
        context['page'] = page
        context['questions'] = page.object_list
        context['tag_name'] = tag.name

        return context


class QuestionDetailView(LoginRequiredMixin, AsideMixin, TemplateView):
    template_name = 'question.html'
    login_url = '/login/'
    redirect_field_name = 'next'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        aside_context = self.get_aside_context()
        likes_context = self.get_likes_context()
        context.update(aside_context)
        context.update(likes_context)

        question_id = kwargs.get('question_id')
        question = get_object_or_404(Question.objects.select_related('author').prefetch_related('tags'), id=question_id)

        is_author = False
        if self.request.user.is_authenticated:
            is_author = (question.author.id == self.request.user.id)

        answers = Answer.objects.select_related('author').filter(question=question).order_by('-created_at')

        correct_answer_id = None
        if hasattr(question, 'correct_answer'):
            correct_answer_id = question.correct_answer.answer_id

        user_liked_answers = likes_context.get('user_liked_answers', [])
        user_liked_questions = likes_context.get('user_liked_questions', [])

        question.is_liked_by_user = question.id in user_liked_questions

        for answer in answers:
            answer.is_correct = answer.id == correct_answer_id
            answer.is_liked_by_user = answer.id in user_liked_answers

        page = paginate(answers, self.request, per_page=3)

        if self.request.user.is_authenticated:
            context['answer_form'] = AnswerForm()

        if self.request.user.is_authenticated:
            token = generate_centrifuge_token(self.request.user.id)
            context['centrifuge_token'] = token

            centrifuge_url = settings.CENTRIFUGO_URL

            if centrifuge_url.startswith('ws://') or centrifuge_url.startswith('wss://'):
                pass
            elif centrifuge_url.startswith('http://'):
                centrifuge_url = centrifuge_url.replace('http://', 'ws://', 1)
            elif centrifuge_url.startswith('https://'):
                centrifuge_url = centrifuge_url.replace('https://', 'wss://', 1)
            elif centrifuge_url.startswith('//'):
                if settings.DEBUG:
                    centrifuge_url = 'ws:' + centrifuge_url
                else:
                    centrifuge_url = 'wss:' + centrifuge_url

            context['centrifuge_url'] = centrifuge_url
            context['centrifuge_channel'] = f"question_{question_id}"

        context.update({
            'question': question,
            'answers': page.object_list,
            'page': page,
            'is_question_author': is_author
        })

        return context

    def post(self, request, *args, **kwargs):
        question_id = kwargs.get('question_id')
        question = get_object_or_404(Question, id=question_id)

        form = AnswerForm(request.POST)
        if form.is_valid():
            try:
                answer = form.save(author=request.user, question=question)

                serialized_answer = {
                    "id": answer.id,
                    "content": answer.content,
                    "author": {
                        "id": answer.author.id,
                        "username": answer.author.username
                    },
                    "created_at": answer.created_at.strftime("%Y-%m-%d %H:%M:%S"),
                    "question_id": question_id
                }

                publish_to_centrifuge(f"question_{question_id}", {
                    "type": "new_answer",
                    "answer": serialized_answer
                })

                return redirect(f'{reverse("app:question", args=[question_id])}#answer-{answer.id}')
            except Exception as e:
                messages.error(request, f"An error occurred while saving your answer: {str(e)}")

        context = self.get_context_data(**kwargs)
        context['answer_form'] = form
        return self.render_to_response(context)


class AskQuestionFormView(LoginRequiredMixin, AsideMixin, FormView):
    template_name = 'ask.html'
    form_class = AskForm
    login_url = '/login/'
    redirect_field_name = 'next'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        return kwargs

    def form_valid(self, form):
        question = form.save(author=self.request.user)
        return redirect('app:question', question_id=question.id)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(self.get_aside_context())
        return context


class SettingsFormView(LoginRequiredMixin, AsideMixin, FormView):
    template_name = 'settings.html'
    form_class = SettingsForm
    login_url = '/login/'
    redirect_field_name = 'next'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        user_profile, created = UserProfile.objects.get_or_create(user=self.request.user)
        kwargs['instance'] = user_profile
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        _ = form.save()
        self.request.user.username = form.cleaned_data['login']
        self.request.user.email = form.cleaned_data['email']
        self.request.user.save()
        messages.success(self.request, "Settings updated successfully!")
        return redirect('app:settings')

    def form_invalid(self, form):
        messages.error(self.request, "Please correct the errors below.")
        return super().form_invalid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(self.get_aside_context())
        user_profile, created = UserProfile.objects.get_or_create(user=self.request.user)
        context['user_profile'] = user_profile
        return context


class LoginFormView(AsideMixin, FormView):
    template_name = 'login.html'
    form_class = LoginForm

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            next_url = request.GET.get('next', 'app:index')
            return redirect(next_url)
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        login(self.request, form.get_user())
        next_url = self.request.GET.get('next', 'app:index')
        return redirect(next_url)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(self.get_aside_context())
        return context


class SignupFormView(AsideMixin, FormView):
    template_name = 'signup.html'
    form_class = SignupForm

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect('app:index')
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        user = form.save()
        login(self.request, user)
        return redirect('app:index')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(self.get_aside_context())
        return context


class LogoutView(View):
    def get(self, request, *args, **kwargs):
        next_url = request.GET.get('next', 'app:index')
        logout(request)
        return redirect(next_url)