from app import create_app, db
from app.models import User

app = create_app()
with app.app_context():
    user = User(username="testuser", email="test@example.com", admin=False)
    user.set_password("testpassword")
    db.session.add(user)
    db.session.commit()