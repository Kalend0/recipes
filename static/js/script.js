document.addEventListener('DOMContentLoaded', function() {
    // DOM elements
    const recipeNameInput = document.getElementById('recipe-name');
    const ingredientsContainer = document.getElementById('ingredients-container');
    const addRecipeBtn = document.getElementById('add-recipe-btn');
    const recipesContainer = document.getElementById('recipes-container');
    const saveDbBtn = document.getElementById('save-db-btn');
    
    // Initialize ingredient fields
    initIngredientFields();
    
    // Add event listeners
    addRecipeBtn.addEventListener('click', addRecipe);
    saveDbBtn.addEventListener('click', saveToDatabase);
    
    // Event delegation for delete buttons
    recipesContainer.addEventListener('click', function(e) {
        if (e.target.classList.contains('delete-btn')) {
            const recipeItem = e.target.closest('.recipe-item');
            const index = recipeItem.dataset.index;
            deleteRecipe(index);
        }
    });
    
    // Event delegation for ingredient inputs
    ingredientsContainer.addEventListener('input', function(e) {
        if (e.target.classList.contains('ingredient-input')) {
            handleIngredientInput(e.target);
        }
    });
    
    // Initialize ingredient fields with event listeners
    function initIngredientFields() {
        const inputs = ingredientsContainer.querySelectorAll('.ingredient-input');
        inputs.forEach(input => {
            input.addEventListener('input', function() {
                handleIngredientInput(this);
            });
        });
    }
    
    // Handle ingredient input - add new field when the last one is filled
    function handleIngredientInput(inputElement) {
        const allInputs = Array.from(ingredientsContainer.querySelectorAll('.ingredient-input'));
        const isLastInput = allInputs.indexOf(inputElement) === allInputs.length - 1;
        
        if (isLastInput && inputElement.value.trim() !== '') {
            addIngredientField();
        }
    }
    
    // Add a new ingredient field
    function addIngredientField() {
        const newRow = document.createElement('div');
        newRow.className = 'ingredient-row';
        
        const newInput = document.createElement('input');
        newInput.type = 'text';
        newInput.className = 'ingredient-input';
        newInput.placeholder = 'Enter ingredient';
        
        newRow.appendChild(newInput);
        ingredientsContainer.appendChild(newRow);
    }
    
    // Get default ingredients based on recipe name
    async function getDefaultIngredients(recipeName) {
        if (!recipeName) return [];
        
        try {
            const response = await fetch('/get_default_ingredients', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ recipe_name: recipeName })
            });
            
            const data = await response.json();
            return data.ingredients || [];
        } catch (error) {
            console.error('Error fetching default ingredients:', error);
            return [];
        }
    }
    
    // Add a new recipe
    async function addRecipe() {
        const recipeName = recipeNameInput.value.trim();
        if (!recipeName) {
            alert('Please enter a recipe name');
            return;
        }
        
        // Get all non-empty ingredient values
        const ingredientInputs = ingredientsContainer.querySelectorAll('.ingredient-input');
        const ingredients = Array.from(ingredientInputs)
            .map(input => input.value.trim())
            .filter(value => value !== '');
        
        if (ingredients.length === 0) {
            alert('Please add at least one ingredient');
            return;
        }
        
        // Send data to server
        try {
            const response = await fetch('/add_recipe', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    name: recipeName,
                    ingredients: ingredients
                })
            });
            
            const data = await response.json();
            if (data.success) {
                // Add recipe to UI
                addRecipeToUI(recipeName, ingredients, document.querySelectorAll('.recipe-item').length);
                
                // Clear form
                recipeNameInput.value = '';
                ingredientInputs.forEach(input => input.value = '');
                
                // Reset ingredient fields
                ingredientsContainer.innerHTML = '';
                for (let i = 0; i < 5; i++) {
                    addIngredientField();
                }
                
                // Set default values for the first 4 fields based on the new recipe name
                const newRecipeName = document.getElementById('recipe-name').value.trim();
                if (newRecipeName) {
                    setDefaultIngredients(newRecipeName);
                }
            }
        } catch (error) {
            console.error('Error adding recipe:', error);
            alert('Failed to add recipe. Please try again.');
        }
    }
    
    // Add recipe to UI
    function addRecipeToUI(name, ingredients, index) {
        const recipeItem = document.createElement('div');
        recipeItem.className = 'recipe-item';
        recipeItem.dataset.index = index;
        
        const recipeTitle = document.createElement('h3');
        recipeTitle.textContent = name;
        
        const ingredientsList = document.createElement('ul');
        ingredients.forEach(ingredient => {
            const listItem = document.createElement('li');
            listItem.textContent = ingredient;
            ingredientsList.appendChild(listItem);
        });
        
        const deleteBtn = document.createElement('button');
        deleteBtn.className = 'delete-btn';
        deleteBtn.textContent = '×';
        
        recipeItem.appendChild(recipeTitle);
        recipeItem.appendChild(ingredientsList);
        recipeItem.appendChild(deleteBtn);
        
        // Replace "No recipes" message if it exists
        const noRecipesMsg = recipesContainer.querySelector('p');
        if (noRecipesMsg) {
            recipesContainer.removeChild(noRecipesMsg);
        }
        
        recipesContainer.appendChild(recipeItem);
    }
    
    // Delete a recipe
    async function deleteRecipe(index) {
        try {
            const response = await fetch(`/delete_recipe/${index}`, {
                method: 'DELETE'
            });
            
            const data = await response.json();
            if (data.success) {
                // Remove from UI
                const recipeItem = document.querySelector(`.recipe-item[data-index="${index}"]`);
                if (recipeItem) {
                    recipesContainer.removeChild(recipeItem);
                    
                    // Update indices of remaining recipes
                    const remainingRecipes = recipesContainer.querySelectorAll('.recipe-item');
                    remainingRecipes.forEach((item, i) => {
                        item.dataset.index = i;
                    });
                    
                    // Add "No recipes" message if no recipes left
                    if (remainingRecipes.length === 0) {
                        const noRecipesMsg = document.createElement('p');
                        noRecipesMsg.textContent = 'No recipes added yet.';
                        recipesContainer.appendChild(noRecipesMsg);
                    }
                }
            }
        } catch (error) {
            console.error('Error deleting recipe:', error);
            alert('Failed to delete recipe. Please try again.');
        }
    }
    
    // Save all recipes to database
    async function saveToDatabase() {
        const recipes = recipesContainer.querySelectorAll('.recipe-item');
        if (recipes.length === 0) {
            alert('No recipes to save');
            return;
        }
        
        try {
            const response = await fetch('/save_to_db', {
                method: 'POST'
            });
            
            const data = await response.json();
            if (data.success) {
                alert('Recipes saved to database successfully');
                
                // Clear UI
                recipesContainer.innerHTML = '<p>No recipes added yet.</p>';
            }
        } catch (error) {
            console.error('Error saving to database:', error);
            alert('Failed to save recipes to database. Please try again.');
        }
    }
    
    // Set default ingredients for a recipe
    async function setDefaultIngredients(recipeName) {
        const defaultIngredients = await getDefaultIngredients(recipeName);
        const inputs = ingredientsContainer.querySelectorAll('.ingredient-input');
        
        // Set values for the first 4 fields (or fewer if not enough default ingredients)
        const numToSet = Math.min(4, defaultIngredients.length, inputs.length);
        for (let i = 0; i < numToSet; i++) {
            inputs[i].value = defaultIngredients[i];
        }
    }
    
    // Set up event listener for recipe name input to get default ingredients
    recipeNameInput.addEventListener('blur', function() {
        const recipeName = this.value.trim();
        if (recipeName) {
            setDefaultIngredients(recipeName);
        }
    });
});
