import os
from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

# Initialise extensions (not yet bound to an app)
db = SQLAlchemy()
migrate = Migrate()


def create_app() -> Flask:
    """Application factory function."""
    app = Flask(
        __name__,
        instance_relative_config=False,
        template_folder="templates",
        static_folder="static",
    )

    # Load configuration
    from .config import Config
    app.config.from_object(Config)

    # Ensure the upload folder exists
    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

    # Bind extensions to the app
    db.init_app(app)
    migrate.init_app(app, db)

    # Register blueprints
    from .routes import api
    app.register_blueprint(api)

    # Serve the frontend dashboard at root
    @app.route("/")
    def index():
        return render_template("index.html")

    # Import models so Flask-Migrate can detect them
    from . import models  # noqa: F401

    return app
