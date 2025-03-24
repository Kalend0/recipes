# Recipe Manager

A Flask-based recipe management application with a minimal JavaScript frontend and Bootstrap-like styling.

## Features

- Add new recipes with name and ingredients
- Dynamic ingredient fields that expand as needed
- Default ingredient suggestions in Dutch using Claude 3.7 API
- Delete recipes with a single click
- Save recipes to a permanent MySQL database
- Temporary storage in JSON file during the session

## Requirements

- Python 3.7+
- Flask
- Anthropic Python SDK (for Claude API)
- Python-dotenv
- MySQL Connector for Python

## Setup

1. Clone or download this repository
2. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```
3. Create a `config.ini` file in the root directory (this file is not included in the repository):
   ```ini
   [MYSQL]
   HOST = yourusername.mysql.pythonanywhere-services.com
   USER = yourusername
   PASSWORD = your_mysql_password
   DATABASE = yourusername$default
   ```
   For PythonAnywhere deployment:
   - Replace `yourusername` with your PythonAnywhere username
   - Use the database credentials from your PythonAnywhere MySQL settings
   - The database name should be `yourusername$default` or another database you've created

4. Run the application:
   ```
   python3 app.py
   ```
5. Open your browser and navigate to `http://127.0.0.1:8080/`

## PythonAnywhere Setup

1. Create a new web app in your PythonAnywhere account
2. Select Flask as your framework
3. Clone this repository to your PythonAnywhere files
4. Set up a MySQL database in your PythonAnywhere account
5. Update the `config.ini` file with your PythonAnywhere MySQL credentials:
   ```
   [MYSQL]
   HOST = yourusername.mysql.pythonanywhere-services.com
   USER = yourusername
   PASSWORD = your_mysql_password
   DATABASE = yourusername$recipes
   ```
6. Configure your WSGI file to point to your app
7. Reload your web app

## Usage

1. Enter a recipe name in the "Recipe Name" field
2. The first 4 ingredient fields will be automatically populated with suggested ingredients in Dutch based on the recipe name
3. Add more ingredients as needed (a new field will appear when the last one is filled)
4. Click "Add Recipe" to add the recipe to the list
5. To delete a recipe, click the "×" button on the right side of the recipe
6. Click "Save All to Database" to permanently save all recipes to the MySQL database

## File Structure

- `app.py`: Main Flask application
- `config.ini`: Configuration file for API keys and database connection
- `recipes.json`: Temporary storage for recipes
- `templates/`: HTML templates
  - `index.html`: Main page template
  - `view_db.html`: Database view template
- `static/`: Static files
  - `css/styles.css`: CSS styles
  - `js/script.js`: JavaScript functionality

## Security

The `config.ini` file contains sensitive database credentials and is intentionally excluded from version control via `.gitignore`. Make sure to:
- Never commit this file to the repository
- Keep your database credentials secure
- Create the file manually on each deployment
