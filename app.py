import os
import json
import configparser
import mysql.connector
# Remove the pooling import since we're not using connection pools
# from mysql.connector import pooling
from flask import Flask, render_template, request, jsonify, redirect, url_for

app = Flask(__name__)

# Get the absolute path to the config file
basedir = os.path.abspath(os.path.dirname(__file__))
config_path = os.path.join(basedir, 'config.ini')
config = configparser.ConfigParser()

# Read the config file
if not os.path.exists(config_path):
    raise FileNotFoundError(
        f"Configuration file not found at {config_path}. "
        "Please create config.ini file as described in README.md"
    )

config.read(config_path)

# Add error checking for the MySQL section
if 'MYSQL' not in config:
    raise ValueError("MYSQL section not found in config.ini. Please check README.md for the correct format.")

# Database configuration - PythonAnywhere MySQL
db_config = {
    'host': config['MYSQL']['HOST'],
    'user': config['MYSQL']['USER'],
    'password': config['MYSQL']['PASSWORD'],
    'database': config['MYSQL']['DATABASE']
}

# Helper function for database connections
def get_db_connection():
    """Get a database connection"""
    try:
        conn = mysql.connector.connect(**db_config)
        return conn, None
    except mysql.connector.Error as err:
        print(f"Database connection error: {err}")
        return None, str(err)

# Database setup
def init_db():
    try:
        conn, error = get_db_connection()
        if error:
            print(f"Critical error initializing database: {error}")
            return
            
        cursor = conn.cursor()
        
        # Create recipes table if it doesn't exist
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS recipes (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(255) NOT NULL,
            ingredients TEXT NOT NULL
        )
        ''')
        
        conn.commit()
        cursor.close()
        conn.close()
        print("Database initialized successfully")
    except Exception as e:
        print(f"Critical error initializing database: {e}")

# Initialize JSON file for temporary storage
def init_json():
    if not os.path.exists('recipes.json'):
        with open('recipes.json', 'w') as f:
            json.dump([], f)

# Get recipes from JSON file
def get_recipes():
    try:
        with open('recipes.json', 'r') as f:
            return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        return []

# Save recipes to JSON file
def save_recipes(recipes):
    with open('recipes.json', 'w') as f:
        json.dump(recipes, f, indent=4)

# Get default ingredients (mock data in Dutch)
def get_default_ingredients(recipe_name):
    # Dictionary of common Dutch recipes and their ingredients
    recipe_ingredients = {
        'pannenkoeken': ['bloem', 'melk', 'eieren', 'zout'],
        'stamppot': ['aardappelen', 'boerenkool', 'rookworst', 'spekjes'],
        'erwtensoep': ['spliterwten', 'varkensvlees', 'prei', 'wortel'],
        'bitterballen': ['rundvlees', 'bouillon', 'bloem', 'paneermeel'],
        'hutspot': ['aardappelen', 'wortelen', 'uien', 'rundvlees'],
        'poffertjes': ['bloem', 'gist', 'melk', 'boter'],
        'boerenkool': ['boerenkool', 'aardappelen', 'rookworst', 'spekjes'],
        'appeltaart': ['appels', 'bloem', 'boter', 'kaneel']
    }
    
    # Convert recipe name to lowercase for case-insensitive matching
    recipe_name_lower = recipe_name.lower()
    
    # Check if the recipe name exactly matches one of our known recipes
    if recipe_name_lower in recipe_ingredients:
        return recipe_ingredients[recipe_name_lower]
    
    # If no exact match is found, return None
    return None

def get_all_recipes():
    """Helper function to get all recipes from database"""
    if __name__ == "__main__":  # Development mode
        print("Running in development mode - using mock data")
        return [], None
    
    conn, error = get_db_connection()
    if error:
        return None, error
    
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute('SELECT id, name FROM recipes ORDER BY name')
        recipes = cursor.fetchall()
        return recipes, None
    except mysql.connector.Error as err:
        return None, str(err)
    finally:
        cursor.close()
        conn.close()

@app.route('/')
def index():
    """Default route - shows recipe selector"""
    recipes, error = get_all_recipes()
    if error:
        return render_template('error.html', error=error)
    return render_template('index.html', recipes=recipes or [])

@app.route('/recipe_manager')
def recipe_manager():
    """Route for the recipe manager page"""
    recipes = get_recipes()
    return render_template('recipe_manager.html', recipes=recipes)

@app.route('/add_recipe', methods=['POST'])
def add_recipe():
    data = request.get_json()
    recipes = get_recipes()
    recipes.append({
        'name': data['name'],
        'ingredients': data['ingredients']
    })
    save_recipes(recipes)
    return jsonify({'success': True})

@app.route('/delete_recipe/<int:index>', methods=['DELETE'])
def delete_recipe(index):
    recipes = get_recipes()
    if 0 <= index < len(recipes):
        del recipes[index]
        save_recipes(recipes)
        return jsonify({'success': True})
    return jsonify({'success': False, 'error': 'Recipe not found'})

@app.route('/save_to_db', methods=['POST'])
def save_to_db():
    recipes = get_recipes()
    
    if __name__ == "__main__":
        print("Running in development mode - skipping database operations")
        return jsonify({'success': True, 'message': 'Development mode - database operations skipped'})
    
    try:
        conn, error = get_db_connection()
        if error:
            return jsonify({'success': False, 'error': error})
            
        cursor = conn.cursor()
        
        for recipe in recipes:
            cursor.execute(
                'INSERT INTO recipes (name, ingredients) VALUES (%s, %s)',
                (recipe['name'], json.dumps(recipe['ingredients']))
            )
        
        conn.commit()
        cursor.close()
        conn.close()
        
        # Clear the temporary storage
        save_recipes([])
        
        return jsonify({'success': True})
    except Exception as e:
        print(f"Unexpected error: {e}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/get_default_ingredients', methods=['POST'])
def default_ingredients_route():
    data = request.get_json()
    recipe_name = data.get('recipe_name', '')
    ingredients = get_default_ingredients(recipe_name)
    return jsonify({'ingredients': ingredients})

@app.route('/view_db')
def view_db():
    
    if __name__ == "__main__":
        print("Running in development mode - skipping database operations")
        return jsonify({'success': True, 'message': 'Development mode - database operations skipped'})
    
    try:
        conn, error = get_db_connection()
        if error:
            return f"Database connection error: {error}"
            
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM recipes')
        recipe_data = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        recipes = []
        for row in recipe_data:
            id, name, ingredients_json = row
            ingredients = json.loads(ingredients_json)
            recipes.append({
                'id': id,
                'name': name,
                'ingredients': ingredients
            })
        
        return render_template('view_db.html', recipes=recipes)
    except Exception as e:
        print(f"Unexpected error: {e}")
        return f"Error: {str(e)}"

@app.route('/get_ingredients', methods=['POST'])
def get_ingredients():
    """API endpoint to get ingredients for selected recipes"""
    
    # Check if running in development mode
    if __name__ == "__main__":
        print("Running in development mode - using mock data")
        return jsonify({
            'success': True,
            'ingredients': ['Mock ingredient 1', 'Mock ingredient 2', 'Mock ingredient 3']
        })
    
    try:
        data = request.get_json()
        recipe_ids = data.get('recipe_ids', [])
        
        conn, error = get_db_connection()
        if error:
            return jsonify({'success': False, 'error': error}), 500
            
        cursor = conn.cursor(dictionary=True)
        
        cursor.execute(
            'SELECT ingredients FROM recipes WHERE id IN (%s)' % ','.join(['%s'] * len(recipe_ids)),
            recipe_ids
        )
        
        results = cursor.fetchall()
        all_ingredients = []
        
        for result in results:
            ingredients = json.loads(result['ingredients'])
            all_ingredients.extend(ingredients)
            
        cursor.close()
        conn.close()
        
        return jsonify({
            'success': True,
            'ingredients': all_ingredients
        })
        
    except Exception as e:
        print(f"Error in get_ingredients: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

if __name__ == '__main__':
    init_json()
    app.run(debug=True, host='0.0.0.0', port=8080)
