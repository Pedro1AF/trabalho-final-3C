# ---- importaçao de todas as bibliotecas, files e classes
from flask import Flask, render_template, request, url_for, redirect, flash
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from db import db
from models import Usuarios, Diretorios, Boxes, SenhasGuardadas

# ---- config basica do flask e sqlalchemy respectivamente
app = Flask(__name__)
app.secret_key = 'dev'

# Config DB
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///bancodados.db"
db.init_app(app)

# ---- config para gerir o usuario logado
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
    # ---- este if somente permite o id utilizar a pagina
    if current_user.id != 1:
        return redirect("/pagina_principal")
    
    if request.method == 'GET':
        # ---- caso seja get apenas retornar a propria pagina
        return render_template('criar.html')
    
    if request.method == 'POST':
        # ---- caso seja post inputs sera puxado pelo atributo name
        email = request.form['email']
        senha = request.form['password']
        nome = request.form['nome']
        # ---- adicionando os inputs no database
        novo_user = Usuarios(email=email, nome=nome, password=senha)
        db.session.add(novo_user)
        db.session.commit()
    return redirect(url_for('index'))


# -----------------------------
# LOGIN
# -----------------------------
@app.route('/', methods=['GET', 'POST'])
def login():
    # --- metodo get apenas retorna mesma pagina
    if request.method == 'GET':
        return render_template('entrada.html')
    # ---- puxa os campos do html do login
    email = request.form['email']
    senha = request.form['password']
    usuario = Usuarios.query.filter_by(email=email).first()
    # ---- verifica se a senha condiz coma senha do email especifico do usuario via consulta no db
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
    # ---- apenas o usuario 1 tem acesso a esta rota
    if current_user.id != 1:
        flash("Você não tem permissão.")
        return redirect(url_for('index'))
     # ---- requisição get
    if request.method == 'GET':
        diretorios_lista = Diretorios.query.all()
        return render_template('admin.html', diretorios_lista=diretorios_lista)
     # ---- requisiçaõ post com criação de users
    if request.method == 'POST':
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
# --------------
# ROTA DE DELETE DOS DIRETORIOS
# --------------
@app.route('/delete/<int:id>')
def delete(id):

    diretorio = db.session.query(Diretorios).filter_by(id=id).first()
    db.session.delete(diretorio)
    db.session.commit()
    return redirect(url_for('index'))   

# -----------------------------
# DIRETÓRIO INDIVIDUAL
# -----------------------------
@app.route('/diretorio/<int:id>', methods=['GET', 'POST'])
@login_required
def diretorio(id):
     # Verifica se o diretório existe
    diretorio = Diretorios.query.get_or_404(id)
         # Puxa as boxes do diretório
    boxes = Boxes.query.filter_by(diretorio_id=id).all()

    if diretorio.user_id != current_user.id:
            flash("Você não tem permissão para acessar este diretório.")
            return redirect(url_for('index'))
    if request.method == 'GET':
         return render_template('diretorio.html', diretorio=diretorio, boxes=boxes)
         
    if request.method == 'POST':
        nome = request.form['boxName']
        senha = request.form['boxPassword']
        nova_box = Boxes(nome=nome, password=senha, diretorio_id=id)
        db.session.add(nova_box)
        db.session.commit()
    return redirect(url_for('diretorio', id=id))
    # Renderiza página do diretório com boxes
   

    # Criar a senha dentro da BOX
   # nova_senha = SenhasGuardadas(
   #     titulo="Senha salva",       # Se quiser adicionar um título
   #     senha_salva=senha_salva,
   #     box_id=nova_box.box_id
   # )

   # db.session.add(nova_senha)
   # db.session.commit()

    



# --------------
#  ABRIR BOX
# --------------
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

# ------------
#  ROTA ESPECIFICA DA BOX
# ------------
@app.route('/diretorio/<int:dir_id>/box/<int:box_id>', methods=['GET', 'POST'])
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
