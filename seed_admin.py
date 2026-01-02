from app import create_app, db
from app.models import User, Role, Resource
from app.utils.security import hash_password, generate_salt
import uuid
from datetime import datetime

app = create_app('development')

def seed_admin():
    with app.app_context():
        # Ensure tables exist
        db.create_all()
        
        # Create Admin Role
        admin_role = Role.query.filter_by(NAME='admin').first()
        if not admin_role:
            print("Creating admin role...")
            admin_role = Role(
                ID=str(uuid.uuid4()),
                NAME='admin'
            )
            db.session.add(admin_role)
        
        # Define permissions
        permissions = [
            'system:user:query',
            'system:user:remove',
            'system:user:edit',
            'system:config:list',
            'system:config:query',
            'system:config:add',
            'system:config:edit',
            'system:config:remove',
            'system:config:export'
        ]
        
        # Create Resources and assign to Admin Role
        for perm in permissions:
            resource = Resource.query.filter_by(PERMS=perm).first()
            if not resource:
                print(f"Creating resource {perm}...")
                resource = Resource(
                    ID=str(uuid.uuid4()),
                    NAME=perm,
                    PERMS=perm,
                    URL='' # URL is not strictly checked in permission decorator, only PERMS
                )
                db.session.add(resource)
            
            if resource not in admin_role.resources:
                admin_role.resources.append(resource)
        
        db.session.commit()

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
            admin_user.roles.append(admin_role)
            db.session.add(admin_user)
            db.session.commit()
            print("Admin user created.")
        else:
            # Ensure admin has the role
            if admin_role not in admin.roles:
                admin.roles.append(admin_role)
                db.session.commit()
                print("Admin role assigned to existing admin user.")
            print("Admin user already exists.")

if __name__ == '__main__':
    seed_admin()
