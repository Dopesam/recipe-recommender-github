import sys
import os

# Add the parent directory to Python path to import from backend
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

# Set the path for the database
os.environ['DB_PATH'] = os.path.join(os.path.dirname(__file__), '..', 'database', 'recipes.db')

from backend.app import app

# Initialize the database when the module is imported
from backend.app import init_database
init_database()

# Export the app for Vercel
app = app
