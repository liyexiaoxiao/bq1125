from app import create_app, db
from app.models import User
from app.utils.security import hash_password, generate_salt
import uuid
from datetime import datetime

app = create_app('development')

def seed_admin():
    with app.app_context():
        # Ensure tables exist
        db.create_all()
        
        admin = User.query.filter_by(LOGINNAME='admin').first()
        if not admin:
            print("Creating admin user...")
            salt = generate_salt()
            password = "Fuzz_jitong_test"
            hashed_pw = hash_password(password, salt).hex()
            
            admin_user = User(
                ID=str(uuid.uuid4()),
                LOGINNAME='admin',
                PWD=hashed_pw,
                SALT=salt.hex(),
                NAME='Administrator',
                CREATEDATETIME=datetime.now(),
                UPDATEDATETIME=datetime.now(),
                STATUS='1'
            )
            db.session.add(admin_user)
            db.session.commit()
            print("Admin user created.")
        else:
            print("Admin user already exists.")

if __name__ == '__main__':
    seed_admin()
