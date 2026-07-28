"""Database models for the Productivity API."""
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy_serializer import SerializerMixin
from flask_bcrypt import Bcrypt

# Initialize extensions
db = SQLAlchemy()
bcrypt = Bcrypt()


class User(db.Model, SerializerMixin):
    """User model with secure password handling."""

    __tablename__ = "users"

    serialize_rules = ("-tasks.user", "-_password_hash",)

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    _password_hash = db.Column(db.String(128), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationship: a user has many tasks
    tasks = db.relationship(
        "Task",
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="dynamic"
    )

    @property
    def password_hash(self):
        """Prevent direct access to password hash."""
        raise AttributeError("Password hash is not readable.")

    @password_hash.setter
    def password_hash(self, password):
        """Hash and store the password using bcrypt."""
        self._password_hash = bcrypt.generate_password_hash(
            password.encode("utf-8")
        ).decode("utf-8")

    def authenticate(self, password):
        """Verify a plaintext password against the stored hash."""
        return bcrypt.check_password_hash(self._password_hash, password)

    def __repr__(self):
        return f"<User {self.id}: {self.username}>"


class Task(db.Model, SerializerMixin):
    """Task model representing a user's productivity item."""

    __tablename__ = "tasks"

    serialize_rules = ("-user.tasks",)

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    priority = db.Column(db.String(20), default="medium")  # low, medium, high, urgent
    status = db.Column(db.String(20), default="pending")  # pending, in_progress, completed, archived
    due_date = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Foreign key linking task to its owner
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)

    # Relationship back to user
    user = db.relationship("User", back_populates="tasks")

    def __repr__(self):
        return f"<Task {self.id}: {self.title} [{self.status}]>"
