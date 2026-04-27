from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import random
import os

app = Flask(__name__)
app.secret_key = 'english_tech_journey_secret_2024'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///english_journey.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# ─────────────────────────────────────────────
#  MODELS
# ─────────────────────────────────────────────

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    xp = db.Column(db.Integer, default=0)
    level = db.Column(db.Integer, default=1)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    lessons = db.relationship('LessonProgress', backref='user', lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def get_level_title(self):
        titles = {1: 'Rookie Dev', 2: 'Junior Dev', 3: 'Mid-Level Dev',
                  4: 'Senior Dev', 5: 'Tech Lead', 6: 'CTO'}
        return titles.get(self.level, 'Legend')


class LessonProgress(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    module_id = db.Column(db.Integer, nullable=False)
    lesson_id = db.Column(db.Integer, nullable=False)
    completed = db.Column(db.Boolean, default=False)
    completed_at = db.Column(db.DateTime)
    xp_earned = db.Column(db.Integer, default=0)
    __table_args__ = (db.UniqueConstraint('user_id', 'module_id', 'lesson_id'),)


# ─────────────────────────────────────────────
#  COURSE CONTENT
# ─────────────────────────────────────────────

MODULES = [
    {
        'id': 1,
        'name': 'Foundation',
        'icon': '🌱',
        'color': '#00ff9f',
        'description': 'Build your English base from the ground up',
        'lessons': [
            {'id': 1, 'title': 'Greetings & Small Talk', 'xp': 50,
             'content': [
                 {'phrase': 'How are you holding up?', 'translation': 'Como você está aguentando?', 'context': 'Pergunta casual sobre bem-estar'},
                 {'phrase': "I'm swamped with work right now.", 'translation': 'Estou sobrecarregado de trabalho agora.', 'context': 'Quando você está muito ocupado'},
                 {'phrase': "Let's touch base later.", 'translation': 'Vamos entrar em contato mais tarde.', 'context': 'Expressão de negócios comum'},
                 {'phrase': "What's the latest?", 'translation': 'O que há de novo?', 'context': 'Pedir novidades'},
                 {'phrase': "I'm on it!", 'translation': 'Estou nisso!', 'context': 'Confirmar que você está trabalhando em algo'},
             ]},
            {'id': 2, 'title': 'Email & Messaging', 'xp': 60,
             'content': [
                 {'phrase': 'Please find attached the report.', 'translation': 'Segue em anexo o relatório.', 'context': 'Enviar anexos por e-mail'},
                 {'phrase': 'I wanted to follow up on...', 'translation': 'Queria dar um retorno sobre...', 'context': 'Fazer follow-up profissional'},
                 {'phrase': 'Could you clarify the deadline?', 'translation': 'Você poderia esclarecer o prazo?', 'context': 'Pedir esclarecimento'},
                 {'phrase': 'Looking forward to hearing from you.', 'translation': 'Aguardo seu retorno.', 'context': 'Encerramento de e-mail'},
                 {'phrase': 'FYI — just keeping you in the loop.', 'translation': 'Para sua informação — apenas te mantendo atualizado.', 'context': 'Compartilhar informações'},
             ]},
            {'id': 3, 'title': 'Numbers & Time', 'xp': 40,
             'content': [
                 {'phrase': "We're behind schedule by two sprints.", 'translation': 'Estamos duas sprints atrasados.', 'context': 'Gestão de projetos ágeis'},
                 {'phrase': "The deadline is Q3.", 'translation': 'O prazo é no terceiro trimestre.', 'context': 'Referência a trimestres fiscais'},
                 {'phrase': "Let's sync at 3 PM sharp.", 'translation': 'Vamos sincronizar às 15h em ponto.', 'context': 'Marcar reuniões'},
                 {'phrase': "We hit the milestone ahead of time!", 'translation': 'Atingimos a meta antes do prazo!', 'context': 'Celebrar conquistas'},
             ]},
        ]
    },
    {
        'id': 2,
        'name': 'The Office Slangs',
        'icon': '🏢',
        'color': '#ff2d78',
        'description': 'Master workplace slang and informal English',
        'lessons': [
            {'id': 1, 'title': 'Meeting Room Slang', 'xp': 70,
             'content': [
                 {'phrase': 'Let\'s take this offline.', 'translation': 'Vamos discutir isso fora da reunião.', 'context': 'Adiar discussão para depois'},
                 {'phrase': "We need to move the needle.", 'translation': 'Precisamos fazer progresso real.', 'context': 'Expressar necessidade de avanço'},
                 {'phrase': "That\'s a low-hanging fruit.", 'translation': 'Isso é uma tarefa fácil de executar.', 'context': 'Tarefas simples com bom resultado'},
                 {'phrase': "Let\'s not boil the ocean here.", 'translation': 'Não precisamos complicar demais.', 'context': 'Manter foco no essencial'},
                 {'phrase': "We\'re on the same page, right?", 'translation': 'Estamos alinhados, certo?', 'context': 'Confirmar entendimento mútuo'},
             ]},
            {'id': 2, 'title': 'Startup Culture', 'xp': 80,
             'content': [
                 {'phrase': "Let\'s pivot the strategy.", 'translation': 'Vamos mudar a estratégia.', 'context': 'Mudar direção do projeto'},
                 {'phrase': "We need to scale this ASAP.", 'translation': 'Precisamos escalar isso o mais rápido possível.', 'context': 'Crescimento acelerado'},
                 {'phrase': "Ship it, we\'ll iterate later.", 'translation': 'Lança, a gente melhora depois.', 'context': 'Cultura de entregas rápidas'},
                 {'phrase': "This is a game-changer!", 'translation': 'Isso muda tudo!', 'context': 'Algo revolucionário'},
                 {'phrase': "Do more with less.", 'translation': 'Faça mais com menos.', 'context': 'Eficiência em startups'},
             ]},
            {'id': 3, 'title': 'Remote Work Phrases', 'xp': 65,
             'content': [
                 {'phrase': "Can everyone see my screen?", 'translation': 'Todo mundo consegue ver minha tela?', 'context': 'Compartilhamento de tela em calls'},
                 {'phrase': "You\'re on mute!", 'translation': 'Você está no mudo!', 'context': 'Situação clássica de videochamada'},
                 {'phrase': "I\'ll drop it in Slack.", 'translation': 'Vou mandar no Slack.', 'context': 'Compartilhar algo no chat'},
                 {'phrase': "Let\'s hop on a quick call.", 'translation': 'Vamos fazer uma ligação rápida.', 'context': 'Propor reunião breve'},
                 {'phrase': "Async is fine for this.", 'translation': 'Assíncrono é ok para isso.', 'context': 'Comunicação sem precisar de resposta imediata'},
             ]},
        ]
    },
    {
        'id': 3,
        'name': 'Tech Vocabulary',
        'icon': '⚡',
        'color': '#00d4ff',
        'description': 'Cloud, Python & BioHome tech terms',
        'lessons': [
            {'id': 1, 'title': 'Cloud Computing Basics', 'xp': 90,
             'content': [
                 {'phrase': 'We deployed the app to the cloud.', 'translation': 'Publicamos o app na nuvem.', 'context': 'Deploy em infraestrutura cloud'},
                 {'phrase': "The server is auto-scaling.", 'translation': 'O servidor está escalando automaticamente.', 'context': 'Escalabilidade automática'},
                 {'phrase': "We use serverless functions for this.", 'translation': 'Usamos funções serverless para isso.', 'context': 'Computação sem servidor'},
                 {'phrase': "The API endpoint returned a 404.", 'translation': 'O endpoint da API retornou um 404.', 'context': 'Depuração de APIs'},
                 {'phrase': "We\'re running containers on Kubernetes.", 'translation': 'Estamos rodando containers no Kubernetes.', 'context': 'Orquestração de containers'},
             ]},
            {'id': 2, 'title': 'Python & BioHome Stack', 'xp': 100,
             'content': [
                 {'phrase': "I\'m writing a script to automate that.", 'translation': 'Estou escrevendo um script para automatizar isso.', 'context': 'Automação com Python'},
                 {'phrase': "The data pipeline is running on schedule.", 'translation': 'O pipeline de dados está rodando conforme programado.', 'context': 'Pipelines de dados'},
                 {'phrase': "We parse the sensor data with Python.", 'translation': 'Processamos os dados do sensor com Python.', 'context': 'Contexto BioHome - IoT'},
                 {'phrase': "The carbon offset model is training.", 'translation': 'O modelo de compensação de carbono está treinando.', 'context': 'ML para sustentabilidade'},
                 {'phrase': "We track biodiversity metrics via API.", 'translation': 'Rastreamos métricas de biodiversidade via API.', 'context': 'BioHome - monitoramento ambiental'},
             ]},
            {'id': 3, 'title': 'DevOps & Agile', 'xp': 85,
             'content': [
                 {'phrase': "The CI/CD pipeline broke the build.", 'translation': 'O pipeline de CI/CD quebrou o build.', 'context': 'Integração e entrega contínua'},
                 {'phrase': "We need a hotfix for production.", 'translation': 'Precisamos de um hotfix em produção.', 'context': 'Correção urgente'},
                 {'phrase': "Let\'s do a code review first.", 'translation': 'Vamos fazer uma revisão de código primeiro.', 'context': 'Boas práticas de desenvolvimento'},
                 {'phrase': "The sprint retrospective is on Friday.", 'translation': 'A retrospectiva da sprint é na sexta.', 'context': 'Cerimônias do Scrum'},
                 {'phrase': "We\'re blocked on the infra side.", 'translation': 'Estamos bloqueados na parte de infra.', 'context': 'Bloqueios em projetos ágeis'},
             ]},
        ]
    },
    {
        'id': 4,
        'name': 'Vikings Leadership',
        'icon': '⚔️',
        'color': '#ff8c00',
        'description': 'Lead with confidence — English for leaders',
        'lessons': [
            {'id': 1, 'title': 'Giving Commands Confidently', 'xp': 75,
             'content': [
                 {'phrase': "I need this done by end of day.", 'translation': 'Preciso que isso seja feito até o final do dia.', 'context': 'Delegar tarefas com assertividade'},
                 {'phrase': "Take ownership of this task.", 'translation': 'Assuma a responsabilidade por essa tarefa.', 'context': 'Empoderar membros do time'},
                 {'phrase': "We don\'t retreat — we adapt.", 'translation': 'Não recuamos — nos adaptamos.', 'context': 'Liderança resiliente'},
                 {'phrase': "Rally the team — we have a deadline.", 'translation': 'Mobilize o time — temos um prazo.', 'context': 'Motivar equipe sob pressão'},
                 {'phrase': "Lead from the front.", 'translation': 'Lidere pelo exemplo.', 'context': 'Filosofia de liderança'},
             ]},
            {'id': 2, 'title': 'Negotiation & Influence', 'xp': 95,
             'content': [
                 {'phrase': "Let\'s find a middle ground.", 'translation': 'Vamos encontrar um ponto em comum.', 'context': 'Negociação colaborativa'},
                 {'phrase': "I see your point, but consider this...", 'translation': 'Entendo seu ponto, mas considere isso...', 'context': 'Discordar respeitosamente'},
                 {'phrase': "What\'s the ROI on that?", 'translation': 'Qual é o retorno sobre o investimento disso?', 'context': 'Justificar decisões de negócio'},
                 {'phrase': "I\'ll walk you through the strategy.", 'translation': 'Vou te guiar pela estratégia.', 'context': 'Apresentações executivas'},
                 {'phrase': "We need buy-in from all stakeholders.", 'translation': 'Precisamos do apoio de todos os envolvidos.', 'context': 'Gestão de partes interessadas'},
             ]},
            {'id': 3, 'title': 'Public Speaking Power', 'xp': 110,
             'content': [
                 {'phrase': "Let me paint you a picture.", 'translation': 'Deixa eu te mostrar a visão.', 'context': 'Abertura de apresentação'},
                 {'phrase': "The data speaks for itself.", 'translation': 'Os dados falam por si mesmos.', 'context': 'Argumentação baseada em dados'},
                 {'phrase': "To sum it all up...", 'translation': 'Para resumir tudo...', 'context': 'Conclusão de apresentação'},
                 {'phrase': "Any questions so far?", 'translation': 'Alguma dúvida até aqui?', 'context': 'Engajar a audiência'},
                 {'phrase': "The floor is open for discussion.", 'translation': 'A palavra está aberta para discussão.', 'context': 'Abrir para perguntas'},
             ]},
        ]
    },
    {
        'id': 5,
        'name': 'Career Master',
        'icon': '🚀',
        'color': '#bf00ff',
        'description': 'Land your dream job in the global tech scene',
        'lessons': [
            {'id': 1, 'title': 'LinkedIn & Personal Branding', 'xp': 80,
             'content': [
                 {'phrase': "Passionate about sustainability and tech.", 'translation': 'Apaixonado por sustentabilidade e tecnologia.', 'context': 'Headline do LinkedIn'},
                 {'phrase': "Open to global remote opportunities.", 'translation': 'Aberto a oportunidades remotas globais.', 'context': 'Sinalizar disponibilidade'},
                 {'phrase': "I specialize in Python for environmental data.", 'translation': 'Sou especialista em Python para dados ambientais.', 'context': 'Nicho de especialização'},
                 {'phrase': "Let\'s connect and build together.", 'translation': 'Vamos nos conectar e construir juntos.', 'context': 'Call to action no LinkedIn'},
                 {'phrase': "Check out my latest project on GitHub.", 'translation': 'Confira meu projeto mais recente no GitHub.', 'context': 'Portfólio técnico'},
             ]},
            {'id': 2, 'title': 'Job Interview Mastery', 'xp': 120,
             'content': [
                 {'phrase': "Tell me about yourself.", 'translation': 'Fale sobre você.', 'context': 'Pergunta clássica de entrevista — prepare 90 segundos'},
                 {'phrase': "I\'m a problem-solver at heart.", 'translation': 'Sou um solucionador de problemas por essência.', 'context': 'Descrever sua mentalidade'},
                 {'phrase': "In my last role, I increased efficiency by 30%.", 'translation': 'No meu último cargo, aumentei a eficiência em 30%.', 'context': 'Resposta com métrica (método STAR)'},
                 {'phrase': "I thrive in collaborative environments.", 'translation': 'Me destaco em ambientes colaborativos.', 'context': 'Trabalho em equipe'},
                 {'phrase': "My greatest weakness is perfectionism.", 'translation': 'Meu maior ponto de melhoria é o perfeccionismo.', 'context': 'A resposta clássica — use com moderação!'},
             ]},
            {'id': 3, 'title': 'Salary & Benefits Talk', 'xp': 100,
             'content': [
                 {'phrase': "My expected compensation is...", 'translation': 'Minha expectativa salarial é...', 'context': 'Negociar salário com profissionalismo'},
                 {'phrase': "Is there flexibility on the base salary?", 'translation': 'Há flexibilidade no salário base?', 'context': 'Abrir negociação'},
                 {'phrase': "I\'m also considering other offers.", 'translation': 'Estou também avaliando outras propostas.', 'context': 'Criar urgência sem agressividade'},
                 {'phrase': "What does the benefits package include?", 'translation': 'O que inclui o pacote de benefícios?', 'context': 'Perguntar sobre benefícios'},
                 {'phrase': "I\'d like some time to consider the offer.", 'translation': 'Gostaria de um tempo para avaliar a proposta.', 'context': 'Não aceitar imediatamente'},
             ]},
        ]
    }
]

BROOKLYN_NINE_NINE_PHRASES = [
    {"phrase": "Cool, cool, cool, cool, cool — no doubt, no doubt.", "character": "Jake Peralta", "context": "Quando você concorda nervosamente com tudo"},
    {"phrase": "Title of your sex tape.", "character": "Jake Peralta", "context": "Resposta irônica clássica do Jake — use com cuidado no trabalho 😂"},
    {"phrase": "I have a brown belt in saying 'I don't know.'", "character": "Rosa Diaz", "context": "Ser honesto sobre limitações"},
    {"phrase": "Every time someone steps up and shows they can do more, I want to make sure they feel seen.", "character": "Raymond Holt", "context": "Reconhecer esforço da equipe"},
    {"phrase": "You are smart, capable people who are going to figure this out.", "character": "Raymond Holt", "context": "Motivar a equipe"},
    {"phrase": "I want to get a good look at the full picture before making a decision.", "character": "Amy Santiago", "context": "Análise antes de agir"},
    {"phrase": "Noice. Smort.", "character": "Jake Peralta", "context": "Elogiar algo de forma casual"},
    {"phrase": "I'm not here to make friends. I'm here to do my job and eat snacks.", "character": "Gina Linetti", "context": "Foco total nas tarefas"},
    {"phrase": "I'm the human form of the 100 emoji.", "character": "Gina Linetti", "context": "Expressar confiança"},
    {"phrase": "Sir, I solve problems. That's what I do.", "character": "Charles Boyle", "context": "Assertividade profissional"},
    {"phrase": "I was never one for apologies — but I'm learning.", "character": "Rosa Diaz", "context": "Crescimento pessoal e humildade"},
    {"phrase": "The English language cannot fully capture the depth and complexity of my thoughts.", "character": "Raymond Holt", "context": "Humor ao falar sobre idiomas"},
]

CROSSFIT_EXERCISES = [
    {"name": "Burpees", "description": "Drop to the floor, do a push-up, jump back up with hands overhead", "emoji": "💪"},
    {"name": "Box Jumps", "description": "Explosive jump onto a box or platform, land softly", "emoji": "📦"},
    {"name": "Wall Balls", "description": "Squat deep, then throw a medicine ball to a 10-foot target", "emoji": "🏀"},
    {"name": "Double Unders", "description": "Jump rope passes under feet twice per jump", "emoji": "🪢"},
    {"name": "Thrusters", "description": "Front squat into an overhead press in one fluid movement", "emoji": "🏋️"},
    {"name": "Handstand Push-ups", "description": "Kick up to a wall handstand and do strict push-ups", "emoji": "🤸"},
    {"name": "Muscle-ups", "description": "From dead hang, pull yourself up and over the rings", "emoji": "💫"},
    {"name": "Rowing Machine", "description": "Drive with your legs, lean back, then pull to your chest", "emoji": "🚣"},
    {"name": "Kettlebell Swings", "description": "Hip-hinge power swing, bell to eye level", "emoji": "⚙️"},
    {"name": "Ring Dips", "description": "Full range dips on gymnastics rings for chest and triceps", "emoji": "⭕"},
]

# ─────────────────────────────────────────────
#  HELPER FUNCTIONS
# ─────────────────────────────────────────────

def get_user_progress(user_id):
    progress = LessonProgress.query.filter_by(user_id=user_id, completed=True).all()
    completed = {(p.module_id, p.lesson_id) for p in progress}
    total_lessons = sum(len(m['lessons']) for m in MODULES)
    return completed, total_lessons

def add_xp(user, xp_amount, module_id, lesson_id):
    existing = LessonProgress.query.filter_by(
        user_id=user.id, module_id=module_id, lesson_id=lesson_id).first()
    if existing and existing.completed:
        return False
    if not existing:
        existing = LessonProgress(user_id=user.id, module_id=module_id, lesson_id=lesson_id)
        db.session.add(existing)
    existing.completed = True
    existing.completed_at = datetime.utcnow()
    existing.xp_earned = xp_amount
    user.xp += xp_amount
    user.level = min(6, 1 + user.xp // 200)
    db.session.commit()
    return True

# ─────────────────────────────────────────────
#  ROUTES — AUTH
# ─────────────────────────────────────────────

@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username'].strip()
        email = request.form['email'].strip()
        password = request.form['password']
        if User.query.filter_by(username=username).first():
            return render_template('register.html', error='Nome de usuário já existe.')
        if User.query.filter_by(email=email).first():
            return render_template('register.html', error='E-mail já cadastrado.')
        user = User(username=username, email=email)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        session['user_id'] = user.id
        return redirect(url_for('dashboard'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username'].strip()
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            session['user_id'] = user.id
            return redirect(url_for('dashboard'))
        return render_template('login.html', error='Usuário ou senha incorretos.')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect(url_for('index'))

# ─────────────────────────────────────────────
#  ROUTES — MAIN APP
# ─────────────────────────────────────────────

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    user = User.query.get(session['user_id'])
    completed, total = get_user_progress(user.id)
    progress_pct = int((len(completed) / total) * 100) if total else 0
    return render_template('dashboard.html', user=user, modules=MODULES,
                           completed=completed, progress_pct=progress_pct, total_lessons=total)

@app.route('/module/<int:module_id>')
def module(module_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    user = User.query.get(session['user_id'])
    mod = next((m for m in MODULES if m['id'] == module_id), None)
    if not mod:
        return redirect(url_for('dashboard'))
    completed, _ = get_user_progress(user.id)
    return render_template('module.html', user=user, module=mod, completed=completed)

@app.route('/lesson/<int:module_id>/<int:lesson_id>')
def lesson(module_id, lesson_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    user = User.query.get(session['user_id'])
    mod = next((m for m in MODULES if m['id'] == module_id), None)
    if not mod:
        return redirect(url_for('dashboard'))
    les = next((l for l in mod['lessons'] if l['id'] == lesson_id), None)
    if not les:
        return redirect(url_for('module', module_id=module_id))
    completed, _ = get_user_progress(user.id)
    already_done = (module_id, lesson_id) in completed
    return render_template('lesson.html', user=user, module=mod, lesson=les, already_done=already_done)

@app.route('/complete_lesson', methods=['POST'])
def complete_lesson():
    if 'user_id' not in session:
        return jsonify({'error': 'not logged in'}), 401
    data = request.get_json()
    user = User.query.get(session['user_id'])
    mod = next((m for m in MODULES if m['id'] == data['module_id']), None)
    les = next((l for l in mod['lessons'] if l['id'] == data['lesson_id']), None) if mod else None
    if not les:
        return jsonify({'error': 'not found'}), 404
    gained = add_xp(user, les['xp'], data['module_id'], data['lesson_id'])
    return jsonify({'xp': user.xp, 'level': user.level, 'gained': gained,
                    'xp_earned': les['xp'] if gained else 0,
                    'level_title': user.get_level_title()})

@app.route('/shadowing')
def shadowing():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    user = User.query.get(session['user_id'])
    phrase = random.choice(BROOKLYN_NINE_NINE_PHRASES)
    return render_template('shadowing.html', user=user, phrase=phrase,
                           all_phrases=BROOKLYN_NINE_NINE_PHRASES)

@app.route('/api/random_phrase')
def random_phrase():
    return jsonify(random.choice(BROOKLYN_NINE_NINE_PHRASES))

@app.route('/crossfit')
def crossfit():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    user = User.query.get(session['user_id'])
    exercise = random.choice(CROSSFIT_EXERCISES)
    return render_template('crossfit.html', user=user, exercise=exercise)

@app.route('/api/random_exercise')
def random_exercise():
    return jsonify(random.choice(CROSSFIT_EXERCISES))

@app.route('/profile')
def profile():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    user = User.query.get(session['user_id'])
    completed, total = get_user_progress(user.id)
    lessons_detail = LessonProgress.query.filter_by(user_id=user.id, completed=True)\
        .order_by(LessonProgress.completed_at.desc()).limit(10).all()
    next_level_xp = user.level * 200
    return render_template('profile.html', user=user, completed=completed,
                           total=total, lessons_detail=lessons_detail,
                           next_level_xp=next_level_xp)

# ─────────────────────────────────────────────
#  INIT
# ─────────────────────────────────────────────

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True, port=5000)