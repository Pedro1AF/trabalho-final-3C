from flask import Flask, render_template, request, url_for, redirect, flash
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from db import db
from models import Usuarios, Diretorios, Boxes, SenhasGuardadas

app = Flask(__name__)
app.secret_key = 'dev'

# Config DB
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///bancodados.db"
db.init_app(app)

lm = LoginManager(app)
lm.login_view = "login"

@lm.user_loader
def load_user(id):
    return Usuarios.query.get(int(id))


# -----------------------------
# CRIAR CONTA
# -----------------------------
@app.route('/criar_conta', methods=['GET', 'POST'])
def criar_conta():
    #if current_user.id != 1:
     #   return redirect("/pagina_principal")
    if request.method == 'GET':
        return render_template('criar.html')
    
    if request.method == 'POST':
        email = request.form['email']
        senha = request.form['password']
        nome = request.form['nome']

        novo_user = Usuarios(email=email, nome=nome, password=senha)
        db.session.add(novo_user)
        db.session.commit()
    return redirect(url_for('index'))


# -----------------------------
# LOGIN
# -----------------------------
@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template('entrada.html')
    
    email = request.form['email']
    senha = request.form['password']

    usuario = Usuarios.query.filter_by(email=email).first()

    if usuario and usuario.password == senha:
        login_user(usuario)
        return redirect(url_for('index'))

   
    return redirect(url_for('login'))


# -----------------------------
# ADMIN
# -----------------------------
@app.route('/admin', methods=['GET', 'POST'])
@login_required
def admin():
    if current_user.id != 1:
        flash("Você não tem permissão.")
        return redirect(url_for('index'))

    if request.method == 'GET':
        diretorios_lista = Diretorios.query.all()
        return render_template('admin.html', diretorios_lista=diretorios_lista)

    # POST
    nome = request.form['nome']
    email = request.form['email']
    senha = request.form['senha']

    novo_user = Usuarios(nome=nome, email=email, password=senha)
    db.session.add(novo_user)
    db.session.commit()

    return redirect(url_for('admin'))


# -----------------------------
# PAGINA PRINCIPAL
# -----------------------------
@app.route('/pagina_principal', methods=['GET', 'POST'])
@login_required
def index():

    if request.method == 'GET':
        diretorios = Diretorios.query.filter_by(user_id=current_user.id).all()
        return render_template('index.html', diretorios_lista=diretorios)

    if request.method == 'POST':
        #criação do diretorio
        nome = request.form['nome']
        novo_dir = Diretorios(nome=nome, user_id=current_user.id)
        db.session.add(novo_dir)
        db.session.commit()
        #fim da criação do diretorio


    return redirect(url_for('index'))


# -----------------------------
# DIRETÓRIO INDIVIDUAL
# -----------------------------
@app.route('/diretorio/<int:id>', methods=['GET'])
@login_required
def diretorio(id):

    # Verifica se o diretório existe
    diretorio = Diretorios.query.get_or_404(id)

    # Verifica se pertence ao usuário
    if diretorio.user_id != current_user.id:
        flash("Você não tem permissão para acessar este diretório.")
        return redirect(url_for('index'))

    # Puxa as boxes do diretório
    boxes = Boxes.query.filter_by(diretorio_id=id).all()

    # Renderiza página do diretório com boxes
    return render_template(
        'diretorio.html',
        diretorio=diretorio,
        boxes=boxes
    )



# ----------------
# CRIAR BOX
# ----------------

@app.route('/criar_box/<int:id>', methods=['POST'])
@login_required
def criar_box(id):
    diretorio = Diretorios.query.get_or_404(id)

    # Segurança
    if diretorio.user_id != current_user.id:
        flash("Você não tem permissão para criar boxes neste diretório.")
        return redirect(url_for('index'))

    nome = request.form.get("boxName")
    senha = request.form.get("boxPassword")
    senha_salva = request.form.get("savedPassword")

    if not nome or not senha or not senha_salva:
        flash("Preencha todos os campos!")
        return redirect(url_for('diretorio', id=id))

    # Criar a BOX
    nova_box = Boxes(
        nome=nome,
        password=senha,
        diretorio_id=id
    )

    db.session.add(nova_box)
    db.session.commit()

    # Criar a senha dentro da BOX
    nova_senha = SenhasGuardadas(
        titulo="Senha salva",       # Se quiser adicionar um título
        senha_salva=senha_salva,
        box_id=nova_box.box_id
    )

    db.session.add(nova_senha)
    db.session.commit()

    flash("Box criada com sucesso!")
    return redirect(url_for('diretorio', id=id))




@app.route('/abrir_box/<int:id>')
@login_required
def abrir_box(id):
    box = Boxes.query.get_or_404(id)
    diretorio = Diretorios.query.get_or_404(box.diretorio_id)

    # garante que o usuário só acessa seu diretório
    if diretorio.user_id != current_user.id:
        flash("Você não tem permissão para acessar esta box.")
        return redirect(url_for('index'))

    senha_digitada = request.args.get("senha")

    if senha_digitada != box.password:
        flash("Senha da box incorreta!")
        return redirect(url_for('diretorio', id=diretorio.id))

    # pega a senha salva dentro da box
    senha_salva = SenhasGuardadas.query.filter_by(box_id=box.box_id).first()

    return render_template(
        "box.html",
        box=box,
        senha_salva=senha_salva,
        diretorio=diretorio
    )


@app.route('/diretorio/<int:dir_id>/box/<int:box_id>', methods=['GET'])
@login_required
def pagina_box(dir_id, box_id):

    diretorio = Diretorios.query.get_or_404(dir_id)

    if diretorio.user_id != current_user.id:
        flash("Sem permissão para acessar este diretório.")
        return redirect(url_for('index'))

    box = Boxes.query.get_or_404(box_id)

    # Carrega senhas associadas à box
    senhas = SenhasGuardadas.query.filter_by(box_id=box_id).all()

    return render_template(
        'box.html',
        diretorio=diretorio,
        box=box,
        senhas=senhas
    )


if __name__ == '__main__':
    with app.app_context():
      db.create_all()
    app.run(debug=True)
