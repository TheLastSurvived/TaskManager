from flask import Flask, render_template, request, flash, redirect, session, url_for, abort
from flask_sqlalchemy import SQLAlchemy
from flask_ckeditor import CKEditor
from datetime import datetime
import uuid
from werkzeug.utils import secure_filename
import os


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///task_manager.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = 'A0Zr98j/3yX R~XHH!jmN]LWX/,?RT'
app.config['FLASK_ADMIN_SWATCH'] = 'cerulean'
app.config['UPLOAD_FOLDER'] = 'static/img'
ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg', 'gif'])

db = SQLAlchemy(app)
ckeditor = CKEditor(app)


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS


class User(db.Model):
    id = db.Column(db.Integer,primary_key=True)
    name = db.Column(db.String(100))
    surname = db.Column(db.String(100))
    characteristic = db.Column(db.Text)
    department = db.Column(db.String(100))
    position = db.Column(db.String(100))
    email = db.Column(db.String(100), unique=True)
    phone_number = db.Column(db.Integer)
    password = db.Column(db.String(100), unique=True)
    photo = db.Column(db.String(500))
    root = db.Column(db.Integer, default=0)
    date = db.Column(db.DateTime, default=datetime.now)
    task_id = db.relationship('Task', backref='user', lazy='dynamic')


    def __repr__(self):
        return 'User %r' % self.id 


class Task(db.Model):
    id = db.Column(db.Integer,primary_key=True)
    title = db.Column(db.String(500))
    description = db.Column(db.String(500))
    type_task = db.Column(db.String(500))
    date = db.Column(db.DateTime, default=datetime.now)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    def __repr__(self):
        return 'Task %r' % self.id 


@app.route('/', methods=['GET', 'POST'])
def index():
    if not 'name' in session:
        return redirect('/auth')

    users = User.query.all()
    if request.method == 'POST':
        try:
            name = request.form.get('name')
            surname = request.form.get('surname')
            characteristic = request.form.get('ckeditor') 
            departament = request.form.get('departament')
            position = request.form.get('job')
            email = request.form.get('email')
            phone = request.form.get('phone')
            password = request.form.get('password')
            file = request.files['photo']
            filename = ''
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], str(uuid.uuid4()) + filename))
            user = User(
                name=name, 
                surname=surname, 
                characteristic=characteristic, 
                department=departament,
                position=position,
                email=email,
                phone_number=phone,
                password = password,
                photo = filename 
                )
            db.session.add(user)
            db.session.commit()
            return redirect(url_for("index"))
        except:
            flash("Ошибка! Почта или пароль уже заняты!", category="bad")
            return redirect(url_for("index"))
    return render_template("index.html",users=users)


@app.route('/auth', methods=['GET', 'POST'])
def auth():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        user = User.query.filter_by(email=email,password=password).first()

        if not user:
            flash("Неправильная почта или пароль!", category="bad")
            return redirect(url_for("auth"))

        session['name'] = User.query.filter_by(email=email).first().email

        return redirect(url_for("index"))
            
    return render_template("signIn.html")


@app.route('/worker/<int:id>', methods=['GET', 'POST'])
def worker(id):

    if not 'name' in session:
        return redirect('/auth')

    user = User.query.get(id)
    if not user:
        abort(404)

    tasks = [task for task in user.task_id]

    count_task_success = 0
    task_success_procent = 0
    for item in tasks:
        if item.type_task=="Выполнена":
            count_task_success+=1

    count_task = len(tasks)

    if count_task!=0:
        task_success_procent = int(count_task_success / len(tasks) * 100)

    


    if request.method == 'POST':
        try:
            name = request.form.get('name')
            surname = request.form.get('surname')
            characteristic = request.form.get('ckeditor') 
            departament = request.form.get('departament')
            position = request.form.get('job')
            email = request.form.get('email')
            phone = request.form.get('phone')
            password = request.form.get('password')
            file = request.files['photo']

            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                photo_worker = str(uuid.uuid4()) + filename
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], photo_worker))
                user.photo = photo_worker

            user.name = name
            user.surname = surname
            user.characteristic = characteristic
            user.department = departament
            user.position = position
            user.email = email
            user.phone_number = phone
            user.password = password


            db.session.commit()
            return redirect(url_for("worker", id=id))
        except:
            flash("Ошибка! Почта или пароль уже заняты!", category="bad")
            return redirect(url_for("worker", id=id))
    return render_template("worker.html",user=user, task_success_procent=task_success_procent,count_task_success=count_task_success,count_task=count_task)


@app.route('/delete-worker/<int:id>')
def delete_worker(id):
    user = User.query.get(id)
    if user.root == 1:
        flash("Ошибка! Данный пользователь обладает правами администратора, его нельзя удалить!", category="bad")
        return redirect(url_for("index"))
    db.session.delete(user)
    db.session.commit()
    return redirect(url_for("index"))


@app.route('/add-task/<int:id_worker>', methods=['GET', 'POST'])
def add_task(id_worker):
    if request.method == 'POST':
        try:
        
            title = request.form.get('title')
            description = request.form.get('description')
            type_task = request.form['type_task']
            task = Task(title=title, type_task=type_task, user_id=id_worker, description=description)
            db.session.add(task)
            db.session.commit()
            return redirect(url_for("worker", id=id_worker))
        except:
            flash("Ошибка!", category="bad")
    return redirect(url_for("worker", id=id_worker))


@app.route('/delete-task/<int:id>/<int:id_worker>')
def delete_task(id,id_worker):
    task = Task.query.get(id)
    db.session.delete(task)
    db.session.commit()
    return redirect(url_for("worker", id=id_worker))


@app.route('/success-task/<int:id>/<int:id_worker>')
def success_task(id,id_worker):
    task = Task.query.get(id)
    task.type_task = 'Выполнена'
    db.session.commit()
    return redirect(url_for("worker", id=id_worker))



@app.context_processor
def inject_user():
    def get_user_name():
        if 'name' in session:
            return User.query.filter_by(email=session['name']).first()

    return dict(active_user=get_user_name())


@app.route('/logout')
def logout():
    session.pop('name', None)
    return redirect('/')


@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(403)
def page_not_found(e):
    return render_template('403.html'), 403


if __name__ == '__main__':
    app.run(debug=True)