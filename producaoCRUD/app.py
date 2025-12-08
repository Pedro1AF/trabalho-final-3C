# ---- importaçao de todas as bibliotecas, files e classes
from flask import Flask, render_template, request, url_for, redirect, flash
from flask_login import LoginManager, login_user, login_required, logout_user, current_user, UserMixin

# NOVO: Importações e Configuração do Firebase
import firebase_admin
from firebase_admin import credentials, db

if not firebase_admin._apps:
    SERVICE_ACCOUNT_FILE = 'projeto-final3c-firebase-adminsdk-fbsvc-34ab346f73.json'
    DATABASE_URL = 'https://projeto-final3c-default-rtdb.firebaseio.com/'

    cred = credentials.Certificate(SERVICE_ACCOUNT_FILE)
    firebase_admin.initialize_app(cred, {
        'databaseURL': DATABASE_URL
    })


# -----------------------------
# CLASSE SIMPLIFICADA PARA FLASK-LOGIN
# -----------------------------
class User(UserMixin):
    """
    Classe para integrar o Firebase com o Flask-Login.
    O 'id' é a chave única gerada pelo Firebase (string).
    """
    def __init__(self, fb_key, user_data):
        self.id = fb_key  
        self.email = user_data.get('email')
        self.nome = user_data.get('nome')
        # ATENÇÃO: Senha em texto puro armazenada
        self.password = user_data.get('password') 
        # Mantém o ID inteiro para a checagem de admin (ID 1)
        self.user_id_int = user_data.get('user_id_int', 0) 

    def get_id(self):
        return self.id

    # Método de verificação simples (texto puro)
    def check_password(self, password):
        return self.password == password

# -----------------------------
# FUNÇÕES DE BANCO DE DADOS (FIREBASE)
# -----------------------------

def get_users_ref():
    """Retorna a referência para o nó 'usuarios'."""
    return db.reference('usuarios')

def get_ref(path):
    """Retorna uma referência para um nó específico do Firebase."""
    return db.reference(path)

def get_next_user_id_int():
    """Gera um ID inteiro sequencial, usado apenas para manter a lógica de Admin (ID 1)."""
    counter_ref = db.reference('id_counter')
    current_count = counter_ref.get()
    
    if current_count is None:
        counter_ref.set(1)
        return 1
    
    new_count = current_count + 1
    counter_ref.set(new_count)
    return new_count

# ---- config basica do flask
app = Flask(__name__)
app.secret_key = 'dev'

# ---- config para gerir o usuario logado
lm = LoginManager(app)
lm.login_view = "login"

@lm.user_loader
def load_user(fb_key):
    # Busca no Firebase pela chave (ID)
    user_data = get_users_ref().child(fb_key).get()
    if user_data:
        return User(fb_key, user_data)
    return None


# -----------------------------
# LOGOUT
# -----------------------------
@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))


# -----------------------------
# CRIAR CONTA (Administrador cria novos usuários)
# -----------------------------
@app.route('/criar_conta', methods=['GET', 'POST'])
@login_required
def criar_conta():

    # Apenas admin (user_id_int == 1) acessa
    if current_user.user_id_int != 1:
        return redirect("/pagina_principal")

    # Buscar todos os usuários do Firebase
    usuarios = get_users_ref().get() or {}

    if request.method == 'GET':
        return render_template(
            'admin.html',
            usuarios=usuarios
        )

    if request.method == 'POST':
        email = request.form['email']
        senha = request.form['password']
        nome = request.form['nome']

        novo_user_data = {
            'email': email,
            'nome': nome,
            'password': senha,
            'user_id_int': get_next_user_id_int()
        }

        get_users_ref().push(novo_user_data)
        flash("Conta criada com sucesso!")

    return redirect(url_for('criar_conta'))


@app.route('/editar_usuario/<uid>', methods=['GET', 'POST'])
@login_required
def editar_usuario(uid):

    # apenas o admin pode editar qualquer usuário
    if current_user.user_id_int != 1:
        return redirect("/pagina_principal")

    user_ref = get_users_ref().child(uid)
    usuario = user_ref.get()

    if not usuario:
        flash("Usuário não encontrado.")
        return redirect("/pagina_principal")

    if request.method == 'GET':
        return render_template("editar_usuario.html", usuario=usuario, uid=uid)

    if request.method == 'POST':
        user_ref.update({
            "nome": request.form['nome'],
            "email": request.form['email'],
            "password": request.form['password']
        })

        flash("Usuário atualizado com sucesso!")
        return redirect(url_for('criar_conta'))

    

@app.route('/deletar_usuario/<uid>', methods=['POST'])
@login_required
def deletar_usuario(uid):
    if current_user.user_id_int != 1:
        return redirect("/pagina_principal")

    get_users_ref().child(uid).delete()
    flash("Usuário deletado.")
    
    return redirect(url_for('criar_conta'))



# -----------------------------
# LOGIN
# -----------------------------
@app.route('/', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    if request.method == 'GET':
        return render_template('entrada.html')
        
    email = request.form['email']
    senha = request.form['password']
    
    # Busca no Firebase pelo email.
    users_data = get_users_ref().order_by_child('email').equal_to(email).get()

    if users_data:
        # Pega a primeira (e única) chave/valor do resultado
        fb_key, user_data = list(users_data.items())[0]
        usuario = User(fb_key, user_data)
        
        # Verifica a senha em texto puro
        if usuario.check_password(senha):
            login_user(usuario)
            return redirect(url_for('index'))
    
    flash("Email ou senha incorretos.")
    return redirect(url_for('login'))


# -----------------------------
# ADMIN (Redirecionando para a criação de conta)
# -----------------------------
@app.route('/admin', methods=['GET'])
@login_required
def admin():
    # ---- apenas o usuario 1 tem acesso a esta rota
    if current_user.user_id_int != 1:
        flash("Você não tem permissão.")
        return redirect(url_for('index'))
        
    # Redireciona para a rota 'criar_conta', que usa o template 'admin.html'
    return redirect(url_for('criar_conta'))


# -----------------------------
# PAGINA PRINCIPAL
# -----------------------------
@app.route('/pagina_principal', methods=['GET', 'POST'])
@login_required
def index():
    diretorios_ref = get_ref('diretorios')

    if request.method == 'GET':
        # Busca por diretórios do usuário atual
        diretorios_data = diretorios_ref.order_by_child('user_id').equal_to(current_user.id).get() or {}
        
        # Converte para uma lista de objetos
        diretorios_lista = [{'id': key, **data} for key, data in diretorios_data.items()]
        
        return render_template('index.html', diretorios_lista=diretorios_lista)

    if request.method == 'POST':
        # Criação do diretório (FIREBASE)
        nome = request.form['nome']
        
        novo_dir_data = {
            'nome': nome,
            'user_id': current_user.id # A chave do Firebase é o ID do Flask-Login
        }
        
        diretorios_ref.push(novo_dir_data)
        flash(f"Diretório '{nome}' criado com sucesso.")

    return redirect(url_for('index'))
    
# --------------
# ROTA DE DELETE DOS DIRETORIOS
# --------------
@app.route('/delete/<string:id>') # ID agora é STRING (chave do Firebase)
@login_required
def delete(id):
    diretorio_ref = get_ref('diretorios').child(id)
    diretorio = diretorio_ref.get()
    
    if not diretorio or diretorio.get('user_id') != current_user.id:
        flash("Diretório não encontrado ou você não tem permissão.")
        return redirect(url_for('index'))

    # Excluir do Firebase
    diretorio_ref.delete()
    flash("Diretório excluído com sucesso.")

    return redirect(url_for('index'))

# -----------------------------
# DIRETÓRIO INDIVIDUAL
# -----------------------------
@app.route('/diretorio/<string:id>', methods=['GET', 'POST']) # ID agora é STRING
@login_required
def diretorio(id):
    # Verifica se o diretório existe e puxa dados
    diretorio_ref = get_ref('diretorios').child(id)
    diretorio_data = diretorio_ref.get()
    
    if not diretorio_data:
        flash("Diretório não encontrado.")
        return redirect(url_for('index'))
        
    diretorio_obj = {'id': id, **diretorio_data}
    
    if diretorio_obj.get('user_id') != current_user.id:
        flash("Você não tem permissão para acessar este diretório.")
        return redirect(url_for('index'))
    
    boxes_ref = get_ref('boxes')
    
    # Puxa as boxes do diretório atual
    boxes_data = boxes_ref.order_by_child('diretorio_id').equal_to(id).get() or {}
    boxes = [{'id': key, **data} for key, data in boxes_data.items()]

    if request.method == 'GET':
        return render_template('diretorio.html', diretorio=diretorio_obj, boxes=boxes)
        
    if request.method == 'POST':
        # Criação da BOX (FIREBASE)
        nome = request.form['boxName']
        senha = request.form['boxPassword'] # Senha da box em texto puro
        
        nova_box_data = {
            'nome': nome,
            'password': senha, 
            'diretorio_id': id
        }
        
        boxes_ref.push(nova_box_data)
        flash(f"Box '{nome}' criada com sucesso.")
        
    return redirect(url_for('diretorio', id=id))


# --------------
# ABRIR BOX
# --------------
@app.route('/abrir_box/<string:id>') # ID agora é STRING
@login_required
def abrir_box(id):
    box_ref = get_ref('boxes').child(id)
    box_data = box_ref.get()
    
    if not box_data:
        flash("Box não encontrada.")
        return redirect(url_for('index'))
        
    box = {'id': id, **box_data}
    diretorio_id = box.get('diretorio_id')

    diretorio_ref = get_ref('diretorios').child(diretorio_id)
    diretorio_data = diretorio_ref.get()
    diretorio = {'id': diretorio_id, **diretorio_data}

    if diretorio.get('user_id') != current_user.id:
        flash("Você não tem permissão para acessar esta box.")
        return redirect(url_for('index'))

    senha_digitada = request.args.get("senha")

    if senha_digitada != box.get('password'):
        flash("Senha da box incorreta!")
        return redirect(url_for('diretorio', id=diretorio.get('id')))

    # Redireciona para a rota 'pagina_box' que carrega o template e as senhas
    return redirect(url_for('pagina_box', dir_id=diretorio.get('id'), box_id=id))

# ------------
# ROTA ESPECIFICA DA BOX (Carrega o template e manipula a criação de senhas)
# ------------
@app.route('/diretorio/<string:dir_id>/box/<string:box_id>', methods=['GET', 'POST']) # IDs são STRINGS
@login_required
def pagina_box(dir_id, box_id):

    diretorio_ref = get_ref('diretorios').child(dir_id)
    diretorio_data = diretorio_ref.get()
    
    if not diretorio_data:
        flash("Diretório não encontrado.")
        return redirect(url_for('index'))
    
    diretorio = {'id': dir_id, **diretorio_data}
    
    if diretorio.get('user_id') != current_user.id:
        flash("Sem permissão para acessar este diretório.")
        return redirect(url_for('index'))

    box_ref = get_ref('boxes').child(box_id)
    box_data = box_ref.get()
    if not box_data:
        flash("Box não encontrada.")
        return redirect(url_for('diretorio', id=dir_id))
        
    box = {'id': box_id, **box_data}

    senhas_ref = get_ref('senhas_guardadas')
    
    if request.method == 'POST':
        titulo = request.form.get('titulo')
        senha_salva = request.form.get('senha_salva') 

        nova_senha_data = {
            'titulo': titulo,
            'senha_salva': senha_salva, # Senha salva em texto puro
            'box_id': box_id
        }
        
        senhas_ref.push(nova_senha_data)
        flash("Senha salva com sucesso.")
        return redirect(url_for('pagina_box', dir_id=dir_id, box_id=box_id))

    # GET request: Carrega e lista as senhas
    senhas_data = senhas_ref.order_by_child('box_id').equal_to(box_id).get() or {}
    senhas = [{'id': key, **data} for key, data in senhas_data.items()]
    
    return render_template(
        'box.html',
        diretorio=diretorio,
        box=box,
        senhas=senhas
    )


if __name__ == '__main__':
    with app.app_context():
        # Inicializa o contador de ID (usado apenas para manter a lógica do admin ID 1)
        counter_ref = db.reference('id_counter')
        if counter_ref.get() is None:
            counter_ref.set(0)
            
    app.run(debug=True)