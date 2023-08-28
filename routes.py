from app import app, login_manager, logger, mail
from flask import render_template, redirect, url_for, flash, jsonify, request
import sqlalchemy.exc
from sqlalchemy import or_
from flask_mail import Message
from forms import *
from models import *
from flask_login import login_user, login_required, current_user, logout_user
from constants import *
from collections import Counter
from typing import Literal
import dateutil.relativedelta
import uuid


@app.route('/')
@app.route('/home')
def index():
    return render_template('home.html', title='Home')


@app.route('/about')
def about():
    return render_template('about.html', title='About')


@app.route('/signup', methods=['GET', 'POST'])
def sign_up():
    form = SignUpForm()
    if form.validate_on_submit():
        email_code = str(uuid.uuid4())
        user = User(username=form.username.data, email=form.email.data, email_code=email_code)
        user.set_password(form.password.data)
        try:
            db.session.add(user)
            db.session.commit()
        except sqlalchemy.exc.IntegrityError as e:
            logger.warning(f'Failed to commit new user to database - {e}')
            db.session.rollback()
            flash('This username or email already exists')
        else:
            logger.info(f'Successfully committed new user id={user.id} to database')
            flash('You have been sent an email to validate your email address')
            message = Message('Validate Test',
                              [user.email])
            message.body = 'Email Validation'
            message.html = f'''Please click <a href="http://127.0.0.1:5000/verify_email/{user.id}/{email_code}">here</a>
                                or follow this url: http://127.0.0.1:5000/verify_email/{user.id}/{email_code}'''
            mail.send(message)
            login_user(user)
            return redirect(url_for('profile', user_id=user.id))
    return render_template('sign_up.html', form=form, title='Sign Up')


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and user.check_password(form.password.data):
            logger.info('Successfully authenticated user and password')
            login_user(user)
            logger.info(f'Successfully logged in user id={current_user.id}')
            return redirect(url_for('profile', user_id=user.id))
        else:
            logger.info('User or password authorisation failed')
            flash('Wrong username or password')
    return render_template('login.html', title='Login', form=form)


@app.route('/profile/<int:user_id>')
def profile(user_id):
    user = User.query.get(user_id)
    if user is not None:
        logger.info(f'Successfully found user id={user.id}... rendering user.html')
        all_tags = []
        for discussion in user.discussions.all():
            if discussion:
                tag_split = discussion.tags.split(',')
                for tag in tag_split:
                    if tag != '':
                        all_tags += [tag]
        counter = Counter(all_tags)
        return render_template('user.html', title=user.username, user=user, tag_counter=counter)
    logger.warning(f'Failed to find user id={user_id}... redirecting to /home')
    flash('This user does not exist')
    return redirect(url_for('index'))


@app.route('/discussions', methods=['GET', 'POST'])
def discussions():
    all_discussions = Discussion.query.all()
    form = NewDiscussionForm()
    search_form = SearchDiscussionsForm()
    if search_form.search_text.data is not None:
        if search_form.validate_on_submit():
            # Get all discussions where title or text are like the searched text
            all_discussions = Discussion.query.filter(or_(
                Discussion.text.ilike('%' + search_form.search_text.data + '%'),
                Discussion.title.ilike('%' + search_form.search_text.data + '%'))
            ).all()
            filter_tags = search_form.tag_filter_choices.data
            tags = [AVAILABLE_CHOICES[int(i) - 1][1] for i in filter_tags]
            tagged = set()
            # if user specified any tags
            if tags:
                # Find all discussions which contain atleast 1 of the filtered tags
                for discussion in all_discussions:
                    if discussion:
                        for tag in tags:
                            if tag in discussion.tags:
                                tagged.add(discussion)
                all_discussions = tagged
    elif form.validate_on_submit():
        str_tags = [AVAILABLE_CHOICES[int(i)-1][1] for i in form.assigned.data]
        new_tags = ','.join(str_tags)
        print(form.text.data)
        if current_user.is_authenticated:
            print(form.text.data)
            new_discussion = Discussion(title=form.title.data, text=form.text.data, poster_id=int(current_user.id), tags=new_tags)
            try:
                db.session.add(new_discussion)
                db.session.commit()
            except sqlalchemy.exc.IntegrityError as e:
                logger.warning(f'Failed to commit new discussion to database - {e}')
                db.session.rollback()
                flash('A discussion with this title already exists.')
                return render_template('discussions.html', discussions=all_discussions, title='Discussions', form=form, search_form=search_form)
            logger.info(f'Successfully committed new discussion id={new_discussion.id}... redirecting to discussion page')
            return redirect(url_for('discussion', discussion_id=int(new_discussion.id)))
        else:
            logger.warning('Current user not authenticated for posting new discussion')
            return redirect(url_for('login'))

    return render_template('discussions.html', discussions=all_discussions, title='Discussions', form=form, search_form=search_form)


@app.route('/discussions/<int:discussion_id>', methods=['GET', 'POST'])
def discussion(discussion_id):
    get_discussion = Discussion.query.get(discussion_id)
    if get_discussion:
        get_discussion.views += 1
        db.session.commit()

        form = NewCommentForm()
        if form.validate_on_submit() and not form.text.data.isspace():
            new_comment = Comment(text=form.text.data, poster_id=int(current_user.id), discussion_id=get_discussion.id)
            try:
                db.session.add(new_comment)
                db.session.commit()
            except sqlalchemy.exc.IntegrityError as e:
                logger.warning(f'Failed to commit new comment id={new_comment.id} - {e}')
                db.session.rollback()
                flash('Failed to post comment')
            else:
                logger.info(f'Successfully committed new comment id={new_comment.id}')

        comments = get_discussion.comments
        return render_template('discussion.html', title='Discussion', discussion=get_discussion,
                               comments=comments, form=form)

    flash('Failed to load discussion', category='load fail')
    return redirect(url_for('discussions'))


@app.route('/delete/<string:object>/<int:object_id>', methods=['POST'])
def delete_discussion(object, object_id):
    url, del_obj = url_for('index'), ''
    if object == 'discussion':
        del_obj = Discussion.query.get(object_id)
        if del_obj:
            if int(current_user.id) == int(del_obj.poster_id):
                url = url_for('discussions')
    elif object == 'comment':
        del_obj = Comment.query.get(object_id)
        if del_obj:
            if int(current_user.id) == int(del_obj.poster_id):
                url = url_for('discussion', discussion_id=del_obj.discussion_id)
    elif object == 'user':
        del_obj = User.query.get(object_id)
        if del_obj:
            if int(current_user.id) == int(object_id):
                url = url_for('index')
    try:
        db.session.delete(del_obj)
        db.session.commit()
    except sqlalchemy.exc.IntegrityError as e:
        logger.warning(f'Failed to delete {object} id={object_id} - {e}')
        db.session.rollback()
        flash(f'Failed to delete {object}')
    else:
        logger.info(f'Successfully deleted {object} id={object_id}')
    return jsonify({'redirect': url})


@app.route('/logout')
@login_required
def logout():
    logout_user()
    logger.info('Successfully logged out user')
    return redirect(url_for('index', title='Home'))


# user loader
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


@login_manager.unauthorized_handler
def unauthorized():
    flash('You must be logged in to view this page', category='authentication_required')
    return redirect(url_for('login'))


@app.route('/checkloggedon', methods=['POST'])
def check_logged_on():
    if current_user.is_authenticated:
        return jsonify({'success': True})
    flash(request.get_json()['message'], category='authentication_required')
    return jsonify({'redirect': url_for('login'), 'success': False})


@app.route('/add_like/<string:object>/<int:id>/<string:option>', methods=['POST'])
def add_like(object: str, id: int, option: str):
    # Like/Dislike a discussion
    if object == 'discussion':
        liked_discussion = Discussion.query.get(id)
        if liked_discussion:
            if option == 'add_like':
                if str(liked_discussion.id) not in current_user.liked_discussion_ids:
                    liked_discussion.likes += 1
                    current_user.liked_discussion_ids = current_user.liked_discussion_ids + f',{liked_discussion.id}'
                    if str(liked_discussion.id) in current_user.disliked_discussion_ids:
                        liked_discussion.dislikes -= 1
                        current_user.disliked_discussion_ids = current_user.disliked_discussion_ids.replace(f',{liked_discussion.id}', '')
            elif option == 'add_dislike':
                if str(liked_discussion.id) not in current_user.disliked_discussion_ids:
                    liked_discussion.dislikes += 1
                    current_user.disliked_discussion_ids = current_user.disliked_discussion_ids + f',{liked_discussion.id}'
                    if str(liked_discussion.id) in current_user.liked_discussion_ids:
                        liked_discussion.likes -= 1
                        current_user.liked_discussion_ids = current_user.liked_discussion_ids.replace(f',{liked_discussion.id}', '')
            else:
                logger.error(f'option parameter not valid, must be {Literal["add_like", "add_dislike"]}')
    # Like/Dislike a comment
    elif object == 'comment':
        liked_comment = Comment.query.get(id)
        if liked_comment:
            if option == 'add_like':
                if str(liked_comment.id) not in current_user.liked_comment_ids:
                    liked_comment.likes += 1
                    current_user.liked_comment_ids = current_user.liked_comment_ids + f',{liked_comment.id}'
                    if str(liked_comment.id) in current_user.disliked_comment_ids:
                        liked_comment.dislikes -= 1
                        current_user.disliked_comment_ids = current_user.disliked_comment_ids.replace(f',{liked_comment.id}', '')
            elif option == 'add_dislike':
                if str(liked_comment.id) not in current_user.disliked_comment_ids:
                    liked_comment.dislikes += 1
                    current_user.disliked_comment_ids = current_user.disliked_comment_ids + f',{liked_comment.id}'
                    if str(liked_comment.id) in current_user.liked_comment_ids:
                        liked_comment.likes -= 1
                        current_user.liked_comment_ids = current_user.liked_comment_ids.replace(f',{liked_comment.id}', '')
            else:
                logger.error(f'option parameter not valid, must be {Literal["add_like", "add_dislike"]}')
    else:
        logger.error(f'object parameter not valid, must be {Literal["discussion", "discussion"]}')
    # Attempt to commit
    try:
        db.session.commit()
    except sqlalchemy.exc.IntegrityError as e:
        logger.warning(f'Failed to alter likes/dislikes - {e}')
        flash('Failed to add like or dislike')
        return jsonify({'success': False})
    else:
        logger.info('Successfully altered likes/dislikes')
    return jsonify({'success': True})


@app.route('/verify_email/<user_id>/<code>', methods=['GET', 'POST'])
def verify_email(user_id, code):
    user = User.query.get(user_id)
    if user:
        if code == user.email_code:
            user.verified_email = True
            try:
                db.session.commit()
            except sqlalchemy.exc.IntegrityError as e:
                db.session.rollback()
                logger.warning(f'Failed to varify email address for {user_id} - {e}')
                flash('Verification failed please try again')
            else:
                flash('Successfully verified email address!')
                logger.info(f'Successfully verified Email address user_id={user_id}')
                return redirect(url_for('profile', user_id=user_id))
        else:
            flash('It seems the verification failed. The verification was resent')
            logger.error('Verification code sent was incorrect')
            message = Message('Validate Test',
                              [user.email],
                              'Email Validation Code: ')
            mail.send(message)
    else:
        flash('User ID does not exist')
        logger.warning('User ID does not exist')
        return redirect(url_for('index'))


@app.route('/change-password', methods=['GET', 'POST'])
def change_password():
    form = ChangePasswordForm()
    if request.method == 'POST':
        if form.email.validate(form):
            user = User.query.filter_by(email=form.email.data).first()
            if user:
                reset_password_code = str(uuid.uuid4())
                message = Message('Change Password',
                                  [user.email],
                                  html=f'''<p>Someone has tried to change your password!</p>
                                            <p>If this was not you, you can safely ignore this email.</p>
                                            <p>Please click <a href=
                                            'http://127.0.0.1:5000/change-password/{user.id}/{reset_password_code}'>
                                            here</a> to reset your password</p>
                                            <p>This URL will expire in 10 minutes</p>''')
                mail.send(message)
                user.reset_password_code = reset_password_code
                user.reset_password_expire_time = datetime.datetime.utcnow() + dateutil.relativedelta.relativedelta(minutes=10)
                try:
                    db.session.commit()
                except sqlalchemy.exc.IntegrityError as e:
                    flash('An error occurred')
                    logger.warning(f'Failed to set User.reset_password_code - {e}')
                    db.session.rollback()
                else:
                    flash('An email was successfully sent to you. Please go to it to reset your password')
            else:
                flash('No user is registered with this email')
    return render_template('change_password_email.html', title='Change Password', form=form)


@app.route('/change-password/<int:user_id>/<string:code>', methods=['GET', 'POST'])
def reset_password(user_id, code):
    user = User.query.get(user_id)
    if user:
        if user.reset_password_code == code:
            form = ChangePasswordForm()
            if request.method == 'POST':
                if datetime.datetime.utcnow() < user.reset_password_expire_time:
                    if form.new_password.validate(form) and form.new_password_check.validate(form):
                        user.set_password(form.new_password.data)
                        try:
                            db.session.commit()
                        except sqlalchemy.exc.IntegrityError as e:
                            flash('An error occurred')
                            logger.warning(f'Failed to set user new password - {e}')
                            db.session.rollback()
                        else:
                            flash('Your password was successfully changed')
                            return redirect(url_for('login'))
                else:
                    return f"Authorization code has expired, click <a href={url_for('change_password')}>here</a> to try again"

            return render_template('change_password.html', title='Change Password', form=form)
    flash('This user does not exist')
    return redirect(url_for('change_password'))
