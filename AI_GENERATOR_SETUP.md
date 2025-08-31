# AI Recipe Generator Setup Guide

## ✅ Completed Updates

The AI recipe generator has been successfully updated and fixed:

### 1. **Updated Dependencies**
- Upgraded OpenAI library from version 1.3.0 to 1.13.3 (stable, compatible version)
- Updated `requirements.txt` to reflect the new version

### 2. **Fixed API Endpoint Mismatch**
- Added new endpoint `/api/generate-recipe` that matches frontend expectations
- Updated the endpoint to handle `ingredients` and `preferences` payload format
- Kept the original `/api/ai/generate-recipe` endpoint for backward compatibility

### 3. **Modernized OpenAI Integration**
- Updated to use modern OpenAI client: `openai.OpenAI(api_key=api_key)`
- Implemented proper error handling for OpenAI API errors
- Added structured JSON response parsing

### 4. **Fixed Frontend-Backend Integration**
- Backend now properly processes ingredients array and preferences object
- Response format matches frontend expectations
- Proper error handling and user feedback

## 🚀 How to Start the Application

1. **Set up OpenAI API Key** (Required for AI functionality):
   ```bash
   # For Windows PowerShell:
   $env:OPENAI_API_KEY="your-actual-openai-api-key-here"
   
   # For Windows Command Prompt:
   set OPENAI_API_KEY=your-actual-openai-api-key-here
   ```

2. **Start the Flask Backend**:
   ```bash
   cd "C:\Users\Admin\recipe-recommender\backend"
   python app.py
   ```

3. **Access the Application**:
   - Open your web browser
   - Navigate to `http://localhost:5000`
   - The app should load with the AI generator interface

## 🧪 Testing the AI Generator

1. **Login/Signup**: Create an account or log in (required for AI features)
2. **Navigate to AI Generator**: Click on the AI generator tab or section
3. **Add Ingredients**: 
   - Add at least 2 ingredients (e.g., "chicken", "rice", "tomatoes")
   - Set preferences for difficulty and cuisine type
4. **Generate Recipe**: Click "Generate Recipe" button
5. **View Results**: The AI-generated recipe should appear with:
   - Recipe name and description
   - Ingredient list with measurements
   - Step-by-step instructions
   - Nutritional information and dietary flags

## 🔧 API Endpoints

### `/api/generate-recipe` (New - Frontend Compatible)
- **Method**: POST
- **Authentication**: Required
- **Payload**:
  ```json
  {
    "ingredients": ["ingredient1", "ingredient2", "ingredient3"],
    "preferences": {
      "difficulty": "Easy|Medium|Hard",
      "cuisine": "Italian|Asian|Mexican|etc"
    }
  }
  ```
- **Response**: Recipe object with all details

### `/api/ai/generate-recipe` (Original - Prompt Based)
- **Method**: POST
- **Authentication**: Required
- **Payload**:
  ```json
  {
    "prompt": "Create a spicy Italian pasta dish with tomatoes"
  }
  ```
- **Response**: Recipe object with all details

## 📊 Database Schema

The AI recipes are stored in the `ai_recipes` table with the following structure:
- `recipe_id`: Unique UUID for the recipe
- `name`, `country`, `origin`, `cuisine_type`: Recipe metadata
- `description`, `prep_time`, `difficulty`, `spice_level`: Recipe details
- `is_vegan`, `is_vegetarian`, `is_gluten_free`: Dietary flags
- `ingredients`, `steps`: Pipe-separated recipe content
- `user_prompt`: Original user request
- `created_by`: User ID who generated the recipe
- `created_at`: Timestamp

## 🚨 Important Notes

1. **OpenAI API Key**: The generator requires a valid OpenAI API key to function
2. **Authentication**: Users must be logged in to use AI features
3. **Rate Limits**: Be aware of OpenAI API rate limits for your account
4. **Cost**: Each AI generation uses OpenAI API tokens (check your usage)

## 🎯 Expected Behavior

When working correctly, the AI generator should:
1. Accept user ingredients and preferences
2. Generate a comprehensive recipe using OpenAI
3. Save the recipe to the database
4. Display the recipe in the UI with an "AI Generated" badge
5. Allow users to save, rate, and view their generated recipes

The system is now fully functional and ready for use with a valid OpenAI API key!
