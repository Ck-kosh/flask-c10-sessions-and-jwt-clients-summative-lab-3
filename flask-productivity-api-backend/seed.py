"""Seed script to populate the database with sample data.

Run with: python seed.py
"""
from datetime import datetime, timedelta
from random import choice, randint

from faker import Faker

from server.app import create_app
from server.models import db, User, Task

fake = Faker()

# Sample data constants
PRIORITIES = ["low", "medium", "high", "urgent"]
STATUSES = ["pending", "in_progress", "completed", "archived"]


def seed_users(count=5):
    """Create sample users with secure hashed passwords."""
    users = []
    for i in range(count):
        username = fake.user_name() + str(i)  # ensure uniqueness
        user = User(username=username)
        user.password_hash = "password123"  # same password for all demo accounts
        db.session.add(user)
        users.append(user)

    # Add a predictable demo user for easy testing
    demo = User(username="demo_user")
    demo.password_hash = "demo123"
    db.session.add(demo)
    users.append(demo)

    db.session.commit()
    print(f"  Created {len(users)} users.")
    return users


def seed_tasks(users, tasks_per_user=6):
    """Create sample tasks assigned to each user."""
    task_count = 0
    for user in users:
        for _ in range(tasks_per_user):
            due = fake.date_time_between(
                start_date="-30d",
                end_date="+30d"
            )
            task = Task(
                title=fake.sentence(nb_words=6),
                description=fake.paragraph(nb_sentences=3),
                priority=choice(PRIORITIES),
                status=choice(STATUSES),
                due_date=due,
                user_id=user.id
            )
            db.session.add(task)
            task_count += 1

    db.session.commit()
    print(f"  Created {task_count} tasks.")


def clear_data():
    """Remove all existing data from tables."""
    db.session.query(Task).delete()
    db.session.query(User).delete()
    db.session.commit()
    print("  Cleared existing data.")


def run_seed():
    """Execute the full seeding process."""
    app = create_app()

    with app.app_context():
        print("Seeding database...")
        clear_data()
        users = seed_users(count=5)
        seed_tasks(users, tasks_per_user=6)
        print("Done! Database seeded successfully.")


if __name__ == "__main__":
    run_seed()
