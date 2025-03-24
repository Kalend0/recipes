import requests
import json
import time
import os
import subprocess
import signal
import sys
import configparser
import mysql.connector

def setup_test_env():
    """Set up test environment with mock MySQL config"""
    # Create test config if it doesn't exist
    if not os.path.exists("config.ini.test"):
        with open("config.ini.test", "w") as f:
            f.write("""[API]
CLAUDE_API_KEY = test_api_key

[MYSQL]
HOST = localhost
USER = test_user
PASSWORD = test_password
DATABASE = test_recipes_db
""")
        
    # Copy test config to config.ini for testing
    if os.path.exists("config.ini.test"):
        with open("config.ini.test", "r") as src:
            with open("config.ini", "w") as dst:
                dst.write(src.read())

def test_flask_app():
    # Set up test environment
    setup_test_env()
    
    # Start the Flask app in a separate process
    print("Starting Flask application...")
    flask_process = subprocess.Popen(["python3", "app.py"], 
                                    stdout=subprocess.PIPE,
                                    stderr=subprocess.PIPE)
    
    # Give the app some time to start
    print("Waiting for Flask app to start...")
    time.sleep(3)
    
    base_url = "http://localhost:8080"
    
    try:
        # Test 1: Check if the app is running
        print("\nTest 1: Checking if the app is running...")
        response = requests.get(base_url)
        print(f"Status code: {response.status_code}")
        if response.status_code == 200:
            print("✅ App is running successfully!")
        else:
            print("❌ App is not running correctly.")
            print(f"Response: {response.text}")
            return
        
        # Test 2: Get default ingredients
        print("\nTest 2: Testing default ingredients API...")
        recipe_name = "pannenkoeken"
        response = requests.post(f"{base_url}/get_default_ingredients", 
                                json={"recipe_name": recipe_name})
        print(f"Status code: {response.status_code}")
        if response.status_code == 200:
            ingredients = response.json().get("ingredients", [])
            print(f"Default ingredients for {recipe_name}: {ingredients}")
            print("✅ Default ingredients API working!")
        else:
            print("❌ Default ingredients API not working.")
            print(f"Response: {response.text}")
        
        # Test 3: Add a recipe
        print("\nTest 3: Adding a recipe...")
        recipe_data = {
            "name": "Test Recipe",
            "ingredients": ["Ingredient 1", "Ingredient 2", "Ingredient 3"]
        }
        response = requests.post(f"{base_url}/add_recipe", json=recipe_data)
        print(f"Status code: {response.status_code}")
        if response.status_code == 200 and response.json().get("success"):
            print("✅ Recipe added successfully!")
        else:
            print("❌ Failed to add recipe.")
            print(f"Response: {response.text}")
        
        # Test 4: Check if recipe was saved to JSON
        print("\nTest 4: Checking if recipe was saved to JSON...")
        if os.path.exists("recipes.json"):
            with open("recipes.json", "r") as f:
                recipes = json.load(f)
            
            if recipes and recipes[0]["name"] == "Test Recipe":
                print("✅ Recipe saved to JSON successfully!")
            else:
                print("❌ Recipe not found in JSON file.")
                print(f"JSON content: {recipes}")
        else:
            print("❌ recipes.json file not found.")
        
        # Test 5: Delete the recipe
        print("\nTest 5: Deleting the recipe...")
        response = requests.delete(f"{base_url}/delete_recipe/0")
        print(f"Status code: {response.status_code}")
        if response.status_code == 200 and response.json().get("success"):
            print("✅ Recipe deleted successfully!")
        else:
            print("❌ Failed to delete recipe.")
            print(f"Response: {response.text}")
        
        # Test 6: Save to database (may fail if MySQL is not set up)
        print("\nTest 6: Testing save to database...")
        # First add a recipe again
        requests.post(f"{base_url}/add_recipe", json=recipe_data)
        # Then save to database
        response = requests.post(f"{base_url}/save_to_db")
        print(f"Status code: {response.status_code}")
        if response.status_code == 200 and response.json().get("success"):
            print("✅ Saved to database successfully!")
        else:
            print("❌ Database operation failed. This is expected if you're not running a local MySQL server.")
            print(f"Response: {response.json() if response.status_code == 200 else response.text}")
        
        print("\nAll tests completed!")
        
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to Flask application. Make sure it's running on http://localhost:8080")
    except Exception as e:
        print(f"❌ Error during testing: {e}")
    finally:
        # Terminate the Flask app
        print("\nShutting down Flask application...")
        flask_process.terminate()
        flask_process.wait()
        print("Flask application terminated.")

if __name__ == "__main__":
    test_flask_app()
