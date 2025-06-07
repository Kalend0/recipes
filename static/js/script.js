document.addEventListener('DOMContentLoaded', function() {
    // DOM elements
    const recipeNameInput = document.getElementById('recipe-name');
    const ingredientsSection = document.getElementById('ingredients-section');
    const ingredientsContainer = document.getElementById('ingredients-container');
    const addRecipeBtn = document.getElementById('add-recipe-btn');
    const recipesContainer = document.getElementById('recipes-container');
    const saveDbBtn = document.getElementById('save-db-btn');
    
    // Show/hide ingredients section based on recipe name input
    recipeNameInput.addEventListener('input', () => {
        if (recipeNameInput.value.trim() !== '') {
            ingredientsSection.style.display = 'block';
        } else {
            ingredientsSection.style.display = 'none';
        }
    });
    
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

        const newSelect = document.createElement('select');
        newSelect.className = 'ingredient-category';
        newSelect.innerHTML = `
            <option value="" selected disabled style="color: #999;">Selecteer een categorie</option>
            <option value="verse-groenten-fruit">Verse groenten en fruit</option>
            <option value="vlees-vis">Vlees en vis</option>
            <option value="zuivel">Zuivel</option>
            <option value="brood-bakkerij">Brood en bakkerij</option>
            <option value="diepvries">Diepvries</option>
            <option value="conserven">Conserven</option>
            <option value="droge-waren">Droge waren</option>
            <option value="dranken">Dranken</option>
            <option value="snacks">Snacks</option>
            <option value="ontbijt">Ontbijt</option>
            <option value="broodbeleg">Broodbeleg</option>
            <option value="baby">Baby</option>
            <option value="kruiden">Kruiden</option>
            <option value="non-food">Non-food</option>
            <option value="overig">Overig</option>
        `;
        
        newRow.appendChild(newInput);
        newRow.appendChild(newSelect);
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
        const ingredientRows = ingredientsContainer.querySelectorAll('.ingredient-row');
        const ingredients = Array.from(ingredientRows)
            .map(row => {
                const name = row.querySelector('.ingredient-input').value.trim();
                const category = row.querySelector('.ingredient-category').value;
                return { name, category };
            })
            .filter(ingredient => ingredient.name !== '');
        
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
                
                // Clear form, hide ingredients section, and reset fields
                recipeNameInput.value = '';
                ingredientsSection.style.display = 'none';
                
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
            if (typeof ingredient === 'object' && ingredient.name) {
                listItem.innerHTML = `${ingredient.name} - <em>${ingredient.category}</em>`;
            } else {
                listItem.textContent = ingredient;
            }
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

        // Clear all existing ingredient rows before populating with new defaults.
        const ingredientRows = ingredientsContainer.querySelectorAll('.ingredient-row');
        ingredientRows.forEach(row => {
            row.querySelector('.ingredient-input').value = '';
            row.querySelector('.ingredient-category').value = '';
        });

        // If there are more default ingredients than rows, add new rows.
        while (ingredientsContainer.querySelectorAll('.ingredient-row').length < defaultIngredients.length) {
            addIngredientField();
        }
        
        const allIngredientRows = ingredientsContainer.querySelectorAll('.ingredient-row');
        
        // Populate rows with default ingredients.
        const numToSet = Math.min(defaultIngredients.length, allIngredientRows.length);
        for (let i = 0; i < numToSet; i++) {
            const ingredient = defaultIngredients[i];
            const row = allIngredientRows[i];
            const input = row.querySelector('.ingredient-input');
            const select = row.querySelector('.ingredient-category');

            if (typeof ingredient === 'object' && ingredient.name) {
                input.value = ingredient.name;
                const category = ingredient.category;

                if (category && category.trim() !== '' && category.toLowerCase() !== 'n/a') {
                    const optionExists = Array.from(select.options).some(o => o.value === category);
                    select.value = optionExists ? category : 'overig';
                } else {
                    select.value = 'overig';
                }
            } else { // Fallback for string-based ingredients
                input.value = String(ingredient);
                select.value = 'overig';
            }
        }

        // Ensure there is at least one empty ingredient field for manual entry.
        const allInputs = Array.from(ingredientsContainer.querySelectorAll('.ingredient-input'));
        const lastInput = allInputs[allInputs.length - 1];
        if (lastInput && lastInput.value.trim() !== '') {
            addIngredientField();
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
