from flask import Flask

from core.app_bootstrap import (
    install_legacy_endpoint_aliases,
    register_routes,
    register_startup_hooks,
    register_template_context,
)
from core.config import settings
from core.pg_schema import ensure_postgres_schema


def create_app(config_overrides=None, *, init_schema=True):
    app = Flask(__name__)
    app.secret_key = settings.flask_secret_key

    if config_overrides:
        app.config.update(config_overrides)

    if init_schema:
        ensure_postgres_schema()

    register_startup_hooks(app)
    register_routes(app)
    register_template_context(app)
    install_legacy_endpoint_aliases(app)

    return app
