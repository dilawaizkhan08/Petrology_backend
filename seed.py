from app import db, create_app
from app.models import User
from faker import Faker

def seed_admin_user():
    admin_email = 'admin@gmail.com'
    admin_password = 'AdminPassword123!'  # Ensure this password meets your validation criteria

    existing_user = User.query.filter_by(email=admin_email).first()
    if existing_user:
        print('Admin user already exists.')
        return

    admin_user = User(
        email=admin_email,
        full_name='Admin User',  # Provide a valid full name
        role='Founder',  # Provide a valid role
    )
    admin_user.set_password(admin_password)
    admin_user.is_admin = True
    admin_user.email_verified = True

    db.session.add(admin_user)
    db.session.commit()
    print('Admin user created successfully.')



if __name__ == "__main__":
    app = create_app()
    with app.app_context():
        seed_admin_user()
