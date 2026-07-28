from flask import Flask, request, jsonify, session
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_bcrypt import Bcrypt
from flask_restful import Api, Resource
from sqlalchemy.exc import IntegrityError
from config import Config

app = Flask(__name__)
app.config.from_object(Config)

db = SQLAlchemy(app)
migrate = Migrate(app, db)
bcrypt = Bcrypt(app)
api = Api(app)

# Import models after db initialization to avoid circular imports
from models import User, Task


class Signup(Resource):
    """Handle user registration."""

    def post(self):
        data = request.get_json()

        # Validate required fields
        if not data or not data.get("username") or not data.get("password"):
            return {"error": "Username and password are required."}, 400

        username = data.get("username").strip()
        password = data.get("password")

        if len(username) < 3:
            return {"error": "Username must be at least 3 characters long."}, 400

        if len(password) < 6:
            return {"error": "Password must be at least 6 characters long."}, 400

        # Hash password and create user
        password_hash = bcrypt.generate_password_hash(password).decode("utf-8")
        new_user = User(username=username, password_hash=password_hash)

        try:
            db.session.add(new_user)
            db.session.commit()
            # Auto-login after signup
            session["user_id"] = new_user.id
            return {
                "id": new_user.id,
                "username": new_user.username,
                "message": "User created and logged in successfully."
            }, 201
        except IntegrityError:
            db.session.rollback()
            return {"error": "Username already exists."}, 409


class Login(Resource):
    """Handle user login with session-based authentication."""

    def post(self):
        data = request.get_json()

        if not data or not data.get("username") or not data.get("password"):
            return {"error": "Username and password are required."}, 400

        username = data.get("username").strip()
        password = data.get("password")

        user = User.query.filter_by(username=username).first()

        if user and bcrypt.check_password_hash(user.password_hash, password):
            session["user_id"] = user.id
            return {
                "id": user.id,
                "username": user.username,
                "message": "Logged in successfully."
            }, 200

        return {"error": "Invalid username or password."}, 401


class Logout(Resource):
    """Handle user logout by clearing the session."""

    def delete(self):
        if "user_id" in session:
            session.pop("user_id")
            return {"message": "Logged out successfully."}, 200
        return {"error": "No active session."}, 401


class CheckSession(Resource):
    """Check if a user is currently logged in and return their data."""

    def get(self):
        user_id = session.get("user_id")

        if user_id:
            user = User.query.get(user_id)
            if user:
                return {
                    "id": user.id,
                    "username": user.username
                }, 200

        return {"error": "Not authenticated."}, 401

def get_current_user():
    """Helper to retrieve the currently logged-in user from session."""
    user_id = session.get("user_id")
    if user_id:
        return User.query.get(user_id)
    return None


class TaskList(Resource):
    """
    Handle paginated listing of tasks and creation of new tasks.
    GET  /tasks  - Retrieve paginated tasks for the logged-in user.
    POST /tasks  - Create a new task for the logged-in user.
    """

    def get(self):
        user = get_current_user()
        if not user:
            return {"error": "Unauthorized. Please log in."}, 401

        # Pagination parameters
        page = request.args.get("page", 1, type=int)
        per_page = request.args.get("per_page", 10, type=int)

        # Cap per_page to prevent excessive load
        per_page = min(per_page, 50)

        # Query only the current user's tasks, ordered by creation date
        pagination = Task.query.filter_by(user_id=user.id)            .order_by(Task.created_at.desc())            .paginate(page=page, per_page=per_page, error_out=False)

        tasks = [task.to_dict() for task in pagination.items]

        return {
            "tasks": tasks,
            "pagination": {
                "page": pagination.page,
                "per_page": pagination.per_page,
                "total_pages": pagination.pages,
                "total_items": pagination.total,
                "has_next": pagination.has_next,
                "has_prev": pagination.has_prev
            }
        }, 200


    def post(self):
        user = get_current_user()
        if not user:
            return {"error": "Unauthorized. Please log in."}, 401

        data = request.get_json()

        if not data or not data.get("title"):
            return {"error": "Title is required."}, 400

        title = data.get("title").strip()
        description = data.get("description", "").strip()
        priority = data.get("priority", "medium").lower()
        status = data.get("status", "pending").lower()
        due_date = data.get("due_date")

        # Validate priority
        valid_priorities = ["low", "medium", "high"]
        if priority not in valid_priorities:
            return {"error": f"Priority must be one of: {valid_priorities}"}, 400

        # Validate status
        valid_statuses = ["pending", "in_progress", "completed"]
        if status not in valid_statuses:
            return {"error": f"Status must be one of: {valid_statuses}"}, 400

        new_task = Task(
            title=title,
            description=description,
            priority=priority,
            status=status,
            due_date=due_date,
            user_id=user.id
        )

        db.session.add(new_task)
        db.session.commit()

        return new_task.to_dict(), 201


class TaskDetail(Resource):
    """
    Handle retrieval, update, and deletion of a single task.
    GET    /tasks/<id>  - Retrieve a specific task.
    PATCH  /tasks/<id>  - Update a specific task.
    DELETE /tasks/<id>  - Delete a specific task.
    """

    def get(self, id):
        user = get_current_user()
        if not user:
            return {"error": "Unauthorized. Please log in."}, 401

        task = Task.query.get(id)

        if not task:
            return {"error": "Task not found."}, 404

        if task.user_id != user.id:
            return {"error": "Forbidden. You can only access your own tasks."}, 403

        return task.to_dict(), 200

    def patch(self, id):
        user = get_current_user()
        if not user:
            return {"error": "Unauthorized. Please log in."}, 401

        task = Task.query.get(id)

        if not task:
            return {"error": "Task not found."}, 404

        if task.user_id != user.id:
            return {"error": "Forbidden. You can only update your own tasks."}, 403

        data = request.get_json()

        if not data:
            return {"error": "No data provided for update."}, 400

        # Update allowed fields
        if "title" in data:
            task.title = data["title"].strip()
        if "description" in data:
            task.description = data["description"].strip()
        if "priority" in data:
            priority = data["priority"].lower()
            valid_priorities = ["low", "medium", "high"]
            if priority not in valid_priorities:
                return {"error": f"Priority must be one of: {valid_priorities}"}, 400
            task.priority = priority
        if "status" in data:
            status = data["status"].lower()
            valid_statuses = ["pending", "in_progress", "completed"]
            if status not in valid_statuses:
                return {"error": f"Status must be one of: {valid_statuses}"}, 400
            task.status = status
        if "due_date" in data:
            task.due_date = data["due_date"]

        db.session.commit()
        return task.to_dict(), 200

    def delete(self, id):
        user = get_current_user()
        if not user:
            return {"error": "Unauthorized. Please log in."}, 401

        task = Task.query.get(id)

        if not task:
            return {"error": "Task not found."}, 404

        if task.user_id != user.id:
            return {"error": "Forbidden. You can only delete your own tasks."}, 403

        db.session.delete(task)
        db.session.commit()

        return {"message": "Task deleted successfully."}, 200

api.add_resource(Signup, "/signup")
api.add_resource(Login, "/login")
api.add_resource(Logout, "/logout")
api.add_resource(CheckSession, "/check_session")
api.add_resource(TaskList, "/tasks")
api.add_resource(TaskDetail, "/tasks/<int:id>")


@app.route("/")
def index():
    """Root endpoint with API info."""
    return jsonify({
        "message": "Welcome to the Productivity Task API",
        "version": "1.0.0",
        "auth": "session-based",
        "endpoints": {
            "auth": ["/signup", "/login", "/logout", "/check_session"],
            "tasks": ["/tasks (GET, POST)", "/tasks/<id> (GET, PATCH, DELETE)"]
        }
    })


if __name__ == "__main__":
    app.run(debug=True, port=5555)
