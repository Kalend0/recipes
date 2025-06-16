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

# Ingredient category mapping
INGREDIENT_CATEGORIES = {
    "droge-waren": "Droge waren",
    "verse-groenten-fruit": "Verse groenten en fruit",
    "vlees-vis": "Vlees en vis",
    "zuivel": "Zuivel",
    "brood-bakkerij": "Brood en bakkerij",
    "diepvries": "Diepvries",
    "conserven": "Conserven",
    "dranken": "Dranken",
    "snacks": "Snacks",
    "ontbijt": "Ontbijt",
    "broodbeleg": "Broodbeleg",
    "baby": "Baby",
    "kruiden": "Kruiden",
    "non-food": "Non-food",
    "overig": "Overig"
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
        # Return test recipes for development
        test_recipes = [
            {'id': 1, 'name': 'Pannenkoeken'},
            {'id': 2, 'name': 'Stamppot'},
            {'id': 3, 'name': 'Erwtensoep'},
            {'id': 4, 'name': 'Bitterballen'},
            {'id': 5, 'name': 'Hutspot'},
            {'id': 6, 'name': 'Poffertjes'},
            {'id': 7, 'name': 'Appeltaart'},
            {'id': 8, 'name': 'Pasta Carbonara'},
            {'id': 9, 'name': 'Chocolate Cake'}
        ]
        return test_recipes, None
    
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
    return render_template('recipe_manager.html', recipes=recipes, categories=INGREDIENT_CATEGORIES)

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
        
        # Create mock test data for the database view
        test_recipes = [
            {
                'id': 1,
                'name': 'Chocolate Cake',
                'ingredients': ['Flour', 'Sugar', 'Cocoa', 'Eggs']
            },
            {
                'id': 2,
                'name': 'Pasta Carbonara',
                'ingredients': ['Pasta', 'Eggs', 'Pancetta', 'Parmesan']
            }
        ]
        return render_template('view_db.html', recipes=test_recipes)
    
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
        
        data = request.get_json()
        recipe_ids = data.get('recipe_ids', [])
        
        # Test recipe ingredients mapping with categories
        test_recipe_ingredients = {
            1: [{'name': 'bloem', 'category': 'droge-waren'}, {'name': 'melk', 'category': 'zuivel'}, {'name': 'eieren', 'category': 'zuivel'}, {'name': 'zout', 'category': 'kruiden'}],  # Pannenkoeken
            2: [{'name': 'aardappelen', 'category': 'verse-groenten-fruit'}, {'name': 'boerenkool', 'category': 'verse-groenten-fruit'}, {'name': 'rookworst', 'category': 'vlees-vis'}, {'name': 'spekjes', 'category': 'vlees-vis'}],  # Stamppot
            3: [{'name': 'spliterwten', 'category': 'droge-waren'}, {'name': 'varkensvlees', 'category': 'vlees-vis'}, {'name': 'prei', 'category': 'verse-groenten-fruit'}, {'name': 'wortel', 'category': 'verse-groenten-fruit'}],  # Erwtensoep
            4: [{'name': 'rundvlees', 'category': 'vlees-vis'}, {'name': 'bouillon', 'category': 'droge-waren'}, {'name': 'bloem', 'category': 'droge-waren'}, {'name': 'paneermeel', 'category': 'brood-bakkerij'}],  # Bitterballen
            5: [{'name': 'aardappelen', 'category': 'verse-groenten-fruit'}, {'name': 'wortelen', 'category': 'verse-groenten-fruit'}, {'name': 'uien', 'category': 'verse-groenten-fruit'}, {'name': 'rundvlees', 'category': 'vlees-vis'}],  # Hutspot
            6: [{'name': 'bloem', 'category': 'droge-waren'}, {'name': 'gist', 'category': 'droge-waren'}, {'name': 'melk', 'category': 'zuivel'}, {'name': 'boter', 'category': 'zuivel'}],  # Poffertjes
            7: [{'name': 'appels', 'category': 'verse-groenten-fruit'}, {'name': 'bloem', 'category': 'droge-waren'}, {'name': 'boter', 'category': 'zuivel'}, {'name': 'kaneel', 'category': 'kruiden'}],  # Appeltaart
            8: [{'name': 'pasta', 'category': 'droge-waren'}, {'name': 'eieren', 'category': 'zuivel'}, {'name': 'pancetta', 'category': 'vlees-vis'}, {'name': 'parmezaan', 'category': 'zuivel'}],  # Pasta Carbonara
            9: [{'name': 'bloem', 'category': 'droge-waren'}, {'name': 'suiker', 'category': 'droge-waren'}, {'name': 'cacao', 'category': 'droge-waren'}, {'name': 'eieren', 'category': 'zuivel'}, {'name': 'boter', 'category': 'zuivel'}]  # Chocolate Cake
        }
        
        all_ingredients = []
        for recipe_id in recipe_ids:
            if recipe_id in test_recipe_ingredients:
                all_ingredients.extend(test_recipe_ingredients[recipe_id])
        
        return jsonify({
            'success': True,
            'ingredients': all_ingredients
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

@app.route('/delete_and_export_recipe/<int:recipe_id>', methods=['POST'])
def delete_and_export_recipe(recipe_id):
    """
    Delete a recipe from the database and export it to the recipe manager JSON
    """
    if __name__ == "__main__":
        print("Remove recipe button clicked. Running in development mode - skipping database operations")
        return jsonify({'success': True, 'message': 'Development mode - database operations skipped'})
    
    try:
        # Get database connection
        conn, error = get_db_connection()
        if error:
            return jsonify({'success': False, 'error': error})
        
        cursor = conn.cursor(dictionary=True)
        
        # Fetch the recipe details before deleting
        cursor.execute('SELECT name, ingredients FROM recipes WHERE id = %s', (recipe_id,))
        recipe = cursor.fetchone()
        
        if not recipe:
            return jsonify({'success': False, 'error': 'Recipe not found'})
        
        # Delete the recipe from the database
        cursor.execute('DELETE FROM recipes WHERE id = %s', (recipe_id,))
        conn.commit()
        
        # Load existing recipes from JSON
        recipes = get_recipes()
        
        # Add the deleted recipe to the JSON
        recipes.append({
            'name': recipe['name'],
            'ingredients': json.loads(recipe['ingredients'])
        })
        
        # Save updated recipes to JSON
        save_recipes(recipes)
        
        cursor.close()
        conn.close()
        
        return jsonify({'success': True, 'recipe': recipe})
    except Exception as e:
        print(f"Error in delete_and_export_recipe: {str(e)}")
        return jsonify({'success': False, 'error': str(e)})

if __name__ == '__main__':
    init_json()
    app.run(debug=True, host='0.0.0.0', port=8080)
