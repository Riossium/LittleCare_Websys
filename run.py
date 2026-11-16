import os
from app import create_app
from app.extensions import db
from init_db import seed_database

env = os.getenv('FLASK_ENV', 'development')
app = create_app(env)


@app.cli.command('init-db')
def init_db_command():
    """CLI command to initialize and seed the database."""
    seed_database()


if __name__ == '__main__':
    # Ensure database is initialized before serving
    with app.app_context():
        db.create_all()
    
    port = int(os.getenv('PORT', 5000))
    debug = os.getenv('DEBUG', 'True').lower() in ['true', '1', 't']
    app.run(host='0.0.0.0', port=port, debug=debug)
