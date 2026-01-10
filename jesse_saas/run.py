from app import create_app, db
from app.models import Client, KnowledgeBase, InteractionLog
import os
from dotenv import load_dotenv

# Load .env from project root (one level up)
root_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
load_dotenv(os.path.join(root_path, '.env'))

app = create_app()

@app.shell_context_processor
def make_shell_context():
    return {'db': db, 'Client': Client, 'KnowledgeBase': KnowledgeBase, 'InteractionLog': InteractionLog}

if __name__ == '__main__':
    app.run(debug=True, port=8000)
