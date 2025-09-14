Vehicle Parking App
This is a basic virtual parking management system for 4-wheeler vehicles. The application is designed to streamline the process of finding, reserving, and managing parking spots.

Features
User Authentication: Secure registration and login for both users and administrators.

Role-Based Access Control: Different dashboards and functionalities for users and admins.

User Dashboard:

View all available parking lots and their capacity.

Reserve and occupy a parking spot.

Release an occupied spot to stop the timer.

View a history of all past parking sessions and their total cost.

Admin Dashboard:

Create, view, and manage parking lots and individual spots.

Monitor all active user reservations and occupied spots.

View a complete history of all reservations made in the system.

Technologies Used
Backend: Python, Flask

Database: SQLite

ORM: Flask-SQLAlchemy

Authentication: Flask-Login, Werkzeug

Frontend: HTML, CSS (Bootstrap)

Setup and Installation
Clone the Repository:

Bash

git clone https://github.com/23f3003227/vehicle-parking-app.git
cd vehicle-parking-app
Create a Virtual Environment:

Bash

python -m venv venv
Activate the Virtual Environment:

Windows:

Bash

venv\Scripts\activate
macOS / Linux:

Bash

source venv/bin/activate
Install Dependencies:

Bash

pip install -r requirements.txt
Run the Application:

Bash

python app.py
The application will start and be accessible at http://127.0.0.1:5000.

Admin Credentials
The application automatically creates an admin account on the first run to allow you to log in and manage the system.

Email: admin@gmail.com

Password: admin

