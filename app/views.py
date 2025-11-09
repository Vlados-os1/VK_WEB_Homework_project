import random

from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.shortcuts import render, redirect
from django.http import HttpRequest, HttpResponse
from django.contrib import messages
from django.conf import settings

mock_members = [
    'Mr. Freeman',
    'Dr. House',
    'Bender',
    'Queen Victoria',
    'V. Pupkin'
]

mock_tags = [
    'perl', 'python', 'TechnoPark', 'MySQL', 'django',
    'Mail.Ru', 'Voloshin', 'Firefox', 'black-jack'
]

mock_questions = [
    {
        'id': i,
        'title': f'How to build a moon park? #{i}',
        'content': 'Guys, i have trouble with a moon park. Can\'t find th black-jack...',
        'author': 'SpaceExplorer',
        'answers_count': 3,
        'tags': random.sample(mock_tags, 2),
        'likes': random.randint(0, 20)
    } for i in range(1, 20)]

mock_answers = [
    {
        'id': j,
        'question_id': i,
        'content': f'First of all I would like to thank you for the invitation to participate in such a discussion about moon park #{i}. This is answer #{j} to your question.',
        'author': author,
        'is_correct': j == 1,
        'likes': random.randint(0, 15),
        'created_at': f'{random.randint(1, 24)} hours ago'
    }
    for i in range(1, 20)
    for j, author in enumerate([
        'Mr. Freeman',
        'Dr. House',
        'Bender',
        'Elon Musk',
        'Neil Armstrong'
    ][:3], 1)
]

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

base_context = {
        'members': mock_members,
        'tags': mock_tags,
        'user': {'is_authenticated': False, 'username': 'Dr. Pepper'},
        'USER_FILES_URL': settings.USER_FILES_URL,
    }

def get_base_context():
    return base_context

def index_view(request):
    context = get_base_context()

    page = paginate(mock_questions, request, 3)
    context['page'] = page
    context['questions'] = page.object_list

    return render(request, 'index.html', context)


def hot_questions_view(request):
    hot_questions = sorted(mock_questions, key=lambda x: x['likes'], reverse=True)
    hot_questions = [i for i in hot_questions if i['likes'] > 15]

    context = get_base_context()
    page = paginate(hot_questions, request, 3)
    context['page'] = page
    context['questions'] = page.object_list

    return render(request, 'index.html', context)


def tag_questions_view(request, tag_name):
    filtered_questions = [q for q in mock_questions if tag_name in q['tags']]

    context = get_base_context()
    context['tag_name'] = tag_name

    page = paginate(filtered_questions, request, 3)
    context['page'] = page
    context['questions'] = page.object_list

    return render(request, 'index.html', context)


def question_detail_view(request, question_id):
    question_data = next((q for q in mock_questions if q['id'] == question_id), None)
    if not question_data:
        return HttpResponse("Question not found", status=404)

    question_answers = [a for a in mock_answers if a['question_id'] == question_id]

    context = get_base_context()
    context['question'] = question_data
    context['answers'] = question_answers

    return render(request, 'question.html', context)


def ask_question_view(request):
    context = get_base_context()

    if request.method == 'POST':
        title = request.POST.get('title')
        text = request.POST.get('text')
        tags = request.POST.get('tags')

        print("Ask: ", title, text, tags)

        new_question = {
            'id': len(mock_questions) + 1,
            'title': title,
            'content': text,
            'author': context['user']['username'],
            'answers_count': 0,
            'tags': [tag.strip() for tag in tags.split(',')] if tags else [],
            'likes': 0
        }
        mock_questions.insert(0, new_question)

        return redirect('app:index')

    return render(request, 'ask.html', context)


def login_view(request):
    context = get_base_context()

    if request.method == 'POST':
        login = request.POST.get("login")
        password = request.POST.get("password")

        if login and password:
            if password != "123":
                messages.error(request, "Invalid password! Try '123'.")
                return redirect('app:login')
            else:
                context['user']['is_authenticated'] = True
                context['user']['username'] = login
                return redirect('app:index')

    return render(request, 'login.html', context)


def signup_view(request):
    context = get_base_context()

    if request.method == 'POST':
        login = request.POST.get("login")
        email = request.POST.get("email")
        nickname = request.POST.get("nickname")
        password = request.POST.get("password")
        repeat_password = request.POST.get("repeat_password")

        if any([login, email, nickname, password, repeat_password]):
            if email == "example@mail.ru":
                messages.error(request, "Sorry, this email address already registered!")
                return render(request, 'signup.html', context)
            else:
                context['user']['is_authenticated'] = True
                context['user']['username'] = login
                return redirect('app:index')

    return render(request, 'signup.html', context)


def vote_question_view(request, question_id):
    if request.method == 'POST':
        vote_type = request.POST.get('vote_type')

        for question in mock_questions:
            if question['id'] == question_id:
                if vote_type in ['up', 'up_a']:
                    question['likes'] += 1
                elif vote_type in ['down', 'down_a']:
                    question['likes'] -= 1
                break

        if vote_type and vote_type[-1] != 'a':
            return redirect('app:index')

        return redirect('app:question', question_id=question_id)

    return redirect('app:index')


def vote_answer_view(request, answer_id):
    if request.method == 'POST':
        vote_type = request.POST.get('vote_type')
        question_id = None

        for answer in mock_answers:
            if answer['id'] == answer_id:
                if vote_type == 'up':
                    answer['likes'] += 1
                elif vote_type == 'down':
                    answer['likes'] -= 1
                question_id = answer['question_id']
                break

        if question_id:
            return redirect('app:question', question_id=question_id)

    return redirect('app:index')


def logout_view(request):
    context = get_base_context()
    context['user']['is_authenticated'] = False
    return render(request, 'index.html', context)