"""
Enhanced AI Assistant Service for Recipe Generation and Cooking Assistance
Uses OpenAI GPT models to provide intelligent cooking assistance, recipe generation,
and personalized recommendations.
"""

import openai
import json
import os
from typing import Dict, List, Optional, Any
import uuid
from datetime import datetime


class RecipeAIAssistant:
    """Enhanced AI Assistant for recipe generation and cooking assistance"""
    
    def __init__(self, api_key: str = None):
        """Initialize the AI assistant with OpenAI API key"""
        self.api_key = api_key or os.getenv('OPENAI_API_KEY')
        if not self.api_key:
            raise ValueError("OpenAI API key is required")
        
        self.client = openai.OpenAI(api_key=self.api_key)
        self.conversation_history = {}  # Store conversation context per user
    
    def generate_recipe_from_prompt(self, user_prompt: str, user_preferences: Dict = None) -> Dict[str, Any]:
        """Generate a recipe based on user prompt with enhanced context"""
        
        # Enhanced system prompt with better context and formatting
        system_prompt = """
You are a world-class professional chef and recipe developer with expertise in global cuisines. 
You have extensive knowledge of cooking techniques, ingredient interactions, nutritional values, and cultural food traditions.

Generate a detailed, practical recipe based on the user's request. Consider dietary restrictions, skill levels, and cultural authenticity.

Return ONLY a valid JSON object with this exact structure:

{
    "name": "Recipe Name",
    "country": "Country of Origin",
    "origin": "Specific Region/Origin",
    "cuisine_type": "Cuisine Type (e.g., Italian Traditional, Asian Fusion)",
    "description": "Brief, appetizing description of the dish",
    "prep_time": "Preparation time (e.g., '30 mins')",
    "difficulty": "Easy, Medium, or Hard",
    "spice_level": "None, Mild, Medium, or Hot",
    "is_vegan": true/false,
    "is_vegetarian": true/false,
    "is_gluten_free": true/false,
    "health_benefits": "Specific health benefits and nutritional highlights",
    "ingredients": ["1 cup ingredient with precise measurement", "2 tbsp another ingredient"],
    "steps": ["Detailed step 1 with specific techniques", "Detailed step 2 with timing and tips"],
    "cooking_tips": ["Professional tip 1", "Professional tip 2"],
    "nutritional_info": {
        "calories_per_serving": 350,
        "servings": 4,
        "protein": "25g",
        "carbs": "30g",
        "fat": "12g"
    },
    "substitutions": {
        "common_substitutions": ["If you don't have X, use Y", "For gluten-free, substitute Z"],
        "dietary_modifications": ["To make vegan: replace A with B", "For low-carb: substitute C with D"]
    }
}

Ensure ingredients have precise measurements, steps are detailed with cooking techniques and timing.
Provide helpful cooking tips and substitution suggestions.
        """
        
        # Build enhanced prompt with user preferences
        enhanced_prompt = f"Create a recipe for: {user_prompt}"
        
        if user_preferences:
            if user_preferences.get('dietary_restrictions'):
                enhanced_prompt += f"\nDietary requirements: {', '.join(user_preferences['dietary_restrictions'])}"
            if user_preferences.get('difficulty'):
                enhanced_prompt += f"\nDifficulty level: {user_preferences['difficulty']}"
            if user_preferences.get('cuisine_preference'):
                enhanced_prompt += f"\nCuisine preference: {user_preferences['cuisine_preference']}"
            if user_preferences.get('prep_time_limit'):
                enhanced_prompt += f"\nTime constraint: Maximum {user_preferences['prep_time_limit']} minutes"
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4",  # Using GPT-4 for better quality
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": enhanced_prompt}
                ],
                max_tokens=2000,
                temperature=0.7
            )
            
            ai_response = response.choices[0].message.content.strip()
            
            # Clean and parse response
            recipe_data = self._parse_ai_response(ai_response)
            
            # Add metadata
            recipe_data['generated_at'] = datetime.utcnow().isoformat()
            recipe_data['ai_model'] = "gpt-4"
            recipe_data['user_prompt'] = user_prompt
            
            return recipe_data
            
        except Exception as e:
            raise Exception(f"Recipe generation failed: {str(e)}")
    
    def generate_recipe_from_ingredients(self, ingredients: List[str], preferences: Dict = None) -> Dict[str, Any]:
        """Generate recipe from available ingredients with smart suggestions"""
        
        system_prompt = """
You are a creative professional chef who specializes in creating delicious recipes from available ingredients.
You excel at combining ingredients in innovative ways while respecting culinary traditions.

Given a list of ingredients, create a practical and delicious recipe that uses most or all of them.
Consider flavor profiles, cooking techniques, and ingredient compatibility.

Return ONLY a valid JSON object with the same structure as before, including:
- cooking_tips for best results
- substitutions for missing common ingredients
- nutritional_info estimates
- suggestions for complementary ingredients if needed

Focus on creating a balanced, flavorful dish that makes the most of the available ingredients.
        """
        
        ingredients_text = ", ".join(ingredients)
        prompt = f"Create a recipe using these available ingredients: {ingredients_text}"
        
        if preferences:
            if preferences.get('cuisine_style'):
                prompt += f"\nCuisine style preference: {preferences['cuisine_style']}"
            if preferences.get('meal_type'):
                prompt += f"\nMeal type: {preferences['meal_type']}"
            if preferences.get('difficulty'):
                prompt += f"\nDifficulty level: {preferences['difficulty']}"
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=2000,
                temperature=0.8  # Slightly higher for more creativity
            )
            
            ai_response = response.choices[0].message.content.strip()
            recipe_data = self._parse_ai_response(ai_response)
            
            # Add metadata
            recipe_data['generated_at'] = datetime.utcnow().isoformat()
            recipe_data['ai_model'] = "gpt-4"
            recipe_data['user_prompt'] = prompt
            recipe_data['source_ingredients'] = ingredients
            
            return recipe_data
            
        except Exception as e:
            raise Exception(f"Recipe generation from ingredients failed: {str(e)}")
    
    def chat_with_assistant(self, user_id: str, message: str, context: Dict = None) -> Dict[str, Any]:
        """Interactive conversation with the AI cooking assistant"""
        
        # Initialize conversation history for user if not exists
        if user_id not in self.conversation_history:
            self.conversation_history[user_id] = []
        
        system_prompt = """
You are an expert culinary assistant and professional chef with decades of experience.
You help users with all aspects of cooking including:
- Recipe suggestions and modifications
- Ingredient substitutions
- Cooking techniques and troubleshooting
- Dietary advice and nutritional information
- Meal planning and preparation tips
- Kitchen equipment recommendations
- Food safety and storage advice

Provide helpful, practical, and encouraging responses. Be conversational but professional.
When suggesting recipes, provide concise but complete information.
Always prioritize food safety and proper cooking techniques.

If asked to generate a full recipe, use the structured JSON format.
For general cooking questions, provide clear, actionable advice.
        """
        
        # Add message to conversation history
        self.conversation_history[user_id].append({"role": "user", "content": message})
        
        # Keep only last 10 messages to manage context length
        if len(self.conversation_history[user_id]) > 10:
            self.conversation_history[user_id] = self.conversation_history[user_id][-10:]
        
        # Build messages with conversation history
        messages = [{"role": "system", "content": system_prompt}]
        messages.extend(self.conversation_history[user_id])
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=messages,
                max_tokens=1000,
                temperature=0.7
            )
            
            ai_response = response.choices[0].message.content.strip()
            
            # Add AI response to conversation history
            self.conversation_history[user_id].append({"role": "assistant", "content": ai_response})
            
            return {
                "response": ai_response,
                "timestamp": datetime.utcnow().isoformat(),
                "conversation_id": user_id
            }
            
        except Exception as e:
            raise Exception(f"AI conversation failed: {str(e)}")
    
    def analyze_recipe(self, recipe_data: Dict) -> Dict[str, Any]:
        """Analyze an existing recipe and provide improvements and insights"""
        
        system_prompt = """
You are a professional chef and food scientist analyzing a recipe.
Provide constructive analysis including:
- Nutritional assessment
- Technique improvements
- Flavor enhancement suggestions
- Dietary modification options
- Time and difficulty optimization
- Potential issues and solutions

Be specific and practical in your suggestions.
        """
        
        recipe_text = f"""
Recipe: {recipe_data.get('name', 'Unknown')}
Cuisine: {recipe_data.get('cuisine_type', 'Unknown')}
Difficulty: {recipe_data.get('difficulty', 'Unknown')}
Prep Time: {recipe_data.get('prep_time', 'Unknown')}

Ingredients:
{chr(10).join(recipe_data.get('ingredients', []))}

Steps:
{chr(10).join(recipe_data.get('steps', []))}
        """
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Analyze this recipe and provide improvement suggestions:\n\n{recipe_text}"}
                ],
                max_tokens=1500,
                temperature=0.6
            )
            
            analysis = response.choices[0].message.content.strip()
            
            return {
                "analysis": analysis,
                "recipe_name": recipe_data.get('name'),
                "analyzed_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            raise Exception(f"Recipe analysis failed: {str(e)}")
    
    def get_cooking_tips(self, topic: str, skill_level: str = "beginner") -> Dict[str, Any]:
        """Generate cooking tips and techniques for specific topics"""
        
        system_prompt = f"""
You are a professional culinary instructor providing cooking education.
Provide clear, practical cooking tips and techniques for {skill_level} level cooks.

Focus on:
- Step-by-step explanations
- Common mistakes to avoid
- Professional techniques
- Food safety considerations
- Equipment recommendations
- Practical applications

Be encouraging and educational in your approach.
        """
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Provide detailed cooking tips and techniques for: {topic}"}
                ],
                max_tokens=1000,
                temperature=0.6
            )
            
            tips = response.choices[0].message.content.strip()
            
            return {
                "topic": topic,
                "skill_level": skill_level,
                "tips": tips,
                "generated_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            raise Exception(f"Cooking tips generation failed: {str(e)}")
    
    def suggest_ingredient_substitutions(self, ingredient: str, dietary_restrictions: List[str] = None) -> Dict[str, Any]:
        """Suggest ingredient substitutions based on dietary needs or availability"""
        
        system_prompt = """
You are a culinary expert specializing in ingredient substitutions and dietary modifications.
Provide practical, tested substitutions that maintain flavor and texture as much as possible.
Consider ratios, cooking behavior changes, and taste impacts.
        """
        
        restrictions_text = ""
        if dietary_restrictions:
            restrictions_text = f" considering these dietary restrictions: {', '.join(dietary_restrictions)}"
        
        prompt = f"Provide substitution options for {ingredient}{restrictions_text}. Include ratios and any cooking adjustments needed."
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=800,
                temperature=0.6
            )
            
            substitutions = response.choices[0].message.content.strip()
            
            return {
                "original_ingredient": ingredient,
                "dietary_restrictions": dietary_restrictions or [],
                "substitutions": substitutions,
                "generated_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            raise Exception(f"Substitution suggestions failed: {str(e)}")
    
    def generate_meal_plan(self, preferences: Dict, days: int = 7) -> Dict[str, Any]:
        """Generate a personalized meal plan based on user preferences"""
        
        system_prompt = """
You are a professional nutritionist and chef creating personalized meal plans.
Consider nutritional balance, variety, practical preparation, and user preferences.
Ensure meals are realistic for home cooking with proper nutritional distribution.
        """
        
        preferences_text = self._format_preferences(preferences)
        prompt = f"Create a {days}-day meal plan with the following preferences:\n{preferences_text}"
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=2500,
                temperature=0.7
            )
            
            meal_plan = response.choices[0].message.content.strip()
            
            return {
                "meal_plan": meal_plan,
                "duration_days": days,
                "preferences": preferences,
                "generated_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            raise Exception(f"Meal plan generation failed: {str(e)}")
    
    def explain_cooking_technique(self, technique: str, detail_level: str = "intermediate") -> Dict[str, Any]:
        """Provide detailed explanations of cooking techniques"""
        
        system_prompt = f"""
You are a culinary instructor explaining cooking techniques to {detail_level} level cooks.
Provide clear, comprehensive explanations including:
- Step-by-step process
- Why the technique works (science behind it)
- Common applications
- Equipment needed
- Troubleshooting common problems
- Professional tips and variations

Be educational but accessible.
        """
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Explain the cooking technique: {technique}"}
                ],
                max_tokens=1200,
                temperature=0.6
            )
            
            explanation = response.choices[0].message.content.strip()
            
            return {
                "technique": technique,
                "detail_level": detail_level,
                "explanation": explanation,
                "generated_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            raise Exception(f"Technique explanation failed: {str(e)}")
    
    def get_recipe_variations(self, base_recipe: Dict, variation_type: str = "dietary") -> Dict[str, Any]:
        """Generate recipe variations based on the original recipe"""
        
        system_prompt = """
You are a creative chef specializing in recipe adaptations and variations.
Create practical variations of existing recipes while maintaining the essence of the original dish.
Consider dietary needs, seasonal ingredients, and skill level adaptations.
        """
        
        recipe_summary = f"""
Original Recipe: {base_recipe.get('name')}
Cuisine: {base_recipe.get('cuisine_type')}
Main Ingredients: {', '.join(base_recipe.get('ingredients', [])[:5])}
Difficulty: {base_recipe.get('difficulty')}
        """
        
        prompt = f"Create {variation_type} variations of this recipe:\n{recipe_summary}\n\nProvide 3-4 practical variations with brief explanations of changes needed."
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=1200,
                temperature=0.8
            )
            
            variations = response.choices[0].message.content.strip()
            
            return {
                "original_recipe": base_recipe.get('name'),
                "variation_type": variation_type,
                "variations": variations,
                "generated_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            raise Exception(f"Recipe variations generation failed: {str(e)}")
    
    def troubleshoot_cooking_issue(self, issue_description: str, recipe_context: str = None) -> Dict[str, Any]:
        """Help troubleshoot cooking problems and provide solutions"""
        
        system_prompt = """
You are an experienced chef and cooking instructor helping to solve cooking problems.
Provide practical, immediate solutions and explain what went wrong and how to prevent it in the future.
Be encouraging and solution-focused.
        """
        
        prompt = f"Help troubleshoot this cooking issue: {issue_description}"
        if recipe_context:
            prompt += f"\n\nRecipe context: {recipe_context}"
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=800,
                temperature=0.6
            )
            
            solution = response.choices[0].message.content.strip()
            
            return {
                "issue": issue_description,
                "solution": solution,
                "recipe_context": recipe_context,
                "generated_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            raise Exception(f"Cooking troubleshooting failed: {str(e)}")
    
    def _parse_ai_response(self, ai_response: str) -> Dict[str, Any]:
        """Parse and clean AI response to extract JSON"""
        
        # Clean the response
        cleaned_response = ai_response.strip()
        
        # Remove markdown code blocks if present
        if cleaned_response.startswith('```json'):
            cleaned_response = cleaned_response[7:]
        elif cleaned_response.startswith('```'):
            cleaned_response = cleaned_response[3:]
        
        if cleaned_response.endswith('```'):
            cleaned_response = cleaned_response[:-3]
        
        try:
            return json.loads(cleaned_response.strip())
        except json.JSONDecodeError as e:
            # Try to find JSON within the response
            start_idx = cleaned_response.find('{')
            end_idx = cleaned_response.rfind('}') + 1
            
            if start_idx != -1 and end_idx != -1:
                json_part = cleaned_response[start_idx:end_idx]
                try:
                    return json.loads(json_part)
                except json.JSONDecodeError:
                    pass
            
            raise Exception(f"Failed to parse AI response as JSON: {str(e)}")
    
    def _format_preferences(self, preferences: Dict) -> str:
        """Format user preferences for AI prompt"""
        formatted = []
        
        if preferences.get('dietary_restrictions'):
            formatted.append(f"Dietary restrictions: {', '.join(preferences['dietary_restrictions'])}")
        
        if preferences.get('cuisine_preferences'):
            formatted.append(f"Preferred cuisines: {', '.join(preferences['cuisine_preferences'])}")
        
        if preferences.get('skill_level'):
            formatted.append(f"Cooking skill level: {preferences['skill_level']}")
        
        if preferences.get('time_constraint'):
            formatted.append(f"Time available: {preferences['time_constraint']}")
        
        if preferences.get('budget_level'):
            formatted.append(f"Budget level: {preferences['budget_level']}")
        
        if preferences.get('health_goals'):
            formatted.append(f"Health goals: {', '.join(preferences['health_goals'])}")
        
        return '\n'.join(formatted) if formatted else "No specific preferences provided"
    
    def clear_conversation_history(self, user_id: str):
        """Clear conversation history for a user"""
        if user_id in self.conversation_history:
            del self.conversation_history[user_id]


class RecipeImageGenerator:
    """AI-powered recipe image generation (placeholder for future DALL-E integration)"""
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv('OPENAI_API_KEY')
        self.client = openai.OpenAI(api_key=self.api_key) if self.api_key else None
    
    def generate_recipe_image(self, recipe_name: str, cuisine_type: str, description: str) -> str:
        """Generate an AI image for a recipe (future implementation with DALL-E)"""
        
        # For now, return curated food images based on cuisine type
        cuisine_images = {
            "italian": "https://images.unsplash.com/photo-1621996346565-e3dbc353d2e5?w=400&h=300&fit=crop",
            "asian": "https://images.unsplash.com/photo-1559847844-d2104c53b694?w=400&h=300&fit=crop",
            "mexican": "https://images.unsplash.com/photo-1565299624946-b28f40a0ca4b?w=400&h=300&fit=crop",
            "indian": "https://images.unsplash.com/photo-1563379091339-03246963d51a?w=400&h=300&fit=crop",
            "thai": "https://images.unsplash.com/photo-1559847844-d2104c53b694?w=400&h=300&fit=crop",
            "french": "https://images.unsplash.com/photo-1544025162-d76694265947?w=400&h=300&fit=crop",
            "american": "https://images.unsplash.com/photo-1568901346375-23c9450c58cd?w=400&h=300&fit=crop",
            "mediterranean": "https://images.unsplash.com/photo-1571197119282-7c4fe7c2f9f5?w=400&h=300&fit=crop",
            "default": "https://images.unsplash.com/photo-1556909114-f6e7ad7d3136?w=400&h=300&fit=crop"
        }
        
        # Match cuisine type to appropriate image
        cuisine_key = "default"
        for key in cuisine_images:
            if key.lower() in cuisine_type.lower():
                cuisine_key = key
                break
        
        return cuisine_images[cuisine_key]
    
    def generate_dall_e_image(self, recipe_name: str, description: str) -> str:
        """Generate custom recipe image using DALL-E (future feature)"""
        
        if not self.client:
            return self.generate_recipe_image(recipe_name, "default", description)
        
        # Future implementation with DALL-E API
        # prompt = f"Professional food photography of {recipe_name}, {description}, appetizing, well-lit, restaurant quality"
        # This would use OpenAI's image generation API when implemented
        
        return self.generate_recipe_image(recipe_name, "default", description)


# Singleton instance for the app
ai_assistant = None

def get_ai_assistant() -> RecipeAIAssistant:
    """Get or create the AI assistant instance"""
    global ai_assistant
    if ai_assistant is None:
        try:
            ai_assistant = RecipeAIAssistant()
        except ValueError as e:
            print(f"Warning: AI Assistant initialization failed: {e}")
            return None
    return ai_assistant


def get_image_generator() -> RecipeImageGenerator:
    """Get the image generator instance"""
    return RecipeImageGenerator()
