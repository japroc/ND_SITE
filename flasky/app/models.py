from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from flask import current_app
from flask_login import UserMixin, AnonymousUserMixin
from . import db, login_manager


class Permission:
    FOLLOW = 1
    COMMENT = 2
    WRITE = 4
    MODERATE = 8
    ADMIN = 16


class Role(db.Model):
    __tablename__ = 'roles'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True)
    default = db.Column(db.Boolean, default=False, index=True)
    permissions = db.Column(db.Integer)
    users = db.relationship('User', backref='role', lazy='dynamic')

    def __init__(self, **kwargs):
        super(Role, self).__init__(**kwargs)
        if self.permissions is None:
            self.permissions = 0

    @staticmethod
    def insert_roles():
        roles = {
            'User': [Permission.FOLLOW, Permission.COMMENT, Permission.WRITE],
            'Moderator': [Permission.FOLLOW, Permission.COMMENT,
                          Permission.WRITE, Permission.MODERATE],
            'Administrator': [Permission.FOLLOW, Permission.COMMENT,
                              Permission.WRITE, Permission.MODERATE,
                              Permission.ADMIN],
        }
        default_role = 'User'
        for r in roles:
            role = Role.query.filter_by(name=r).first()
            if role is None:
                role = Role(name=r)
            role.reset_permissions()
            for perm in roles[r]:
                role.add_permission(perm)
            role.default = (role.name == default_role)
            db.session.add(role)
        db.session.commit()

    def add_permission(self, perm):
        if not self.has_permission(perm):
            self.permissions += perm

    def remove_permission(self, perm):
        if self.has_permission(perm):
            self.permissions -= perm

    def reset_permissions(self):
        self.permissions = 0

    def has_permission(self, perm):
        return self.permissions & perm == perm

    def __repr__(self):
        return '<Role %r>' % self.name



class Messages(db.Model):
    __tablename__ = 'messages'
    id = db.Column(db.Integer, primary_key=True,unique=True, index=True)
    to_id=db.Column(db.Integer,db.ForeignKey('users.id'))
    from_id=db.Column(db.Integer,db.ForeignKey('users.id'))
    content=db.Column(db.Text())
    created_at=db.Column(db.DateTime(), index=True, default=datetime.utcnow)
    check_ms=db.Column(db.Boolean,default=False)
    def get_id(self):
        return self.from_id,self.to_id

    def delete_mess(self):
        db.session.delete(self)
        db.session.commit()

class Chats(db.Model):
    __tablename__ = 'chats'
    fr_one_id=db.Column(db.Integer, db.ForeignKey('users.id'), primary_key=True)
    fr_two_id=db.Column(db.Integer, db.ForeignKey('users.id'),primary_key=True)
    def get_id(self):
        return self.fr_one_id,self.fr_two_id
    def delete_chat(self):
        db.session.delete(self)
        db.session.commit()
		
class User(UserMixin, db.Model):

    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(64), unique=True, index=True)
    username = db.Column(db.String(64), unique=True, index=True)
    language=db.Column(db.String(12),index=True,nullable=False)
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'))
    password_hash = db.Column(db.String(128))
    confirmed = db.Column(db.Boolean, default=False)
    name = db.Column(db.String(64))
    location = db.Column(db.String(64))
    about_me = db.Column(db.Text())
    member_since = db.Column(db.DateTime(), default=datetime.utcnow)
    last_seen = db.Column(db.DateTime(), default=datetime.utcnow)
    fr_one = db.relationship('Chats',
                               foreign_keys=[Chats.fr_one_id],
                               backref=db.backref('fr_one', lazy='joined'),
                               lazy='dynamic',
                               cascade='all, delete-orphan')
    fr_two = db.relationship('Chats',
                                foreign_keys=[Chats.fr_two_id],
                                backref=db.backref('fr_two', lazy='joined'),
                                lazy='dynamic',
                                cascade='all, delete-orphan')
    #freind_one = db.relationship('Chats',primaryjoin='')
    #freind_two = db.relationship('Chats', foreign_keys=[Chats.fr_tw])
    to_me = db.relationship('Messages',
                             foreign_keys=[Messages.to_id],
                             backref=db.backref('to_me', lazy='joined'),
                             lazy='dynamic',
                             cascade='all, delete-orphan')
    from_me = db.relationship('Messages',
                             foreign_keys=[Messages.from_id],
                             backref=db.backref('from_me', lazy='joined'),
                             lazy='dynamic',
                             cascade='all, delete-orphan')

    def __init__(self, **kwargs):
        super(User, self).__init__(**kwargs)
        if self.role is None:
            if self.email == 'sobolsb5@gmail.com':
                self.role = Role.query.filter_by(name='Administrator').first()
            if self.role is None:
                self.role = Role.query.filter_by(default=True).first()

    @property
    def password(self):
        raise AttributeError('password is not a readable attribute')

    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password)

    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)

    def generate_confirmation_token(self, expiration=3600):
        s = Serializer(current_app.config['SECRET_KEY'], expiration)
        return s.dumps({'confirm': self.id}).decode('utf-8')

    def confirm(self, token):
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token.encode('utf-8'))
        except:
            return False
        if data.get('confirm') != self.id:
            return False
        self.confirmed = True
        db.session.add(self)
        return True

    def generate_reset_token(self, expiration=3600):
        s = Serializer(current_app.config['SECRET_KEY'], expiration)
        return s.dumps({'reset': self.id}).decode('utf-8')

    @staticmethod
    def reset_password(token, new_password):
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token.encode('utf-8'))
        except:
            return False
        user = User.query.get(data.get('reset'))
        if user is None:
            return False
        user.password = new_password
        db.session.add(user)
        return True

    def generate_email_change_token(self, new_email, expiration=3600):
        s = Serializer(current_app.config['SECRET_KEY'], expiration)
        return s.dumps(
            {'change_email': self.id, 'new_email': new_email}).decode('utf-8')

    def change_email(self, token):
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token.encode('utf-8'))
        except:
            return False
        if data.get('change_email') != self.id:
            return False
        new_email = data.get('new_email')
        if new_email is None:
            return False
        if self.query.filter_by(email=new_email).first() is not None:
            return False
        self.email = new_email
        db.session.add(self)
        return True

    def can(self, perm):
        return self.role is not None and self.role.has_permission(perm)

    def is_administrator(self):
        return self.can(Permission.ADMIN)

    def ping(self):
        self.last_seen = datetime.utcnow()
        db.session.add(self)

    def __repr__(self):
        return '<User %r>' % self.username

    def get_name(self):
        return self.username

    def add_message(self,user,data):
        m=Messages(to_me=user,from_me=self,content=data)
        db.session.add(m)
        db.session.commit()

    def add_chats(self, user):
        if not self.check_chats(user):
            f = Chats(fr_one=self, fr_two=user)
            db.session.add(f)
            db.session.commit()

    def delete_chats(self, user):
        f = self.fr_two.filter_by(fr_two_id=user.id).first()
        if f:
            db.session.delete(f)
            db.session.commit()

    def delete_chats2(self, user):
        f = self.fr_one.filter_by(fr_one_id=user.id).first()
        if f:
            db.session.delete(f)
            db.session.commit()

    def check_chats(self, user):
        if user.id is None:
            return None
        f = Chats.query.filter_by(fr_two_id=user.id,fr_one_id=self.id).first()
        if f == None:
            return False
        return True

    def check_chats2(self, user):
        if user.id is None:
            return None
        f = Chats.query.filter_by(fr_one_id=user.id,fr_two_id=self.id).first()
        if f==None:
            return False
        return True

class AnonymousUser(AnonymousUserMixin):
    def can(self, permissions):
        return False

    def is_administrator(self):
        return False

login_manager.anonymous_user = AnonymousUser


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))





#class Messages(db.Model):
#    __tablename__ = 'messages'
#    id = db.Column(db.Integer, primary_key=True,unique=True, index=True)
#    to_id=db.Column(db.Integer,db.ForeignKey('users.id'))
#    from_id=db.Column(db.Integer,db.ForeignKey('users.id'))
#    content=db.Column(db.Text())
#    created_at=db.Column(db.DateTime(), default=datetime.utcnow)






