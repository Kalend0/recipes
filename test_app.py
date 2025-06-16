import requests
import json
import time
import os
import subprocess
import pytest

# Define paths relative to this script to avoid CWD issues with pytest
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(SCRIPT_DIR, "config.ini")
CONFIG_TEST_PATH = os.path.join(SCRIPT_DIR, "config.ini.test")
RECIPES_JSON_PATH = os.path.join(SCRIPT_DIR, "recipes.json")

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
            stderr=subprocess.PIPE,
            cwd=SCRIPT_DIR
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

    def setup_method(self, method):
        """Setup that runs before each test"""
        # Clean up recipes.json before each test
        with open(RECIPES_JSON_PATH, "w") as f:
            json.dump([], f)

    def test_01_index_page(self):
        """Test the main page (recipe selector) loads"""
        response = requests.get(self.base_url)
        assert response.status_code == 200
        # In development mode, should return empty recipe list
        assert "Recepten Ingrediënten Selector" in response.text

    def test_02_manager_page(self):
        """Test the recipe manager page loads"""
        response = requests.get(f"{self.base_url}/recipe_manager")
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
        with open(RECIPES_JSON_PATH, "r") as f:
            recipes = json.load(f)
        assert len(recipes) == 1
        assert recipes[0]["name"] == "Test Recipe"
        assert len(recipes[0]["ingredients"]) == 3

    def test_04_delete_recipe(self):
        """Test deleting a recipe"""
        # Add a recipe to be deleted
        recipe_data = {
            "name": "Recipe to Delete",
            "ingredients": ["A", "B"]
        }
        add_response = requests.post(f"{self.base_url}/add_recipe", json=recipe_data)
        assert add_response.status_code == 200

        # Now, delete the recipe
        response = requests.delete(f"{self.base_url}/delete_recipe/0")
        assert response.status_code == 200
        assert response.json()["success"] is True

        # Verify it was deleted from JSON
        with open(RECIPES_JSON_PATH, "r") as f:
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

    def test_08_bootstrap_navbar_functionality(self):
        """Test the functioning of the bootstrap navbar across different pages"""
        # Test navbar on index page
        response = requests.get(self.base_url)
        assert response.status_code == 200
        
        # Check for essential navbar components
        assert 'class="navbar navbar-expand-lg navbar-dark bg-dark"' in response.text
        assert 'class="navbar-brand"' in response.text
        assert 'Boodschappen' in response.text
        assert 'class="navbar-toggler"' in response.text
        assert 'data-bs-toggle="collapse"' in response.text
        assert 'data-bs-target="#navbarNavDropdown"' in response.text
        
        # Check for dropdown menu
        assert 'class="nav-item dropdown"' in response.text
        assert 'nav-link dropdown-toggle' in response.text
        assert 'role="button"' in response.text
        assert 'data-bs-toggle="dropdown"' in response.text
        assert 'Navigatie' in response.text  # Dropdown button text
        
        # Check for dropdown menu items with correct URLs
        assert 'class="dropdown-menu"' in response.text
        assert 'class="dropdown-item"' in response.text
        assert 'Recepten Selector' in response.text
        assert 'Receptenbeheer' in response.text
        assert 'Database Bekijken' in response.text
        
        # Test navbar on recipe manager page
        response = requests.get(f"{self.base_url}/recipe_manager")
        assert response.status_code == 200
        
        # Check that navbar is present with same structure
        assert 'class="navbar navbar-expand-lg navbar-dark bg-dark"' in response.text
        assert 'class="navbar-brand"' in response.text
        assert 'Boodschappen' in response.text
        assert 'class="dropdown-menu"' in response.text
        assert 'nav-link dropdown-toggle' in response.text
        
        # Check Bootstrap CSS and JS are loaded on both pages
        assert 'bootstrap@5.3.0/dist/css/bootstrap.min.css' in response.text
        assert 'bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js' in response.text
        
        # Test that the collapsible navbar structure is consistent
        index_response = requests.get(self.base_url)
        manager_response = requests.get(f"{self.base_url}/recipe_manager")
        
        # Both pages should have the same navbar structure
        for resp in [index_response, manager_response]:
            assert 'collapse navbar-collapse' in resp.text
            assert 'id="navbarNavDropdown"' in resp.text
            assert 'aria-controls="navbarNavDropdown"' in resp.text
            assert 'navbar-toggler-icon' in resp.text
        
        # Test that all navbar navigation links are accessible
        view_db_response = requests.get(f"{self.base_url}/view_db")
        assert view_db_response.status_code == 200
        assert 'Bootstrap' in view_db_response.text or 'bootstrap' in view_db_response.text
        
        # Verify navbar brand link functionality (should always go to index)
        navbar_brand_response = requests.get(self.base_url)
        assert navbar_brand_response.status_code == 200
        assert 'Selecteer recepten' in navbar_brand_response.text
        
        print("Bootstrap navbar functionality test passed successfully")

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
