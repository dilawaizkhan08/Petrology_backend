from app import create_app, db
from seed import seed_admin_user
app = create_app()

def init_db():
    with app.app_context():
        db.create_all()
        print("Database tables created successfully.")
        seed_admin_user()
        db_path = 'instance/db.sqlite3'  # Adjusted path

init_db()
