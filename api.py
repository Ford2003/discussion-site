import sqlalchemy.exc
from app import app
from flask_restful import Resource, Api, reqparse
from flask import request, g
from models import *
from constants import *
from functools import wraps


api = Api(app, prefix='/api/v1')

parser = reqparse.RequestParser()
parser.add_argument('id', type=int, help='The id of the requested object')
parser.add_argument('title', type=str, help='The title of the discussion')
parser.add_argument('text', type=str, help='The text of the discussion')
parser.add_argument('tags', type=str, help='The tags of the discussion', choices=TAGS, action='append')
parser.add_argument('maxResults', type=int, help='The maximum number of results to give. should be in range [1, 50]', choices=range(1, 51))


def authorisation_required(func):
    @wraps(func)
    def authorised(*args, **kwargs):
        key = request.headers.get('Authorization')
        if key:
            key = key.split(' ')[1]
            user = User.query.filter_by(api_key=key).first()
            if user:
                g.user = user
                return func(*args, **kwargs)
        return ResponseTemplate(request.method.upper(), 401, 'You are not authorized for this request', []).response(), 401
    return authorised


def make_comment_response(comment: Comment):
    d = {
            'id': comment.id,
            'text': comment.text,
            'author': ['deleted user'] if comment.poster is None else comment.poster.username,
            'authorId': ['deleted user'] if comment.poster is None else comment.poster_id,
            'discussionId': comment.discussion_id,
            'stats': {
                'likes': comment.likes,
                'dislikes': comment.dislikes
            }
        }
    return d


def make_discussion_response(discussion: Discussion):
    comments = []
    for comment in discussion.comments:
        comments.append(make_comment_response(comment))
    d = {
            'id': discussion.id,
            'title': discussion.title,
            'text': discussion.text,
            'author': ['deleted user'] if discussion.poster is None else discussion.poster.username,
            'authorId': ['deleted user'] if discussion.poster is None else discussion.poster_id,
            'postDate': str(discussion.post_date.date()),
            'postTime': str(discussion.post_date.time()),
            'stats': {
                'views': discussion.views,
                'likes': discussion.likes,
                'dislikes': discussion.dislikes
            },
            'comments': comments
        }
    return d


def make_user_response(user: User):
    discussions = [make_discussion_response(discussion) for discussion in user.discussions]
    comments = [make_comment_response(comment) for comment in user.comments]

    d = {
        'id': user.id,
        'username': user.username,
        'joinedAtDate': str(user.joined_at_date.date()),
        'joinedAtTime': str(user.joined_at_date.time()),
        'discussions': discussions,
        'comments': comments
    }
    return d


class DiscussionAPI(Resource):
    def get(self):
        args = parser.parse_args()
        discussion_id = args['id']
        if discussion_id is None or discussion_id < 0:
            response = ResponseTemplate('GET', 400, 'discussion_id must be an integer', [])
            return response.response(), 400
        else:
            discussion = Discussion.query.get(discussion_id)
            if discussion:
                items = [make_discussion_response(discussion)]
                response = ResponseTemplate('GET', 200, 'success', items)
                return response.response(), 200
            else:
                response = ResponseTemplate('GET', 404, 'Request was not recognised', [])
                return response.response(), 404

    @authorisation_required
    def post(self):
        user = g.user
        args = parser.parse_args()
        if not (args.get('tags') and args.get('text') and args.get('tags')):
            return ResponseTemplate('POST', 400, 'The required parameters were not given', []).response(), 400
        tags = ','.join(args['tags'])
        discussion = Discussion(title=args['title'], text=args['text'], tags=tags, poster_id=user.id)
        try:
            db.session.add(discussion)
            db.session.commit()
        except sqlalchemy.exc.IntegrityError:
            return ResponseTemplate('POST', 406, 'IntegrityError maybe the title is a duplicate', []).response(), 406
        else:
            items = [make_discussion_response(discussion)]
            return ResponseTemplate('POST', 201, 'success', items).response(), 201

    @authorisation_required
    def put(self):
        args = parser.parse_args()
        id = args.get('id')
        user = g.user
        if id is None:
            return ResponseTemplate('PUT', 400, 'Request must contain id parameter', []).response(), 400
        title = args.get('title')
        text = args.get('text')
        tags = ','.join(args['tags']) if args.get('tags') else None
        if not (title or text or tags):
            return ResponseTemplate('PUT', 400, 'Request must contain at least 1 of: "title", "text" or "tags"', []).response(), 400
        discussion = Discussion.query.get(id)
        if discussion.poster_id != user.id:
            return ResponseTemplate('PUT', 401, 'You are not authorized for this request', []).response(), 401
        if discussion:
            discussion.title = title if title else discussion.title
            discussion.text = text if text else discussion.text
            discussion.tags = tags if tags else discussion.tags
            try:
                db.session.commit()
            except sqlalchemy.exc.IntegrityError:
                return ResponseTemplate('PUT', 406, 'IntegrityError maybe a dupicate title', []).response(), 406
            else:
                items = [make_discussion_response(discussion)]
                return ResponseTemplate('PUT', 200, 'success', items).response(), 200

    @authorisation_required
    def delete(self):
        user = g.user
        args = parser.parse_args()
        id = args.get('id')
        discussion = Discussion.query.get(id)
        if not id:
            return ResponseTemplate('DELETE', 400, 'id parameter is required', []).response(), 400
        if user.id != discussion.poster_id:
            return ResponseTemplate('DELETE', 401, 'You are not authorised for this request', []).response(), 401

        db.session.delete(discussion)
        try:
            db.session.commit()
        except sqlalchemy.exc.IntegrityError:
            db.session.rollback()
            return ResponseTemplate('DELETE', 406, 'DELETE request failed', []).response(), 406
        else:
            return ResponseTemplate('DELETE', 200, 'success', []).response(), 200


api.add_resource(DiscussionAPI, '/discussion')


class DiscussionList(Resource):
    def get(self):
        args = parser.parse_args()
        max_results = args.get('maxResults') if args.get('maxResults') else 5
        discussions = Discussion.query.limit(max_results).all()
        items = [make_discussion_response(discussion) for discussion in discussions]

        response = ResponseTemplate('GET', 200, 'success', items)
        return response.response(), 200


api.add_resource(DiscussionList, '/discussion/list')


class CommentAPI(Resource):
    def get(self):
        args = parser.parse_args()
        id = args.get('id')
        if id is None:
            return ResponseTemplate('GET', 400, 'id parameter is required', []).response(), 400

        comment = Comment.query.get(id)
        if comment:
            items = [make_comment_response(comment)]
            return ResponseTemplate('GET', 200, 'success', items).response(), 200
        else:
            return ResponseTemplate('GET', 404, f'No comment with id={id}', []).response(), 404

    @authorisation_required
    def post(self):
        args = parser.parse_args()
        id = args.get('id')
        text = args.get('text')
        if not (id and text):
            return ResponseTemplate('POST', 400, 'id and text parameters are required', []).response(), 400

        user = g.user
        comment = Comment(text=text, poster_id=user.id, discussion_id=id)
        try:
            db.session.add(comment)
            db.session.commit()
        except sqlalchemy.exc.IntegrityError:
            return ResponseTemplate('POST', 406, 'Failed to post comment', []).response(), 406
        else:
            items = [make_comment_response(comment)]
            return ResponseTemplate('POST', 201, 'success', items).response(), 201

    @authorisation_required
    def put(self):
        args = parser.parse_args()
        id = args.get('id')
        text = args.get('text')
        if not (id and text):
            return ResponseTemplate('PUT', 400, 'id and text parameters are required', []).response(), 400

        comment = Comment.query.get(id)
        user = g.user
        if comment:
            if user.id != comment.poster_id:
                return ResponseTemplate('PUT', 401, 'You are not authorized for this request', []).response(), 401
            comment.text = text if not text.isspace() else comment.text
            try:
                db.session.commit()
            except sqlalchemy.exc.IntegrityError:
                return ResponseTemplate('PUT', 406, 'Failed to edit comment', []).response(), 406
            else:
                items = [make_comment_response(comment)]
                return ResponseTemplate('PUT', 200, 'success', items).response(), 200
        else:
            return ResponseTemplate('PUT', 404, f'No comment found with id={id}', []).response(), 404

    @authorisation_required
    def delete(self):
        user = g.user
        args = parser.parse_args()
        id = args.get('id')
        comment = Comment.query.get(id)
        if not id:
            return ResponseTemplate('DELETE', 400, 'id parameter is required', []).response(), 400
        if user.id != comment.poster_id:
            return ResponseTemplate('DELETE', 401, 'You are not authorised for this request', []).response(), 401

        db.session.delete(comment)
        try:
            db.session.commit()
        except sqlalchemy.exc.IntegrityError:
            db.session.rollback()
            return ResponseTemplate('DELETE', 406, 'DELETE request failed', []).response(), 406
        else:
            return ResponseTemplate('DELETE', 200, 'success', []).response(), 200


api.add_resource(CommentAPI, '/comment')


class CommentList(Resource):
    def get(self):
        args = parser.parse_args()
        max_results = args.get('maxResults') if args.get('maxResults') else 5
        comments = Comment.query.limit(max_results).all()
        items = [make_comment_response(comment) for comment in comments]
        return ResponseTemplate('GET', 200, 'success', items).response(), 200


api.add_resource(CommentList, '/comment/list')


class UserAPi(Resource):
    def get(self):
        args = parser.parse_args()
        id = args.get('id')
        if not id:
            return ResponseTemplate('GET', 400, 'id is a required parameter', []).response(), 400
        user = User.query.get(id)
        if user:
            items = [make_user_response(user)]
            return ResponseTemplate('GET', 200, 'success', items).response(), 200
        else:
            return ResponseTemplate('GET', 404, f'No user found with id={id}', []).response(), 404

    @authorisation_required
    def delete(self):
        user = g.user
        args = parser.parse_args()
        id = args.get('id')
        if not id:
            return ResponseTemplate('DELETE', 400, 'id parameter is required', []).response(), 400
        if user.id != id:
            return ResponseTemplate('DELETE', 401, 'You are not authorised for this request', []).response(), 401
        db.session.delete(user)
        try:
            db.session.commit()
        except sqlalchemy.exc.IntegrityError:
            db.session.rollback()
            return ResponseTemplate('DELETE', 406, 'DELETE request failed', []).response(), 406
        else:
            return ResponseTemplate('DELETE', 200, 'success', []).response(), 200


api.add_resource(UserAPi, '/user')


class UserList(Resource):
    def get(self):
        args = parser.parse_args()
        max_results = args.get('maxResults') if args.get('maxResults') else 5
        users = User.query.limit(max_results).all()
        items = [make_user_response(user) for user in users]
        return ResponseTemplate('GET', 200, 'success', items).response(), 200


api.add_resource(UserList, '/user/list')
