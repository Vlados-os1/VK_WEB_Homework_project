from flask import Flask, render_template, request, redirect, url_for, flash

app = Flask(__name__, template_folder='../public', static_folder='../static')
app.secret_key = 'your_secret_key_here'

mock_questions = [
    {
        'id': 1,
        'title': 'How to build a moon park?',
        'content': 'Guys, i have trouble with a moon park. Can\'t find th black-jack...',
        'author': 'SpaceExplorer',
        'answers_count': 3,
        'tags': ['black-jack', 'bender']
    },
    {
        'id': 2,
        'title': 'How to build a moon park?',
        'content': 'Guys, i have trouble with a moon park. Can\'t find th black-jack...',
        'author': 'SpaceExplorer',
        'answers_count': 3,
        'tags': ['black-jack', 'bender']
    },
    {
        'id': 3,
        'title': 'How to build a moon park?',
        'content': 'Guys, i have trouble with a moon park. Can\'t find th black-jack...',
        'author': 'SpaceExplorer',
        'answers_count': 3,
        'tags': ['black-jack', 'bender']
    },
]

mock_answers = [
    {
        'id': 1,
        'question_id': 1,
        'content': 'First of all I would like to thank you for the invitation to participate in such a … Russia is the huge territory which in many respects needs to be render habitable.',
        'author': 'Mr. Freeman',
        'is_correct': True,
        'created_at': '2 hours ago'
    },
    {
        'id': 2,
        'question_id': 1,
        'content': 'First of all I would like to thank you for the invitation to participate in such a … Russia is the huge territory which in many respects needs to be render habitable.',
        'author': 'Dr. House',
        'is_correct': False,
        'created_at': '5 hours ago'
    },
    {
        'id': 3,
        'question_id': 1,
        'content': 'First of all I would like to thank you for the invitation to participate in such a … Russia is the huge territory which in many respects needs to be render habitable.',
        'author': 'Bender',
        'is_correct': False,
        'created_at': '1 day ago'
    }
]

mock_members = [
    'Mr. Freeman',
    'Dr. House', 
    'Bender',
    'Queen Victoria',
    'V. Pupkin'
]

mock_tags = [
    'perl', 'python', 'TechnoPark', 'MySQL', 'django',
    'Mail.Ru', 'Voloshin', 'Firefox'
]

@app.route('/')
def index():
    return render_template('index.html', 
                         questions=mock_questions,
                         members=mock_members,
                         tags=mock_tags,
                         user={'is_authenticated': True, 'username': 'Dr. Pepper'})

@app.route('/hot')
def hot_questions():
    return render_template('index.html', 
                         questions=mock_questions,
                         members=mock_members,
                         tags=mock_tags,
                         user={'is_authenticated': True, 'username': 'Dr. Pepper'})

@app.route('/question/<int:question_id>')
def question(question_id):
    question_data = next((q for q in mock_questions if q['id'] == question_id), None)
    if not question_data:
        return "Question not found", 404
    
    question_answers = [a for a in mock_answers if a['question_id'] == question_id]
    
    return render_template('question.html',
                         question=question_data,
                         answers=question_answers,
                         members=mock_members,
                         tags=mock_tags,
                         user={'is_authenticated': False})

@app.route('/ask')
def ask_question():
    return render_template('ask.html',
                         members=mock_members,
                         tags=mock_tags,
                         user={'is_authenticated': False})

@app.route('/login')
def login():
    login = request.args.get("login")
    password = request.args.get("password")
    
    if login and password:
        if password != "123":
            flash("Invalid password! Try '123'.")
            return redirect(url_for('login'))
        else:
            return redirect(url_for('index'))
    
    return render_template('login.html',
                         members=mock_members,
                         tags=mock_tags,
                         user={'is_authenticated': False})

@app.route('/signup')
def signup():
    login = request.args.get("login")
    email = request.args.get("email")
    nickname = request.args.get("nickname")
    password = request.args.get("password")
    repeat_password = request.args.get("repeat_password")
    
    if any([login, email, nickname, password, repeat_password]):
        if email == "example@mail.ru":
            flash("Sorry, this email address already registered!")
            return render_template('signup.html',
                                members=mock_members,
                                tags=mock_tags,
                                user={'is_authenticated': False})
        else:
            return redirect(url_for('index'))
    
    return render_template('signup.html',
                         members=mock_members,
                         tags=mock_tags,
                         user={'is_authenticated': False})