"""Flask Productivity API — Session-based Authentication.

A secure RESTful API for managing user-owned tasks with full CRUD,
pagination, and session-based authentication.
"""
from flask import Flask, request, session, jsonify, make_response
from flask_restful import Api, Resource
from marshmallow import ValidationError
from datetime import datetime
from flask_jwt_extended import (
    JWTManager,
    create_access_token,
    get_jwt_identity,
    verify_jwt_in_request,
)

from server.config import Config
from server.models import db, bcrypt, User, Task
from server.schemas import user_schema, users_schema, task_schema, tasks_schema


def create_app(config_class=Config):
    """Application factory pattern for testability and modularity."""
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    bcrypt.init_app(app)
    jwt = JWTManager(app)
    api = Api(app)

    with app.app_context():
        db.create_all()


    def get_current_user():
        """Retrieve the currently logged-in user from session or JWT."""
        user_id = session.get("user_id")
        if user_id:
            return User.query.get(user_id)

        try:
            verify_jwt_in_request(optional=True)
            jwt_id = get_jwt_identity()
            if jwt_id:
                return User.query.get(jwt_id)
        except Exception:
            pass

        return None

    def login_required(func):
        """Decorator to protect routes requiring authentication."""
        def wrapper(*args, **kwargs):
            user = get_current_user()
            if not user:
                return make_response(
                    jsonify({"error": "Unauthorized. Please log in."}),
                    401
                )
            return func(*args, **kwargs)
        wrapper.__name__ = func.__name__
        return wrapper


    @app.route("/signup", methods=["POST"])
    def signup():
        """Register a new user with unique username and hashed password."""
        json_data = request.get_json()
        if not json_data:
            return make_response(jsonify({"error": "No input data provided."}), 400)

        try:
            data = user_schema.load(json_data)
        except ValidationError as err:
            return make_response(jsonify({"errors": err.messages}), 422)

        # Check for existing username
        if User.query.filter_by(username=data["username"]).first():
            return make_response(
                jsonify({"error": "Username already taken."}),
                409
            )

        new_user = User(username=data["username"])
        new_user.password_hash = data["password"]

        db.session.add(new_user)
        db.session.commit()

        # Auto-login after signup
        session["user_id"] = new_user.id
        session.permanent = True

        access_token = create_access_token(identity=new_user.id)

        return make_response(
            jsonify({
                "user": user_schema.dump(new_user),
                "token": access_token
            }),
            201
        )

    @app.route("/login", methods=["POST"])
    def login():
        """Authenticate user and establish session."""
        json_data = request.get_json()
        if not json_data:
            return make_response(jsonify({"error": "No input data provided."}), 400)

        username = json_data.get("username")
        password = json_data.get("password")

        if not username or not password:
            return make_response(
                jsonify({"error": "Username and password are required."}),
                400
            )

        user = User.query.filter_by(username=username).first()

        if user and user.authenticate(password):
            session["user_id"] = user.id
            session.permanent = True
            access_token = create_access_token(identity=user.id)
            return make_response(
                jsonify({
                    "user": user_schema.dump(user),
                    "token": access_token
                }),
                200
            )

        return make_response(
            jsonify({"error": "Invalid username or password."}),
            401
        )

    @app.route("/logout", methods=["DELETE"])
    def logout():
        """Clear the user session."""
        session.pop("user_id", None)
        return make_response(jsonify({"message": "Logged out successfully."}), 204)

    @app.route("/check_session", methods=["GET"])
    def check_session():
        """Return the current user if session is active."""
        user = get_current_user()
        if user:
            return make_response(jsonify(user_schema.dump(user)), 200)
        return make_response(jsonify({"error": "No active session."}), 401)

    @app.route("/me", methods=["GET"])
    def me():
        """Alias for session-compatible user check."""
        return check_session()


    class TaskListResource(Resource):
        """Handles paginated list and creation of tasks."""

        method_decorators = [login_required]

        def get(self):
            """Return paginated tasks belonging to the current user."""
            user = get_current_user()

            # Pagination parameters
            page = request.args.get("page", 1, type=int)
            per_page = request.args.get("per_page", 10, type=int)

            # Clamp values to reasonable bounds
            page = max(1, page)
            per_page = min(max(1, per_page), 50)

            pagination = (
                Task.query
                .filter_by(user_id=user.id)
                .order_by(Task.created_at.desc())
                .paginate(page=page, per_page=per_page, error_out=False)
            )

            return make_response(jsonify({
                "tasks": tasks_schema.dump(pagination.items),
                "pagination": {
                    "page": pagination.page,
                    "per_page": pagination.per_page,
                    "total_pages": pagination.pages,
                    "total_items": pagination.total,
                    "has_next": pagination.has_next,
                    "has_prev": pagination.has_prev
                }
            }), 200)

        def post(self):
            """Create a new task for the current user."""
            user = get_current_user()
            json_data = request.get_json()

            if not json_data:
                return make_response(
                    jsonify({"error": "No input data provided."}),
                    400
                )

            try:
                data = task_schema.load(json_data)
            except ValidationError as err:
                return make_response(jsonify({"errors": err.messages}), 422)

            new_task = Task(
                title=data.get("title"),
                description=data.get("description"),
                priority=data.get("priority", "medium"),
                status=data.get("status", "pending"),
                due_date=data.get("due_date"),
                user_id=user.id
            )

            db.session.add(new_task)
            db.session.commit()

            return make_response(
                jsonify(task_schema.dump(new_task)),
                201
            )


    class TaskDetailResource(Resource):
        """Handles retrieval, update, and deletion of a single task."""

        method_decorators = [login_required]

        def _get_task_or_404(self, task_id, user_id):
            """Fetch a task ensuring it belongs to the current user."""
            task = Task.query.filter_by(id=task_id, user_id=user_id).first()
            if not task:
                return None
            return task

        def get(self, task_id):
            """Return a single task owned by the current user."""
            user = get_current_user()
            task = self._get_task_or_404(task_id, user.id)

            if not task:
                return make_response(
                    jsonify({"error": "Task not found or access denied."}),
                    404
                )

            return make_response(jsonify(task_schema.dump(task)), 200)

        def patch(self, task_id):
            """Update a task owned by the current user."""
            user = get_current_user()
            task = self._get_task_or_404(task_id, user.id)

            if not task:
                return make_response(
                    jsonify({"error": "Task not found or access denied."}),
                    404
                )

            json_data = request.get_json()
            if not json_data:
                return make_response(
                    jsonify({"error": "No input data provided."}),
                    400
                )

            try:
                data = task_schema.load(json_data, partial=True)
            except ValidationError as err:
                return make_response(jsonify({"errors": err.messages}), 422)

            # Update allowed fields
            for field in ["title", "description", "priority", "status", "due_date"]:
                if field in data:
                    setattr(task, field, data[field])

            task.updated_at = datetime.utcnow()
            db.session.commit()

            return make_response(jsonify(task_schema.dump(task)), 200)

        def delete(self, task_id):
            """Delete a task owned by the current user."""
            user = get_current_user()
            task = self._get_task_or_404(task_id, user.id)

            if not task:
                return make_response(
                    jsonify({"error": "Task not found or access denied."}),
                    404
                )

            db.session.delete(task)
            db.session.commit()

            return make_response(
                jsonify({"message": "Task deleted successfully."}),
                200
            )

    # Register RESTful resources
    api.add_resource(TaskListResource, "/tasks")
    api.add_resource(TaskDetailResource, "/tasks/<int:task_id>")


    @app.errorhandler(404)
    def not_found(error):
        return make_response(jsonify({"error": "Resource not found."}), 404)

    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return make_response(jsonify({"error": "Internal server error."}), 500)

    return app


app = create_app()

if __name__ == "__main__":
    app.run(port=5555, debug=True)
