import os

from flask import Flask, send_from_directory

from app import db


def create_app(test_config=None):
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY=os.environ.get("SECRET_KEY", "dev-only-change-me"),
        DATABASE=os.path.join(app.instance_path, "ideal.sqlite"),
        UPLOAD_FOLDER=os.path.join(app.instance_path, "uploads"),
        MAX_CONTENT_LENGTH=50 * 1024 * 1024,
        SESSION_COOKIE_SAMESITE="Lax",
        SESSION_COOKIE_HTTPONLY=True,
    )
    if test_config:
        app.config.update(test_config)

    os.makedirs(app.instance_path, exist_ok=True)
    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

    db.init_app(app)

    from app.boundary.auth_page import bp as auth_bp
    from app.boundary.home_page import bp as home_bp
    from app.boundary.portfolio_page import bp as portfolio_bp
    from app.boundary.admin_page import bp as admin_bp
    from app.boundary.consultation_page import bp as consultation_bp
    from app.boundary.review_page import bp as review_bp
    from app.boundary.customer_project_page import bp as customer_projects_bp
    
    app.register_blueprint(review_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(home_bp)
    app.register_blueprint(portfolio_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(customer_projects_bp)
    # Register the blueprint with the app
    app.register_blueprint(consultation_bp)

    @app.route("/uploads/<path:filename>")
    def uploaded_file(filename):
        return send_from_directory(app.config["UPLOAD_FOLDER"], filename)

    return app
