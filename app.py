from project_app import create_app, db
from project_app.models import Admin
import os

app = create_app()

def create_db_and_seed_admin():
    with app.app_context():
        # db.drop_all() # Comment this out to preserve data
        db.create_all()
        print("Database tables created.")

        if not Admin.query.filter_by(email_id='admin@gmail.com').first():
            admin_user = Admin(
                email_id='admin@gmail.com',
                fullname='System Administrator',
                address='Admin HQ',
                pin_code='110001'
            )
            admin_user.set_password('admin')
            db.session.add(admin_user)
            db.session.commit()
            print("Predefined admin user created: admin@gmail.com / admin")
        else:
            print("Admin user already exists.")

if __name__ == '__main__':
    if not os.path.exists(os.path.join(app.instance_path, 'site.db')):
        os.makedirs(app.instance_path, exist_ok=True)
        create_db_and_seed_admin()
    app.run(debug=True)