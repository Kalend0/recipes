import requests
import json
import time
import os
import subprocess
import pytest

def setup_test_env():
    """Set up test environment with mock config"""
    # Create test config if it doesn't exist
    if not os.path.exists("config.ini.test"):
        with open("config.ini.test", "w") as f:
            f.write("""[MYSQL]
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

class TestFlaskApp:
    @classmethod
    def setup_class(cls):
        """Setup that runs once before all tests"""
        setup_test_env()
        print("Starting Flask application...")
        cls.flask_process = subprocess.Popen(
            ["python3", "app.py"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        # Give the app time to start
        time.sleep(2)
        cls.base_url = "http://localhost:8080"

    @classmethod
    def teardown_class(cls):
        """Cleanup that runs once after all tests"""
        print("Shutting down Flask application...")
        cls.flask_process.terminate()
        cls.flask_process.wait()

    def test_01_index_page(self):
        """Test the main page (recipe selector) loads"""
        response = requests.get(self.base_url)
        assert response.status_code == 200
        # In development mode, should return empty recipe list
        assert "Recepten Ingrediënten Selector" in response.text

    def test_02_manager_page(self):
        """Test the recipe manager page loads"""
        response = requests.get(f"{self.base_url}/manager")
        assert response.status_code == 200
        assert "Receptenmanager" in response.text

    def test_03_add_and_get_recipe(self):
        """Test adding a recipe and retrieving it"""
        # Add a recipe
        recipe_data = {
            "name": "Test Recipe",
            "ingredients": ["Ingredient 1", "Ingredient 2", "Ingredient 3"]
        }
        response = requests.post(f"{self.base_url}/add_recipe", json=recipe_data)
        assert response.status_code == 200
        assert response.json()["success"] is True

        # Verify it was saved to JSON
        with open("recipes.json", "r") as f:
            recipes = json.load(f)
        assert len(recipes) > 0
        assert recipes[0]["name"] == "Test Recipe"
        assert len(recipes[0]["ingredients"]) == 3

    def test_04_delete_recipe(self):
        """Test deleting a recipe"""
        response = requests.delete(f"{self.base_url}/delete_recipe/0")
        assert response.status_code == 200
        assert response.json()["success"] is True

        # Verify it was deleted from JSON
        with open("recipes.json", "r") as f:
            recipes = json.load(f)
        assert len(recipes) == 0

    def test_05_default_ingredients(self):
        """Test getting default ingredients for a known recipe"""
        response = requests.post(
            f"{self.base_url}/get_default_ingredients",
            json={"recipe_name": "pannenkoeken"}
        )
        assert response.status_code == 200
        ingredients = response.json()["ingredients"]
        assert isinstance(ingredients, list)
        assert "bloem" in ingredients
        assert "eieren" in ingredients

    def test_06_save_to_db(self):
        """Test saving to database (should work in dev mode)"""
        # First add a recipe
        recipe_data = {
            "name": "Test Recipe",
            "ingredients": ["Ingredient 1", "Ingredient 2"]
        }
        requests.post(f"{self.base_url}/add_recipe", json=recipe_data)

        # Try to save to database
        response = requests.post(f"{self.base_url}/save_to_db")
        assert response.status_code == 200
        assert "Development mode" in response.json()["message"]

    def test_07_get_ingredients(self):
        """Test getting ingredients for selected recipes"""
        response = requests.post(
            f"{self.base_url}/get_ingredients",
            json={"recipe_ids": [1, 2]}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "ingredients" in data
        assert isinstance(data["ingredients"], list)
        # Should contain ingredients from both recipes
        assert len(data["ingredients"]) > 0

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
