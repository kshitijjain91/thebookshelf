from flask import Flask, render_template, session, url_for, redirect, request, flash, g, send_from_directory, current_app, send_file
from wtforms import Form, BooleanField, StringField, PasswordField, validators
from passlib.hash import sha256_crypt
from flask_login import LoginManager, login_user, logout_user, current_user, login_required
import pymysql
import os
from werkzeug.utils import secure_filename
from dbconnect import connection
import gc
from pagination import Pagination
from functools import wraps
import datetime
import calendar


app = Flask(__name__)

# for file uploads
UPLOAD_FOLDER = 'uploads/'
ALLOWED_EXTENSIONS = set(['txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'epub'])
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

@app.route('/', methods=['GET', 'POST'])
def homepage():
    return render_template("homepage.html")

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not 'logged_in' in session:
            flash('Please login to perform this action.')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/login/', methods=['GET', 'POST'])
def login():
    try:
        c, conn = connection()
        error = None

        if request.method == 'POST':

            #check email match
            data = c.execute("select * from users where email = (%s)", (request.form['email_username'], ))
            if int(data) <= 0:
                data = c.execute("select * from users where username = (%s)", (request.form['email_username'], ))
                if int(data) <= 0:
                    flash("This username or email address does not exist.")


            if int(data) > 0:
                data_row = c.fetchone()
                data = data_row[3]

                if sha256_crypt.verify(request.form['password'], data):
                    session['logged_in'] = True
                    session['username'] = data_row[2]
                    flash('You are now logged in ' + str(session['username']))
                    return redirect(url_for('homepage'))
                else:
                    flash('Invalid password, try again.')
        gc.collect()
        return render_template('login.html', error=error)
    except Exception as e:
        flash(str(e))
        return render_template('login.html', error=e)




@app.route('/logout/')
def logout():
    session.pop('logged_in', None)
    session.clear()
    flash('You have been logged out.')
    gc.collect()
    return redirect(url_for('homepage'))


# defining wtforms class for registration form
class RegistrationForm(Form):
    username = StringField('Username', [validators.Length(min=4, max=25)])
    email = StringField('Email Address', [validators.Length(min=6, max=35)])
    password = PasswordField('New Password', [
        validators.DataRequired(),
        validators.EqualTo('confirm', message='Passwords must match')
    ])
    confirm = PasswordField('Repeat Password')
    accept_tos = BooleanField('I accept the TOS', [validators.DataRequired()])


@app.route('/signup/', methods=['GET', 'POST'])
def signup():
    try:
        form = RegistrationForm(request.form)

        if request.method == 'POST' and form.validate():
            username = form.username.data
            email = form.email.data

            if username is None:
                flash("Please choose a username.")

            password = sha256_crypt.encrypt(str(form.password.data))
            c, conn = connection()

            x = c.execute("select * from users where username = (%s)", (username, ))

            if int(x) > 0:
                flash("Sorry! This username is already taken, please choose another one.")
                return render_template('signup.html', form=form)
            else:
                c.execute('''insert into users (email, username, password)
                    values (%s, %s, %s)''', (email, username, password))
                conn.commit()
                flash("Thanks for registering.")
                conn.close()
                gc.collect()
                session['logged_in'] = True
                session['username'] = username
                return redirect(url_for('homepage'))
        gc.collect()
        return render_template('signup.html', form=form)
    except Exception as e:
        return(str(e))


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def insert_book(username, book_name, author_name, description, book_type, book, super_category):
    # insert user_id, book_id into user-books table
    # insert book name, author, description, type, size and the file into books table
    try:
        c, conn = connection()

        if request.method == 'POST':
            # check if email matches username
            user_data = c.execute("select user_id from users where email = (%s)", (username, ))
            if int(user_data) <= 0:
                user_data = c.execute("select user_id from users where username = (%s)", (username, ))


            if int(user_data) > 0:
                # insert book into books
                user_id = c.fetchone()[0]
                # insert book
                c.execute('''insert into books (name, author, description, type, file, super_category)
                    values (%s, %s, %s, %s, %s, %s)''',
                    (book_name, author_name, description, book_type, book, super_category))
                book_data = c.execute("select last_insert_id();")
                book_id = c.fetchone()[0]
                #insert user_id and book_id
                c.execute("insert into user_books (user_id, book_id) values (%s, %s)", (user_id, book_id))
                conn.commit()
                conn.close()
                return('You have successfully uploaded the book.')
        gc.collect()
    except Exception as e:
        return(str(e))



@app.route('/upload_file/<username>/', methods=['GET', 'POST'])
def upload_file(username):
    if request.method == 'POST':
        # check if the post request has the file part
        if 'file' not in request.files:
            flash('No file')
            return redirect(request.url)
        file = request.files['file']
        # if user does not select file, browser also
        # submits an empty part without filename
        if file.filename == '':
            flash('No file selected.')
            return redirect(request.url)
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            app_base_path = os.path.join(current_app.root_path, app.config['UPLOAD_FOLDER'])
            file.save(os.path.join(app_base_path, filename))

            book = os.path.join(app_base_path, filename)
            book_name = request.form['book_name']
            author_name = request.form['author_name']
            description = request.form['description']
            book_type = filename.rsplit('.', 1)[1].lower()
            super_category = request.form.get('super_category', None)

            insert_status = insert_book(username, book_name, author_name, description, book_type, book, super_category)
            flash(insert_status)
            return redirect(url_for('user_bookshelf', username=username))
    return render_template("upload_file.html")


@app.route('/user_bookshelf/<username>/', methods = ['GET', 'POST'])
def user_bookshelf(username):
    try:
        c, conn = connection()

        user_data = c.execute("select user_id from users where email = (%s)", (username, ))
        if int(user_data) <= 0:
            user_data = c.execute("select user_id from users where username = (%s)", (username, ))

        user_id = c.fetchone()[0]
        c.execute('''select users.user_id, books.book_id, name, author, description
            from users, user_books, books
            where users.user_id=user_books.user_id and user_books.book_id=books.book_id
            and users.user_id=(%s);''', (user_id, ))
        user_book_list = c.fetchall()

        total = len(user_book_list)
        page = request.args.get('page', type=int, default=1)
        per_page = 6

        pagination = Pagination(total, per_page, page)

        return render_template('user_bookshelf.html', user_book_list=user_book_list,
            username=username, p = pagination)

    except Exception as e:
        flash(str(e))


@app.route('/browse_books/<category>/', methods = ['GET'])
def browsebooks(category='all'):
    try:

        page = request.args.get('page', type=int, default=1)
        per_page = 9
        c, conn = connection()


        if category == 'all':
            c.execute('''select a.book_id, a.name, a.author, a.description, a.file, a.user_id, a.username, num
                from
                (select b.book_id, name, author, description, file, u.user_id, u.username
                from users u, books b, user_books ub
                where b.book_id=ub.book_id and u.user_id = ub.user_id) as a
                left join nlikes on
                a.book_id=nlikes.book_id;''')


        if category == 'fiction':
            c.execute('''select a.book_id, a.name, a.author, a.description, a.file, a.user_id, a.username, num
                from
                (select b.book_id, name, author, description, file, u.user_id, u.username
                from users u, books b, user_books ub
                where b.book_id=ub.book_id and u.user_id = ub.user_id and b.super_category=(%s)) as a
                left join nlikes on
                a.book_id=nlikes.book_id''', ('Fiction', ))

        if category == 'non_fiction':
            c.execute('''select a.book_id, a.name, a.author, a.description, a.file, a.user_id, a.username, num
                from
                (select b.book_id, name, author, description, file, u.user_id, u.username
                from users u, books b, user_books ub
                where b.book_id=ub.book_id and u.user_id = ub.user_id and b.super_category=(%s)) as a
                left join nlikes on
                a.book_id=nlikes.book_id''', ('Non-Fiction', ))

        book_list = c.fetchall()
        total = len(book_list)


        pagination = Pagination(total, per_page, page)

        return render_template("browse_books.html", book_list=book_list, p = pagination, category=category)

    except Exception as e:
        flash(str(e))

@app.route('/userbookshelf/<other_user_id>/')
def other_user_shelf(other_user_id):
    # get all the books uploaded by other_user_id
    try:
        c, conn = connection()

        user_id = other_user_id
        c.execute('''select users.user_id, books.book_id, name, author, description, file, username
            from users, user_books, books
            where users.user_id=user_books.user_id and user_books.book_id=books.book_id
            and users.user_id=(%s);''', (user_id, ))
        user_book_list = c.fetchall()

        total = len(user_book_list)
        page = request.args.get('page', type=int, default=1)
        per_page = 6

        pagination = Pagination(total, per_page, page)

        return render_template("other_user.html", p=pagination,
            user_book_list=user_book_list, user_id=user_id)

    except Exception as e:
        flash(str(e))


def redirect_url():
    return request.referrer



@app.route('/add_to_list/<username>/<book_id>/', methods=['GET', 'POST'])
@login_required
def add_to_reading_list(book_id, username='default_user'):
    try:
        c, conn = connection()

        user_data = c.execute("select user_id from users where email = (%s)", (username, ))
        if int(user_data) <= 0:
            user_data = c.execute("select user_id from users where username = (%s)", (username, ))

        user_id = c.fetchone()[0]

        # insert into reading _list
        c.execute(''' insert into reading_list (user_id, book_id)
            values (%s, %s);''', (user_id, book_id))
        conn.commit()
        return redirect(redirect_url())

    except Exception as e:
        flash(str(e))

    finally:
        conn.close()

@app.route('/requestbook/', methods=['GET', 'POST'])
@login_required
def requestbook():
    book_name = request.args.get('book_name', default = "")
    author_name = request.args.get('author_name', default = "")
    description = request.args.get('description', default="")
    username = session['username']
    user_id = username_to_userid(username)

    try:
        c, conn = connection()
        c.execute(''' insert into requests
            (user_id, book_name, author_name, description)
            values (%s, %s, %s, %s);''',
            (user_id, book_name, author_name, description))
        conn.commit()
        flash("Your request will be notified to other users.")
        return redirect(redirect_url())
    except Exception as e:
        flash(e)




@app.route('/add_to_likes/<username>/<book_id>/', methods=['GET', 'POST'])
@login_required
def add_to_likes(book_id, username='default_user'):
    try:
        c, conn = connection()
        user_id = username_to_userid(username)

        # insert into likes table
        c.execute(''' insert into likes (user_id, book_id)
            values (%s, %s);''', (user_id, book_id))
        conn.commit()
        return redirect(redirect_url())

    except Exception as e:
        flash(str(e))

    finally:
        conn.close()

def username_to_userid(username):
    c, conn = connection()
    user_data = c.execute("select user_id from users where email = (%s)", (username, ))

    if int(user_data) <= 0:
        user_data = c.execute("select user_id from users where username = (%s)", (username, ))

    user_id = c.fetchone()[0]
    conn.close()
    return user_id



@app.route('/reading_list/<username>/')
def reading_list(username):
    try:
        user_id=username_to_userid(username)
        c, conn = connection()

        #fetch list of book ids added to the list
        reading_list = c.execute('''select distinct b.book_id, name, author, description, file,
            ub.user_id, u.username
            from users u, books b, user_books ub, reading_list rl
            where b.book_id = ub.book_id and
            u.user_id = ub.user_id and
            rl.user_id = (%s) and rl.book_id = b.book_id;''', (user_id, ))

        user_book_list = c.fetchall()

        total = len(user_book_list)
        page = request.args.get('page', type=int, default=1)
        per_page = 9

        pagination = Pagination(total, per_page, page)

        return render_template("reading_list.html", p=pagination,
            book_list = user_book_list, username=username)

    except Exception as e:
        flash(e)

@app.route('/uploads/', methods = ['GET', 'POST'])
def uploads():
    # file = os.path.basename(filename)
    filename = request.args.get('filename')
    if filename:
        file_name = os.path.basename(filename)
        return send_from_directory('uploads', filename=file_name)
    else:
        flash('no file found')


@app.route('/delete_book/<book_id>/', methods=['GET', 'POST'])
def delete_book(book_id):
    try:
        c, conn = connection()
        c.execute(''' delete from user_books where book_id=(%s);''', (int(book_id), ))
        #c.execute(''' delete from books where book_id = (%s);''', (int(book_id), ))
        conn.commit()
        return redirect(redirect_url())
    except Exception as e:
        flash(e)
    finally:
        conn.close()


@app.route('/edit_book/<book_id>/', methods=['GET', 'POST'])
def edit_book(book_id):

    # retrieve original book details to put in the form by default
    c,conn = connection()
    c.execute(''' select name, author, description from books where book_id=(%s);''', (int(book_id), ))
    book_data = c.fetchone()
    original_name = book_data[0]
    original_author = book_data[1]
    original_desc = book_data[2]

    if request.method == 'POST':
        book_name = request.form['book_name']
        author_name = request.form['author_name']
        description = request.form['description']
        super_category = request.form.get('super_category', None)
        try:
            c, conn = connection()
            c.execute(''' update books set name=(%s), author=(%s), description=(%s),
                super_category=(%s) where book_id=(%s);''',
                (book_name, author_name, description, super_category, book_id))
            conn.commit()
        except Exception as e:
            flash(str(e))
        finally:
            conn.close()

        return redirect(url_for('user_bookshelf', username=session['username']))
    return render_template("edit_book.html", book_id=book_id,
        original_name=original_name, original_author=original_author, original_desc=original_desc)


@app.route('/search/', methods=['GET', 'POST'])
def search():

    if True:
        search_string = request.args.get('search_string')

        if search_string is None:
            return redirect(redirect_url())
        try:
            c, conn = connection()
            # search by book or author
            ''' select a.book_id, a.name, a.author, a.description, a.file, a.user_id, a.username, num
                from
                (select b.book_id, name, author, description, file, u.user_id, u.username
                from users u, books b, user_books ub
                where b.book_id=ub.book_id and u.user_id = ub.user_id and
                (b.name like %s or b.author like %s or u.username like %s)) as a
                left join nlikes on
                a.book_id=nlikes.book_id'''

            b = c.execute('''select a.book_id, a.name, a.author, a.description, a.file, a.user_id, a.username, num
                from
                (select b.book_id, name, author, description, file, u.user_id, u.username
                from users u, books b, user_books ub
                where b.book_id=ub.book_id and u.user_id = ub.user_id and
                (b.name like %s or b.author like %s or u.username like %s)) as a
                left join nlikes on
                a.book_id=nlikes.book_id;''',
                ('%{0}%'.format(search_string), '%{0}%'.format(search_string),
                '%{0}%'.format(search_string)))

            book_list = c.fetchall()


            if int(b) == 0:
                flash("Sorry! There's no book, author or user by this name." )
                return redirect(redirect_url())

            else:
                total = len(book_list)
                per_page = 6
                page = request.args.get('page', type=int, default=1)
                pagination = Pagination(total, per_page, page)
                return render_template("browse_books.html", book_list=book_list,
                p = pagination, category='all', search_string = search_string)

        except Exception as e:
            flash(str(e))


@app.route('/notifications/<username>/', methods=['GET'])
def notifications(username):
    try:
        c, conn = connection()
        user_id = username_to_userid(username)
        r = c.execute(''' select username, book_name, author_name, description, year(ts), month(ts), r.user_id
            from users u, requests r
            where u.user_id=r.user_id and
            u.user_id != (%s);''', (user_id, ))

        all_requests = c.fetchall()
        if int(r) == 0:
            flash('There are no notifications.')
            return redirect(redirect_url())

        else:
            # months = [calendar.month_abbr[all_requests[x][4].month] for x in range(len(all_requests))]
            return render_template('notifications.html', all_requests=all_requests)
    except Exception as e:
        flash(e)




#random comment to test gitignore



















if __name__ == '__main__':
    app.secret_key = 'super_secret_key_1231wqdn'
    app.run(debug=True, port=5151)