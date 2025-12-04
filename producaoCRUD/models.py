from db import db
from flask_login import UserMixin

# ---------------------
# MODELO DOS USUARIOS
# ---------------------
class Usuarios(UserMixin, db.Model):
    __tablename__ = 'usuarios_db'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(50), unique=True, nullable=False)
    nome = db.Column(db.String(50), nullable=False)
    password = db.Column(db.String(255), nullable=False)

    # Relação: 1 usuário -> vários diretórios
    diretorios = db.relationship('Diretorios', backref='usuario', lazy=True, cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<Usuario {self.nome}>"


# ---------------------
# MODELO DOS DIRETORIOS
# ---------------------
class Diretorios(db.Model):
    __tablename__ = 'diretorios_db'

    id = db.Column(db.Integer, primary_key=True)  
    nome = db.Column(db.String(40), nullable=False)
    boxes = db.relationship("Boxes", backref="diretorio", cascade="all, delete", lazy=True)

    # FK: cada diretório pertence a um usuário
    user_id = db.Column(db.Integer, db.ForeignKey('usuarios_db.id'), nullable=False)


# ---------------------
# MODELO DAS BOX
# ---------------------
class Boxes(db.Model):
    __tablename__ = 'boxes_db'

    box_id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    password = db.Column(db.String(255), nullable=False)  # senha que abre a box
    diretorio_id = db.Column(db.Integer, db.ForeignKey('diretorios_db.id'), nullable=False)
    # relação: uma box tem várias senhas guardadas
    senhas = db.relationship("SenhasGuardadas", backref="box", cascade="all, delete", lazy=True)

# ---------------------
# MODELO DAS SENHAS
# ---------------------
class SenhasGuardadas(db.Model):
    __tablename__ = 'senhas_guardadas_db'

    senha_id = db.Column(db.Integer, primary_key=True)
    titulo = db.Column(db.String(100), nullable=False)  # ex: "Gmail", "Facebook"
    senha_salva = db.Column(db.String(255), nullable=False)  # senha criptografada
    box_id = db.Column(db.Integer, db.ForeignKey('boxes_db.box_id'), nullable=False)


