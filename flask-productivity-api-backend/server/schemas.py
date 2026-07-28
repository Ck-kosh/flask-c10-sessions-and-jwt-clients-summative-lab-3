"""Marshmallow schemas for request/response validation and serialization."""
from marshmallow import Schema, fields, validate, ValidationError


class UserSchema(Schema):
    """Schema for user registration and public representation."""
    id = fields.Integer(dump_only=True)
    username = fields.String(
        required=True,
        validate=validate.Length(min=3, max=80, error="Username must be 3-80 characters.")
    )
    password = fields.String(
        required=True,
        load_only=True,
        validate=validate.Length(min=3, max=128, error="Password must be 3-128 characters.")
    )
    created_at = fields.DateTime(dump_only=True)


class TaskSchema(Schema):
    """Schema for task serialization and deserialization."""
    id = fields.Integer(dump_only=True)
    title = fields.String(
        required=True,
        validate=validate.Length(min=1, max=200, error="Title is required (max 200 chars).")
    )
    description = fields.String(allow_none=True)
    priority = fields.String(
        validate=validate.OneOf(
            ["low", "medium", "high", "urgent"],
            error="Priority must be one of: low, medium, high, urgent."
        ),
        missing="medium"
    )
    status = fields.String(
        validate=validate.OneOf(
            ["pending", "in_progress", "completed", "archived"],
            error="Status must be one of: pending, in_progress, completed, archived."
        ),
        missing="pending"
    )
    due_date = fields.DateTime(allow_none=True, format="%Y-%m-%dT%H:%M:%S")
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)
    user_id = fields.Integer(dump_only=True)


# Instantiate schemas for reuse
user_schema = UserSchema()
users_schema = UserSchema(many=True)
task_schema = TaskSchema()
tasks_schema = TaskSchema(many=True)
