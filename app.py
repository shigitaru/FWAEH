from app_factory import create_app
from core.config import settings

app = create_app()


if __name__ == '__main__':
    print('\n  Protocol Archive - http://127.0.0.1:5000\n')
    app.run(debug=settings.flask_debug, port=5000)
