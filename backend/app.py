from flask import Flask, request, jsonify, render_template, session, redirect, url_for
from flask_cors import CORS
from authlib.integrations.flask_client import OAuth
import sqlite3
import random
import os
import hashlib
import datetime
import requests
import json
from functools import wraps
import uuid

app = Flask(__name__, template_folder='../templates', static_folder='../static')
app.secret_key = os.getenv('SECRET_KEY', 'spice-pilot-secret-key-2024-cooking-adventures')
CORS(app)

# OAuth Configuration
oauth = OAuth(app)

# OAuth provider configurations
# Note: In production, these should be environment variables
GOOGLE_CLIENT_ID = os.getenv('GOOGLE_CLIENT_ID', 'your-google-client-id')
GOOGLE_CLIENT_SECRET = os.getenv('GOOGLE_CLIENT_SECRET', 'your-google-client-secret')
FACEBOOK_CLIENT_ID = os.getenv('FACEBOOK_CLIENT_ID', 'your-facebook-app-id')
FACEBOOK_CLIENT_SECRET = os.getenv('FACEBOOK_CLIENT_SECRET', 'your-facebook-app-secret')

# Configure Google OAuth
google = oauth.register(
    name='google',
    client_id=GOOGLE_CLIENT_ID,
    client_secret=GOOGLE_CLIENT_SECRET,
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    client_kwargs={
        'scope': 'openid email profile'
    }
)

# Configure Facebook OAuth
facebook = oauth.register(
    name='facebook',
    client_id=FACEBOOK_CLIENT_ID,
    client_secret=FACEBOOK_CLIENT_SECRET,
    access_token_url='https://graph.facebook.com/oauth/access_token',
    authorize_url='https://www.facebook.com/dialog/oauth',
    api_base_url='https://graph.facebook.com/',
    client_kwargs={'scope': 'email'}
)


# Database path
DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'database', 'recipes.db')

def get_db_connection():
    """Create and return a database connection"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_database():
    """Initialize the database with tables and sample data"""
    conn = get_db_connection()
    
    # Check if we need to migrate the database
    try:
        conn.execute('SELECT origin FROM recipes LIMIT 1')
    except sqlite3.OperationalError:
        # Database needs migration - drop and recreate
        print("🔄 Migrating database to new schema...")
        conn.execute('DROP TABLE IF EXISTS recipes')
    
    # Create users table for authentication
    conn.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT,
            first_name TEXT NOT NULL,
            last_name TEXT NOT NULL,
            oauth_provider TEXT DEFAULT NULL,
            oauth_id TEXT DEFAULT NULL,
            avatar_url TEXT DEFAULT NULL,
            cuisine_preferences TEXT DEFAULT '',
            newsletter_subscribed INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            is_active INTEGER DEFAULT 1
        )
    ''')
    
    # Create recipes table with enhanced schema
    conn.execute('''
        CREATE TABLE IF NOT EXISTS recipes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            country TEXT NOT NULL,
            origin TEXT NOT NULL,
            cuisine_type TEXT NOT NULL,
            description TEXT NOT NULL,
            image TEXT NOT NULL,
            prep_time TEXT NOT NULL,
            difficulty TEXT NOT NULL,
            spice_level TEXT NOT NULL,
            is_vegan INTEGER DEFAULT 0,
            is_vegetarian INTEGER DEFAULT 0,
            is_gluten_free INTEGER DEFAULT 0,
            health_benefits TEXT NOT NULL,
            ingredients TEXT NOT NULL,
            steps TEXT NOT NULL
        )
    ''')
    
    
    # Create recipe ratings table
    conn.execute('''
        CREATE TABLE IF NOT EXISTS recipe_ratings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            recipe_id INTEGER NOT NULL,
            recipe_type TEXT NOT NULL DEFAULT 'regular',
            user_id INTEGER NOT NULL,
            rating INTEGER NOT NULL CHECK (rating >= 1 AND rating <= 5),
            review_text TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(recipe_id, recipe_type, user_id),
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    # Check if data already exists
    existing_recipes = conn.execute('SELECT COUNT(*) FROM recipes').fetchone()[0]
    
    if existing_recipes == 0:
        # Comprehensive Kenyan food database
        kenyan_recipes = [
            {
                'name': 'Ugali',
                'country': 'Kenya',
                'origin': 'East Africa',
                'cuisine_type': 'Kenyan Traditional',
                'description': 'Kenya\'s national staple food made from white cornmeal flour',
                'image': 'https://images.unsplash.com/photo-1586511925558-a4c6376fe65f?w=400&h=300&fit=crop',
                'prep_time': '15 mins',
                'difficulty': 'Easy',
                'spice_level': 'None',
                'is_vegan': 1,
                'is_vegetarian': 1,
                'is_gluten_free': 1,
                'health_benefits': 'High in carbohydrates for energy, gluten-free, rich in fiber, provides essential minerals',
                'ingredients': '2 cups white cornmeal flour (maize flour)|3 cups water|1 tsp salt',
                'steps': 'Boil water with salt in a heavy-bottomed pot|Gradually add cornmeal flour while stirring continuously|Stir vigorously to prevent lumps from forming|Cook for 10-15 minutes, stirring constantly until thick|The ugali is ready when it pulls away from the sides of the pot|Serve hot as an accompaniment to stews and vegetables'
            },
            {
                'name': 'Nyama Choma',
                'country': 'Kenya',
                'origin': 'East Africa',
                'cuisine_type': 'Kenyan BBQ',
                'description': 'Grilled meat, typically goat or beef, seasoned with salt and roasted over open fire',
                'image': 'https://images.unsplash.com/photo-1544025162-d76694265947?w=400&h=300&fit=crop',
                'prep_time': '45 mins',
                'difficulty': 'Medium',
                'spice_level': 'Mild',
                'is_vegan': 0,
                'is_vegetarian': 0,
                'is_gluten_free': 1,
                'health_benefits': 'High in protein and iron, provides essential amino acids, rich in B vitamins',
                'ingredients': '1kg beef or goat meat|2 tsp salt|1 tsp black pepper|2 cloves garlic, minced|1 tsp ginger, minced|2 tbsp vegetable oil|Lemon juice',
                'steps': 'Cut meat into medium-sized pieces|Season with salt, pepper, garlic, and ginger|Let marinate for 30 minutes|Prepare charcoal fire or grill|Grill meat over medium heat, turning occasionally|Cook for 25-30 minutes until well done but tender|Brush with oil and lemon juice while grilling|Serve hot with ugali and vegetables'
            },
            {
                'name': 'Sukuma Wiki',
                'country': 'Kenya',
                'origin': 'East Africa',
                'cuisine_type': 'Kenyan Traditional',
                'description': 'Collard greens sautéed with onions and tomatoes, a popular vegetable dish',
                'image': 'https://images.unsplash.com/photo-1576045057995-568f588f82fb?w=400&h=300&fit=crop',
                'prep_time': '20 mins',
                'difficulty': 'Easy',
                'spice_level': 'Mild',
                'is_vegan': 1,
                'is_vegetarian': 1,
                'is_gluten_free': 1,
                'health_benefits': 'Rich in vitamins A, C, and K, high in fiber, contains antioxidants, good source of calcium',
                'ingredients': '1 bunch collard greens (sukuma wiki)|2 onions, chopped|3 tomatoes, chopped|3 cloves garlic, minced|2 tbsp vegetable oil|Salt to taste|1 tsp curry powder (optional)',
                'steps': 'Wash and chop collard greens into thin strips|Heat oil in a large pan|Sauté onions until golden brown|Add garlic and cook for 1 minute|Add tomatoes and cook until soft|Add chopped greens and stir well|Season with salt and curry powder|Cook for 10-15 minutes until greens are tender|Serve as a side dish with ugali or rice'
            },
            {
                'name': 'Githeri',
                'country': 'Kenya',
                'origin': 'Central Kenya (Kikuyu)',
                'cuisine_type': 'Kenyan Traditional',
                'description': 'Traditional Kikuyu dish of boiled maize and beans, often with vegetables',
                'image': 'https://images.unsplash.com/photo-1586511925558-a4c6376fe65f?w=400&h=300&fit=crop',
                'prep_time': '60 mins',
                'difficulty': 'Easy',
                'spice_level': 'Mild',
                'is_vegan': 1,
                'is_vegetarian': 1,
                'is_gluten_free': 1,
                'health_benefits': 'Complete protein from beans and corn combination, high in fiber, rich in folate and iron',
                'ingredients': '2 cups dried maize (corn)|1 cup kidney beans|2 onions, chopped|3 tomatoes, chopped|2 carrots, diced|2 tbsp vegetable oil|Salt to taste|2 tsp curry powder|Fresh coriander',
                'steps': 'Soak maize and beans overnight separately|Boil maize for 30 minutes until tender|Add beans and continue cooking for 20 minutes|In a separate pan, heat oil and sauté onions|Add tomatoes and carrots, cook until soft|Add curry powder and cook for 2 minutes|Combine with boiled maize and beans|Season with salt and simmer for 10 minutes|Garnish with fresh coriander before serving'
            },
            {
                'name': 'Mandazi',
                'country': 'Kenya',
                'origin': 'East Africa (Swahili Coast)',
                'cuisine_type': 'Kenyan Snack',
                'description': 'Sweet, spiced fried bread popular throughout East Africa',
                'image': 'https://images.unsplash.com/photo-1549007994-cb92caebd54b?w=400&h=300&fit=crop',
                'prep_time': '90 mins',
                'difficulty': 'Medium',
                'spice_level': 'Mild',
                'is_vegan': 0,
                'is_vegetarian': 1,
                'is_gluten_free': 0,
                'health_benefits': 'Provides energy from carbohydrates, contains small amounts of protein and healthy fats',
                'ingredients': '3 cups all-purpose flour|1/2 cup sugar|1 tsp active dry yeast|1/2 cup warm milk|2 eggs|3 tbsp melted butter|1 tsp cardamom powder|1/2 tsp salt|Oil for deep frying',
                'steps': 'Mix warm milk with yeast and a pinch of sugar, let foam for 5 minutes|In a large bowl, mix flour, sugar, cardamom, and salt|Add yeast mixture, eggs, and melted butter|Knead into a soft dough and let rise for 1 hour|Roll out dough and cut into triangular or square shapes|Heat oil to 350°F (175°C)|Deep fry mandazi until golden brown on both sides|Drain on paper towels and serve warm with tea or coffee'
            },
            {
                'name': 'Chapati',
                'country': 'Kenya',
                'origin': 'Indian-Kenyan',
                'cuisine_type': 'Kenyan-Indian',
                'description': 'Soft, layered flatbread that\'s a staple in Kenyan households',
                'image': 'https://images.unsplash.com/photo-1601050690597-df0568f70950?w=400&h=300&fit=crop',
                'prep_time': '45 mins',
                'difficulty': 'Medium',
                'spice_level': 'None',
                'is_vegan': 1,
                'is_vegetarian': 1,
                'is_gluten_free': 0,
                'health_benefits': 'Good source of carbohydrates, provides energy, contains small amounts of protein and fiber',
                'ingredients': '3 cups all-purpose flour|1 tsp salt|2 tbsp vegetable oil|1 cup warm water|Extra oil for rolling',
                'steps': 'Mix flour and salt in a large bowl|Add oil and gradually add water while mixing|Knead into a smooth, soft dough|Let rest for 30 minutes covered|Divide into 8-10 portions|Roll each portion thin, brush with oil|Roll up into a coil, then flatten and roll again|Cook on hot griddle until golden spots appear|Brush with oil while cooking|Serve warm with stew or curry'
            },
            {
                'name': 'Pilau',
                'country': 'Kenya',
                'origin': 'Swahili Coast',
                'cuisine_type': 'Kenyan-Arabic',
                'description': 'Fragrant spiced rice dish cooked with meat and aromatic spices',
                'image': 'https://images.unsplash.com/photo-1563379091339-03246963d51a?w=400&h=300&fit=crop',
                'prep_time': '60 mins',
                'difficulty': 'Medium',
                'spice_level': 'Medium',
                'is_vegan': 0,
                'is_vegetarian': 0,
                'is_gluten_free': 1,
                'health_benefits': 'Rich in protein from meat, provides complex carbohydrates, contains antioxidants from spices',
                'ingredients': '2 cups basmati rice|500g beef or chicken, cubed|2 onions, sliced|4 cloves garlic, minced|2cm ginger, minced|2 tsp pilau masala|1 tsp cumin|4 cardamom pods|2 bay leaves|3 tbsp vegetable oil|3 cups beef stock|Salt to taste|Fresh coriander',
                'steps': 'Wash and soak rice for 30 minutes|Heat oil in a heavy pot, brown meat pieces|Add onions and cook until golden|Add garlic, ginger, and all spices, cook for 2 minutes|Add drained rice and stir gently for 3 minutes|Pour in hot stock, bring to boil|Reduce heat, cover and simmer for 20 minutes|Let rest for 10 minutes before serving|Garnish with fresh coriander'
            },
            {
                'name': 'Samosas',
                'country': 'Kenya',
                'origin': 'Indian-Kenyan',
                'cuisine_type': 'Kenyan-Indian',
                'description': 'Crispy triangular pastries filled with spiced meat or vegetables',
                'image': 'https://images.unsplash.com/photo-1601050690117-94f5f6fa44d4?w=400&h=300&fit=crop',
                'prep_time': '90 mins',
                'difficulty': 'Hard',
                'spice_level': 'Medium',
                'is_vegan': 0,
                'is_vegetarian': 0,
                'is_gluten_free': 0,
                'health_benefits': 'Provides protein from meat, contains vitamins from vegetables, moderate calories',
                'ingredients': '2 cups all-purpose flour|4 tbsp oil|1/2 tsp salt|Water as needed|500g ground beef|2 onions, diced|3 cloves garlic|2 tsp garam masala|1 tsp cumin|Green chilies|Fresh coriander|Oil for frying',
                'steps': 'Make dough with flour, oil, salt, and water, knead until smooth|Let rest for 30 minutes|Cook ground beef with onions, garlic, and spices until dry|Let filling cool completely|Roll dough thin and cut into rectangles|Place filling on one end and fold into triangles|Seal edges with water|Deep fry until golden brown and crispy|Serve hot with chutney or kachumbari'
            },
            {
                'name': 'Kachumbari',
                'country': 'Kenya',
                'origin': 'East Africa',
                'cuisine_type': 'Kenyan Salad',
                'description': 'Fresh tomato and onion salad with lime and chili',
                'image': 'https://images.unsplash.com/photo-1512621776951-a57141f2eefd?w=400&h=300&fit=crop',
                'prep_time': '10 mins',
                'difficulty': 'Easy',
                'spice_level': 'Mild',
                'is_vegan': 1,
                'is_vegetarian': 1,
                'is_gluten_free': 1,
                'health_benefits': 'High in vitamin C, contains antioxidants, very low in calories, provides hydration',
                'ingredients': '4 large tomatoes, diced|2 red onions, finely chopped|2 green chilies, chopped|Juice of 2 limes|1/4 cup fresh coriander, chopped|Salt to taste|1 cucumber, diced (optional)',
                'steps': 'Dice tomatoes and place in a serving bowl|Add finely chopped onions and green chilies|Add diced cucumber if using|Pour lime juice over the vegetables|Season with salt to taste|Add fresh coriander and mix gently|Let sit for 5 minutes for flavors to blend|Serve as a side dish with nyama choma or other main dishes'
            },
            {
                'name': 'Mukimo',
                'country': 'Kenya',
                'origin': 'Central Kenya (Kikuyu)',
                'cuisine_type': 'Kenyan Traditional',
                'description': 'Mashed green vegetables with potatoes, beans, and corn',
                'image': 'https://images.unsplash.com/photo-1586511925558-a4c6376fe65f?w=400&h=300&fit=crop',
                'prep_time': '40 mins',
                'difficulty': 'Easy',
                'spice_level': 'Mild',
                'is_vegan': 1,
                'is_vegetarian': 1,
                'is_gluten_free': 1,
                'health_benefits': 'Rich in vitamins and minerals, high in fiber, provides complex carbohydrates and plant protein',
                'ingredients': '4 medium potatoes, peeled|1 cup green beans|1 cup green peas|2 cups pumpkin leaves or spinach|1 cup boiled maize|1 onion, chopped|2 tbsp vegetable oil|Salt to taste',
                'steps': 'Boil potatoes until tender|Steam or boil green beans and peas until soft|Sauté onions in oil until golden|Add all vegetables and maize to the pot|Mash everything together while still warm|Season with salt to taste|Mix until well combined but still chunky|Serve hot as a main dish or side with meat'
            },
            {
                'name': 'Fish Stew (Mchuzi wa Samaki)',
                'country': 'Kenya',
                'origin': 'Kenyan Coast (Swahili)',
                'cuisine_type': 'Kenyan Coastal',
                'description': 'Coconut fish curry popular along the Kenyan coast',
                'image': 'https://images.unsplash.com/photo-1563379091339-03246963d51a?w=400&h=300&fit=crop',
                'prep_time': '35 mins',
                'difficulty': 'Medium',
                'spice_level': 'Medium',
                'is_vegan': 0,
                'is_vegetarian': 0,
                'is_gluten_free': 1,
                'health_benefits': 'High in omega-3 fatty acids, rich in protein, contains healthy fats from coconut',
                'ingredients': '1kg white fish fillets|400ml coconut milk|2 onions, sliced|4 tomatoes, chopped|4 cloves garlic, minced|2cm ginger, minced|2 green chilies|2 tsp curry powder|1 tsp turmeric|2 tbsp vegetable oil|Salt to taste|Fresh coriander',
                'steps': 'Cut fish into large pieces and season with salt|Heat oil in a large pan, lightly fry fish pieces and set aside|Sauté onions until soft and golden|Add garlic, ginger, and chilies, cook for 2 minutes|Add tomatoes and cook until soft|Add curry powder and turmeric, cook for 1 minute|Pour in coconut milk and bring to gentle simmer|Return fish to pan and simmer for 10 minutes|Garnish with coriander and serve with rice or ugali'
            },
            {
                'name': 'Irio',
                'country': 'Kenya',
                'origin': 'Central Kenya (Kikuyu)',
                'cuisine_type': 'Kenyan Traditional',
                'description': 'Mashed potatoes mixed with green peas and corn',
                'image': 'https://images.unsplash.com/photo-1586511925558-a4c6376fe65f?w=400&h=300&fit=crop',
                'prep_time': '30 mins',
                'difficulty': 'Easy',
                'spice_level': 'None',
                'is_vegan': 1,
                'is_vegetarian': 1,
                'is_gluten_free': 1,
                'health_benefits': 'Rich in vitamin C, provides fiber and potassium, good source of plant protein from peas',
                'ingredients': '6 medium potatoes, peeled|1 cup green peas|1 cup sweet corn kernels|2 tbsp butter or oil|Salt to taste|Fresh parsley (optional)',
                'steps': 'Boil potatoes until very tender|Steam peas and corn until soft|Drain potatoes and mash while hot|Add steamed peas and corn to mashed potatoes|Add butter or oil and mix well|Season with salt to taste|Mash until well combined but leave some texture|Garnish with fresh parsley if desired|Serve hot as a side dish with meat or stew'
            },
            {
                'name': 'Maharagwe',
                'country': 'Kenya',
                'origin': 'East Africa',
                'cuisine_type': 'Kenyan Traditional',
                'description': 'Red kidney beans cooked in coconut milk with spices',
                'image': 'https://images.unsplash.com/photo-1586511925558-a4c6376fe65f?w=400&h=300&fit=crop',
                'prep_time': '75 mins',
                'difficulty': 'Easy',
                'spice_level': 'Mild',
                'is_vegan': 1,
                'is_vegetarian': 1,
                'is_gluten_free': 1,
                'health_benefits': 'High in protein and fiber, rich in folate and iron, contains healthy fats from coconut',
                'ingredients': '2 cups dried red kidney beans|400ml coconut milk|2 onions, chopped|3 tomatoes, chopped|3 cloves garlic, minced|2 tsp curry powder|1 tsp cumin|2 tbsp vegetable oil|Salt to taste|Fresh coriander',
                'steps': 'Soak beans overnight, then boil until tender (about 45 minutes)|Heat oil in a large pan, sauté onions until golden|Add garlic and cook for 1 minute|Add tomatoes and cook until soft|Add curry powder and cumin, cook for 2 minutes|Add cooked beans with some cooking liquid|Pour in coconut milk and simmer for 15 minutes|Season with salt and garnish with coriander|Serve with rice, ugali, or chapati'
            },
            {
                'name': 'Mutura',
                'country': 'Kenya',
                'origin': 'Central Kenya',
                'cuisine_type': 'Kenyan Street Food',
                'description': 'Traditional Kenyan blood sausage grilled over charcoal',
                'image': 'https://images.unsplash.com/photo-1544025162-d76694265947?w=400&h=300&fit=crop',
                'prep_time': '120 mins',
                'difficulty': 'Hard',
                'spice_level': 'Medium',
                'is_vegan': 0,
                'is_vegetarian': 0,
                'is_gluten_free': 1,
                'health_benefits': 'Very high in iron and protein, rich in B vitamins, provides essential minerals',
                'ingredients': 'Cow or goat intestines (cleaned)|2 cups fresh blood|1 cup minced meat|2 onions, finely chopped|4 cloves garlic, minced|2 tsp ginger, minced|2 tsp curry powder|1 tsp black pepper|Salt to taste|Fresh coriander',
                'steps': 'Clean intestines thoroughly with salt and lemon|Mix blood with minced meat, onions, garlic, ginger|Add spices and mix well|Stuff mixture into cleaned intestines|Tie ends securely with string|Boil gently for 45 minutes|Remove and let cool slightly|Grill over charcoal until crispy outside|Slice and serve hot with kachumbari'
            },
            {
                'name': 'Matoke',
                'country': 'Kenya',
                'origin': 'East Africa',
                'cuisine_type': 'Kenyan Traditional',
                'description': 'Green bananas cooked with meat and spices in a hearty stew',
                'image': 'https://images.unsplash.com/photo-1586511925558-a4c6376fe65f?w=400&h=300&fit=crop',
                'prep_time': '50 mins',
                'difficulty': 'Medium',
                'spice_level': 'Medium',
                'is_vegan': 0,
                'is_vegetarian': 0,
                'is_gluten_free': 1,
                'health_benefits': 'Rich in potassium and vitamin B6, high in fiber, provides sustained energy from complex carbs',
                'ingredients': '8 green bananas (matoke)|500g beef, cubed|2 onions, chopped|3 tomatoes, chopped|3 cloves garlic, minced|2 tsp curry powder|1 tsp cumin|2 tbsp vegetable oil|2 cups beef stock|Salt to taste|Fresh coriander',
                'steps': 'Peel and cut green bananas into chunks|Brown meat in oil until golden|Add onions and cook until soft|Add garlic and spices, cook for 2 minutes|Add tomatoes and cook until soft|Add banana chunks and gently mix|Pour in stock to barely cover|Cover and simmer for 25 minutes until bananas are tender|Season with salt and garnish with coriander|Serve hot as a complete meal'
            },
            {
                'name': 'Bhajia',
                'country': 'Kenya',
                'origin': 'Indian-Kenyan',
                'cuisine_type': 'Kenyan-Indian',
                'description': 'Spiced potato fritters popular as a snack or appetizer',
                'image': 'https://images.unsplash.com/photo-1601050690597-df0568f70950?w=400&h=300&fit=crop',
                'prep_time': '30 mins',
                'difficulty': 'Medium',
                'spice_level': 'Medium',
                'is_vegan': 1,
                'is_vegetarian': 1,
                'is_gluten_free': 0,
                'health_benefits': 'Provides energy from potatoes, contains antioxidants from spices, good source of potassium',
                'ingredients': '4 large potatoes, thinly sliced|2 cups chickpea flour (besan)|1 tsp turmeric|2 tsp coriander seeds, ground|1 tsp cumin seeds|2 green chilies, minced|1 tsp ginger-garlic paste|Salt to taste|Water as needed|Oil for deep frying',
                'steps': 'Slice potatoes very thinly and soak in salted water|Mix chickpea flour with all spices and salt|Add water gradually to make a thick batter|Drain potato slices and pat dry|Heat oil to 350°F (175°C)|Dip potato slices in batter and deep fry until golden|Fry in small batches to avoid overcrowding|Drain on paper towels|Serve hot with chutney or tomato sauce'
            },
            {
                'name': 'Kunde',
                'country': 'Kenya',
                'origin': 'East Africa',
                'cuisine_type': 'Kenyan Traditional',
                'description': 'Black-eyed peas cooked with coconut milk and spices',
                'image': 'https://images.unsplash.com/photo-1586511925558-a4c6376fe65f?w=400&h=300&fit=crop',
                'prep_time': '60 mins',
                'difficulty': 'Easy',
                'spice_level': 'Mild',
                'is_vegan': 1,
                'is_vegetarian': 1,
                'is_gluten_free': 1,
                'health_benefits': 'High in protein and fiber, rich in folate, contains antioxidants, good source of potassium',
                'ingredients': '2 cups dried black-eyed peas|400ml coconut milk|2 onions, chopped|3 tomatoes, chopped|3 cloves garlic, minced|2 tsp curry powder|2 tbsp vegetable oil|Salt to taste|Fresh coriander',
                'steps': 'Soak black-eyed peas overnight|Boil until tender, about 30 minutes|Heat oil in a pan, sauté onions until golden|Add garlic and cook for 1 minute|Add tomatoes and cook until soft|Add curry powder and cook for 2 minutes|Add cooked peas with some cooking liquid|Pour in coconut milk and simmer for 10 minutes|Season with salt and garnish with coriander|Serve with ugali or rice'
            },
            {
                'name': 'Maandazi (Sweet Version)',
                'country': 'Kenya',
                'origin': 'East Africa (Swahili Coast)',
                'cuisine_type': 'Kenyan Dessert',
                'description': 'Sweet coconut-flavored fried bread, often eaten as a snack or dessert',
                'image': 'https://images.unsplash.com/photo-1549007994-cb92caebd54b?w=400&h=300&fit=crop',
                'prep_time': '90 mins',
                'difficulty': 'Medium',
                'spice_level': 'Mild',
                'is_vegan': 0,
                'is_vegetarian': 1,
                'is_gluten_free': 0,
                'health_benefits': 'Provides quick energy, contains healthy fats from coconut, moderate protein content',
                'ingredients': '3 cups all-purpose flour|1/2 cup sugar|1 tsp active dry yeast|200ml coconut milk|2 eggs|3 tbsp melted butter|1 tsp cardamom powder|1/2 tsp salt|1 tsp vanilla extract|Oil for frying',
                'steps': 'Warm coconut milk slightly and mix with yeast and 1 tbsp sugar|Let foam for 5 minutes|Mix flour, remaining sugar, cardamom, and salt|Add yeast mixture, eggs, melted butter, and vanilla|Knead into soft dough and let rise for 1 hour|Roll out and cut into desired shapes|Heat oil to 350°F (175°C)|Deep fry until golden brown|Dust with powdered sugar and serve warm'
            },
            {
                'name': 'Terere',
                'country': 'Kenya',
                'origin': 'Central Kenya',
                'cuisine_type': 'Kenyan Traditional',
                'description': 'Amaranth greens cooked with onions and tomatoes',
                'image': 'https://images.unsplash.com/photo-1576045057995-568f588f82fb?w=400&h=300&fit=crop',
                'prep_time': '20 mins',
                'difficulty': 'Easy',
                'spice_level': 'Mild',
                'is_vegan': 1,
                'is_vegetarian': 1,
                'is_gluten_free': 1,
                'health_benefits': 'Extremely high in vitamins A and C, rich in iron and calcium, contains powerful antioxidants',
                'ingredients': '2 bunches amaranth greens (terere)|2 onions, chopped|3 tomatoes, chopped|3 cloves garlic, minced|2 tbsp vegetable oil|Salt to taste|1 green chili (optional)',
                'steps': 'Wash and chop amaranth greens|Heat oil in a large pan|Sauté onions until golden|Add garlic and green chili, cook for 1 minute|Add tomatoes and cook until soft|Add chopped greens and stir well|Cover and cook for 10 minutes until greens are tender|Season with salt to taste|Serve with ugali, rice, or chapati'
            },
            {
                'name': 'Viazi Karai',
                'country': 'Kenya',
                'origin': 'Kenyan Coast',
                'cuisine_type': 'Kenyan Street Food',
                'description': 'Spiced potato curry, a popular street food snack',
                'image': 'https://images.unsplash.com/photo-1601050690597-df0568f70950?w=400&h=300&fit=crop',
                'prep_time': '30 mins',
                'difficulty': 'Easy',
                'spice_level': 'Medium',
                'is_vegan': 1,
                'is_vegetarian': 1,
                'is_gluten_free': 1,
                'health_benefits': 'Good source of potassium and vitamin C, provides complex carbohydrates, contains antioxidants from spices',
                'ingredients': '6 medium potatoes, cubed|2 onions, chopped|3 tomatoes, chopped|4 cloves garlic, minced|2cm ginger, minced|2 tsp curry powder|1 tsp turmeric|1 tsp cumin|2 green chilies|3 tbsp vegetable oil|Salt to taste|Fresh coriander',
                'steps': 'Boil potatoes until just tender, don\'t overcook|Heat oil in a large pan|Sauté onions until golden brown|Add garlic, ginger, and green chilies|Add tomatoes and cook until soft|Add all spices and cook for 2 minutes|Add boiled potatoes and mix gently|Simmer for 10 minutes until flavors blend|Garnish with fresh coriander|Serve hot as a snack or with bread'
            },
            {
                'name': 'Wali wa Nazi',
                'country': 'Kenya',
                'origin': 'Kenyan Coast (Swahili)',
                'cuisine_type': 'Kenyan Coastal',
                'description': 'Coconut rice, a fragrant coastal staple',
                'image': 'https://images.unsplash.com/photo-1586511925558-a4c6376fe65f?w=400&h=300&fit=crop',
                'prep_time': '30 mins',
                'difficulty': 'Easy',
                'spice_level': 'Mild',
                'is_vegan': 1,
                'is_vegetarian': 1,
                'is_gluten_free': 1,
                'health_benefits': 'Provides complex carbohydrates, contains healthy fats from coconut, good source of energy',
                'ingredients': '2 cups basmati rice|400ml coconut milk|2 cups water|1 tsp salt|1 cinnamon stick|3 cardamom pods|2 cloves|1 tbsp vegetable oil',
                'steps': 'Wash rice until water runs clear|Heat oil in a heavy-bottomed pot|Add whole spices and fry for 1 minute|Add rice and stir for 2 minutes|Add coconut milk, water, and salt|Bring to boil, then reduce heat to low|Cover and simmer for 18 minutes|Turn off heat and let rest for 10 minutes|Fluff with a fork before serving|Serve with fish curry or vegetable dishes'
            },
            {
                'name': 'Smokies (Kenyan Style)',
                'country': 'Kenya',
                'origin': 'Urban Kenya',
                'cuisine_type': 'Kenyan Street Food',
                'description': 'Grilled sausages served with kachumbari and ugali',
                'image': 'https://images.unsplash.com/photo-1544025162-d76694265947?w=400&h=300&fit=crop',
                'prep_time': '20 mins',
                'difficulty': 'Easy',
                'spice_level': 'Mild',
                'is_vegan': 0,
                'is_vegetarian': 0,
                'is_gluten_free': 1,
                'health_benefits': 'Good source of protein, provides essential amino acids and B vitamins',
                'ingredients': '8 beef or pork sausages|2 tbsp vegetable oil|1 batch kachumbari|Ugali for serving|Tomato sauce (optional)',
                'steps': 'Heat oil in a large pan or use a grill|Cook sausages over medium heat, turning frequently|Grill for 15-20 minutes until golden brown and cooked through|Meanwhile, prepare fresh kachumbari|Slice sausages diagonally if desired|Serve hot with kachumbari and ugali|Add tomato sauce on the side if preferred'
            },
            {
                'name': 'Chai (Kenyan Tea)',
                'country': 'Kenya',
                'origin': 'East Africa',
                'cuisine_type': 'Kenyan Beverage',
                'description': 'Spiced milk tea that\'s a daily staple in Kenyan households',
                'image': 'https://images.unsplash.com/photo-1571934811356-5cc061b6821f?w=400&h=300&fit=crop',
                'prep_time': '10 mins',
                'difficulty': 'Easy',
                'spice_level': 'Mild',
                'is_vegan': 0,
                'is_vegetarian': 1,
                'is_gluten_free': 1,
                'health_benefits': 'Contains antioxidants from tea, provides calcium from milk, spices aid digestion',
                'ingredients': '2 cups water|2 cups whole milk|4 tsp black tea leaves|4 tsp sugar|4 cardamom pods, crushed|1 cinnamon stick|2 cloves|1cm ginger, sliced',
                'steps': 'Bring water to boil in a saucepan|Add all spices and ginger, boil for 2 minutes|Add tea leaves and boil for 2 minutes|Add milk and sugar|Bring to boil, then simmer for 3-4 minutes|Strain into cups through a fine mesh|Serve hot with mandazi or biscuits'
            }
        ]
        
        # West African recipes (additional to existing)
        west_african_recipes = [
            {
                'name': 'Egusi Soup',
                'country': 'Nigeria',
                'origin': 'West Africa',
                'cuisine_type': 'Nigerian Traditional',
                'description': 'Rich soup made with ground melon seeds, leafy greens, and meat',
                'image': 'https://images.unsplash.com/photo-1559847844-5315695dadae?w=400&h=300&fit=crop',
                'prep_time': '60 mins',
                'difficulty': 'Medium',
                'spice_level': 'Medium',
                'is_vegan': 0,
                'is_vegetarian': 0,
                'is_gluten_free': 1,
                'health_benefits': 'High in protein, rich in vitamins A and C, contains healthy fats from seeds, provides iron',
                'ingredients': '2 cups ground egusi (melon seeds)|500g assorted meat (beef, goat)|1 cup palm oil|2 onions, chopped|4 cloves garlic, minced|2 tbsp locust beans (iru)|4 cups spinach or bitter leaf|2 stock cubes|3 cups water|Scotch bonnet peppers|Salt to taste',
                'steps': 'Season and boil meat until tender|Heat palm oil in large pot|Fry meat pieces until browned|Add onions and garlic, cook until soft|Add locust beans and cook for 2 minutes|Mix egusi with small amount of stock to form paste|Add egusi paste to pot and stir well|Add remaining stock and bring to boil|Simmer for 20 minutes, stirring occasionally|Add leafy greens and cook for 5 minutes|Season with salt and pepper|Serve with pounded yam or fufu'
            },
            {
                'name': 'Kelewele',
                'country': 'Ghana',
                'origin': 'West Africa',
                'cuisine_type': 'Ghanaian Street Food',
                'description': 'Spiced fried plantain cubes, a popular Ghanaian snack',
                'image': 'https://images.unsplash.com/photo-1601050690597-df0568f70950?w=400&h=300&fit=crop',
                'prep_time': '20 mins',
                'difficulty': 'Easy',
                'spice_level': 'Medium',
                'is_vegan': 1,
                'is_vegetarian': 1,
                'is_gluten_free': 1,
                'health_benefits': 'Rich in potassium and vitamin A, provides natural sugars for energy, contains antioxidants',
                'ingredients': '4 ripe plantains|2 tsp ginger, minced|2 cloves garlic, minced|1 tsp nutmeg|1 tsp cinnamon|1/2 tsp cloves, ground|1 tsp salt|1/2 tsp cayenne pepper|Oil for deep frying',
                'steps': 'Peel plantains and cut into 1-inch cubes|Mix all spices with salt in a large bowl|Toss plantain cubes with spice mixture|Let marinate for 10 minutes|Heat oil to 350°F (175°C)|Fry plantains in batches until golden brown|Remove with slotted spoon|Drain on paper towels|Serve hot as a snack or side dish|Can be enjoyed with groundnut soup'
            },
            {
                'name': 'Banku',
                'country': 'Ghana',
                'origin': 'West Africa',
                'cuisine_type': 'Ghanaian Traditional',
                'description': 'Fermented corn and cassava dough cooked into a smooth paste',
                'image': 'https://images.unsplash.com/photo-1586511925558-a4c6376fe65f?w=400&h=300&fit=crop',
                'prep_time': '45 mins + fermentation',
                'difficulty': 'Medium',
                'spice_level': 'None',
                'is_vegan': 1,
                'is_vegetarian': 1,
                'is_gluten_free': 1,
                'health_benefits': 'Good source of carbohydrates, naturally fermented for gut health, provides energy',
                'ingredients': '2 cups fermented corn dough|1 cup cassava dough|4-5 cups water|Salt to taste',
                'steps': 'Mix corn and cassava dough in large bowl|Gradually add water to form smooth paste|Strain mixture to remove lumps|Bring to boil in heavy pot, stirring constantly|Reduce heat and continue stirring vigorously|Cook for 20-30 minutes until very thick and smooth|The banku is ready when it doesn\'t stick to pot|Shape into portions with wet hands|Serve hot with grilled fish and pepper sauce'
            },
            {
                'name': 'Moi Moi',
                'country': 'Nigeria',
                'origin': 'West Africa',
                'cuisine_type': 'Nigerian Traditional',
                'description': 'Steamed bean pudding made from black-eyed peas',
                'image': 'https://images.unsplash.com/photo-1586511925558-a4c6376fe65f?w=400&h=300&fit=crop',
                'prep_time': '90 mins',
                'difficulty': 'Medium',
                'spice_level': 'Mild',
                'is_vegan': 1,
                'is_vegetarian': 1,
                'is_gluten_free': 1,
                'health_benefits': 'High in protein and fiber, rich in folate, provides plant-based iron, contains antioxidants',
                'ingredients': '3 cups black-eyed peas (soaked and peeled)|1 red bell pepper|1 onion|3 cloves garlic|2 tsp ginger|1/2 cup palm oil|2 stock cubes|1 tsp salt|1 cup warm water|Banana leaves or foil for wrapping',
                'steps': 'Soak beans overnight and remove skins|Blend beans with peppers, onion, garlic, ginger|Add just enough water to make smooth paste|Season with salt and stock cubes|Gradually add palm oil while mixing|Mix until well combined and fluffy|Wrap portions in banana leaves or foil|Steam for 45-60 minutes until firm|Test with toothpick - should come out clean|Serve hot as main dish or side|Can be eaten with bread or rice'
            },
            {
                'name': 'Plantain Fufu',
                'country': 'Ghana',
                'origin': 'West Africa',
                'cuisine_type': 'Ghanaian Traditional',
                'description': 'Smooth, stretchy fufu made from boiled plantains',
                'image': 'https://images.unsplash.com/photo-1586511925558-a4c6376fe65f?w=400&h=300&fit=crop',
                'prep_time': '30 mins',
                'difficulty': 'Medium',
                'spice_level': 'None',
                'is_vegan': 1,
                'is_vegetarian': 1,
                'is_gluten_free': 1,
                'health_benefits': 'Rich in potassium and vitamin B6, provides complex carbohydrates, contains dietary fiber',
                'ingredients': '8 green plantains|2 cups cassava flour|Water as needed|Salt to taste',
                'steps': 'Peel and cut plantains into chunks|Boil plantains until very tender|Drain and mash while hot|Gradually add cassava flour while pounding|Add small amounts of warm water as needed|Pound until smooth and stretchy|The fufu should be elastic and not sticky|Form into balls and serve immediately|Traditionally eaten with soup or stew|Use hands to pinch off pieces and dip in soup'
            }
        ]
        
        # Other African recipes
        other_african_recipes = west_african_recipes + [
            {
                'name': 'Jollof Rice',
                'country': 'Nigeria',
                'origin': 'West Africa',
                'cuisine_type': 'Nigerian Traditional',
                'description': 'One-pot rice dish cooked in tomato sauce with spices and vegetables',
                'image': 'https://images.unsplash.com/photo-1563379091339-03246963d51a?w=400&h=300&fit=crop',
                'prep_time': '45 mins',
                'difficulty': 'Medium',
                'spice_level': 'Medium',
                'is_vegan': 1,
                'is_vegetarian': 1,
                'is_gluten_free': 1,
                'health_benefits': 'Rich in lycopene from tomatoes, provides complex carbohydrates, contains antioxidants from spices',
                'ingredients': '3 cups long-grain rice|400ml tomato puree|2 onions, chopped|4 cloves garlic, minced|2cm ginger, minced|2 tsp curry powder|1 tsp thyme|2 bay leaves|3 tbsp vegetable oil|3 cups chicken or vegetable stock|Salt and pepper to taste|Green bell pepper|Scotch bonnet pepper (optional)',
                'steps': 'Wash rice until water runs clear|Heat oil in a large pot, sauté onions until golden|Add garlic and ginger, cook for 2 minutes|Add tomato puree and cook for 10 minutes until reduced|Add spices, bay leaves, and cook for 2 minutes|Add rice and stir to coat with sauce|Pour in stock, bring to boil|Add bell pepper, reduce heat and simmer covered for 20 minutes|Let rest 10 minutes before serving|Garnish with fresh herbs'
            },
            {
                'name': 'Tagine',
                'country': 'Morocco',
                'origin': 'North Africa',
                'cuisine_type': 'Moroccan Traditional',
                'description': 'Slow-cooked stew with meat, vegetables, and aromatic spices',
                'image': 'https://images.unsplash.com/photo-1544025162-d76694265947?w=400&h=300&fit=crop',
                'prep_time': '90 mins',
                'difficulty': 'Medium',
                'spice_level': 'Medium',
                'is_vegan': 0,
                'is_vegetarian': 0,
                'is_gluten_free': 1,
                'health_benefits': 'High in protein, rich in antioxidants from spices, contains healthy fats, provides vitamins from vegetables',
                'ingredients': '1kg lamb or chicken, cubed|2 onions, sliced|3 carrots, sliced|2 tsp ginger, minced|4 cloves garlic, minced|2 tsp cinnamon|1 tsp turmeric|1 tsp cumin|1/2 cup dried apricots|1/4 cup almonds|3 tbsp olive oil|2 cups chicken stock|Fresh coriander|Salt and pepper',
                'steps': 'Heat oil in tagine or heavy pot|Brown meat pieces on all sides|Add onions and cook until soft|Add garlic, ginger, and all spices|Cook for 2 minutes until fragrant|Add carrots, apricots, and stock|Bring to boil, then reduce heat|Cover and simmer for 60 minutes until meat is tender|Add almonds in last 10 minutes|Garnish with fresh coriander|Serve with couscous or bread'
            },
            {
                'name': 'Bobotie',
                'country': 'South Africa',
                'origin': 'South Africa',
                'cuisine_type': 'South African Traditional',
                'description': 'Spiced mince meat dish topped with egg custard and baked',
                'image': 'https://images.unsplash.com/photo-1544025162-d76694265947?w=400&h=300&fit=crop',
                'prep_time': '75 mins',
                'difficulty': 'Medium',
                'spice_level': 'Medium',
                'is_vegan': 0,
                'is_vegetarian': 0,
                'is_gluten_free': 0,
                'health_benefits': 'High in protein, provides essential amino acids, contains antioxidants from spices',
                'ingredients': '500g ground beef or lamb|2 onions, chopped|2 slices white bread|1 cup milk|2 eggs|2 tbsp curry powder|1 tsp turmeric|2 tbsp chutney|2 tbsp vinegar|1/4 cup raisins|2 tbsp almonds, chopped|2 bay leaves|Salt and pepper',
                'steps': 'Preheat oven to 180°C (350°F)|Soak bread in milk, then squeeze out excess|Brown mince in a large pan|Add onions and cook until soft|Add spices and cook for 2 minutes|Add soaked bread, chutney, vinegar, raisins|Mix well and transfer to baking dish|Beat eggs with remaining milk|Pour egg mixture over meat|Top with bay leaves|Bake for 45 minutes until golden|Serve with yellow rice and chutney'
            },
            {
                'name': 'Injera',
                'country': 'Ethiopia',
                'origin': 'East Africa (Ethiopia)',
                'cuisine_type': 'Ethiopian Traditional',
                'description': 'Spongy sourdough flatbread made from teff flour',
                'image': 'https://images.unsplash.com/photo-1601050690597-df0568f70950?w=400&h=300&fit=crop',
                'prep_time': '72 hours (fermentation)',
                'difficulty': 'Hard',
                'spice_level': 'None',
                'is_vegan': 1,
                'is_vegetarian': 1,
                'is_gluten_free': 1,
                'health_benefits': 'High in protein and fiber, rich in iron and calcium, naturally fermented for gut health',
                'ingredients': '4 cups teff flour|4 cups water|1/2 cup starter (optional)|Additional water for thinning',
                'steps': 'Mix teff flour with water to form smooth batter|Cover and let ferment at room temperature for 3 days|Stir daily and add water if needed|Batter should smell sour and bubbly|Boil 1 cup of batter with 3 cups water until thick|Cool and mix back into main batter|Heat non-stick pan over medium heat|Pour thin layer of batter onto pan|Cover and cook until surface is dry and edges lift|Do not flip - cook only one side|Stack cooked injera with cloth between layers'
            },
            {
                'name': 'Couscous',
                'country': 'Morocco',
                'origin': 'North Africa',
                'cuisine_type': 'Moroccan Traditional',
                'description': 'Steamed semolina grain served with vegetables and meat',
                'image': 'https://images.unsplash.com/photo-1586511925558-a4c6376fe65f?w=400&h=300&fit=crop',
                'prep_time': '45 mins',
                'difficulty': 'Medium',
                'spice_level': 'Mild',
                'is_vegan': 0,
                'is_vegetarian': 0,
                'is_gluten_free': 0,
                'health_benefits': 'Good source of protein and fiber, provides B vitamins, contains selenium for immune support',
                'ingredients': '2 cups couscous|500g lamb or chicken|3 carrots, sliced|2 zucchini, sliced|1 onion, quartered|2 tomatoes, quartered|1 tsp cinnamon|1 tsp ginger|1 tsp turmeric|3 tbsp olive oil|4 cups water or stock|Salt to taste|Fresh herbs',
                'steps': 'Place couscous in steamer basket|Steam over boiling water for 20 minutes|Meanwhile, brown meat in oil|Add onions and cook until soft|Add spices and cook for 2 minutes|Add vegetables and enough water to cover|Simmer for 30 minutes until tender|Fluff couscous with fork and add oil|Steam couscous again for 15 minutes|Serve couscous with vegetables and meat on top'
            },
            {
                'name': 'Bunny Chow',
                'country': 'South Africa',
                'origin': 'South Africa (Durban)',
                'cuisine_type': 'South African Fusion',
                'description': 'Curry served in a hollowed-out loaf of bread',
                'image': 'https://images.unsplash.com/photo-1563379091339-03246963d51a?w=400&h=300&fit=crop',
                'prep_time': '60 mins',
                'difficulty': 'Medium',
                'spice_level': 'Hot',
                'is_vegan': 0,
                'is_vegetarian': 0,
                'is_gluten_free': 0,
                'health_benefits': 'High in protein from meat, provides carbohydrates from bread, contains antioxidants from spices',
                'ingredients': '1 unsliced white bread loaf|500g mutton or chicken, cubed|2 onions, chopped|4 tomatoes, chopped|4 cloves garlic, minced|2cm ginger, minced|3 tbsp curry powder|1 tsp garam masala|2 green chilies|3 tbsp oil|1 cup water|Salt to taste|Fresh coriander',
                'steps': 'Cut bread loaf in half and hollow out centers|Brown meat in oil until sealed|Add onions and cook until golden|Add garlic, ginger, chilies and spices|Cook for 3 minutes until fragrant|Add tomatoes and cook until soft|Add water and simmer for 30 minutes until meat is tender|Season with salt|Fill bread halves with curry|Garnish with coriander|Serve immediately while hot'
            },
            {
                'name': 'Fufu',
                'country': 'Ghana',
                'origin': 'West Africa',
                'cuisine_type': 'Ghanaian Traditional',
                'description': 'Starchy staple made from cassava and plantain, served with soup',
                'image': 'https://images.unsplash.com/photo-1586511925558-a4c6376fe65f?w=400&h=300&fit=crop',
                'prep_time': '40 mins',
                'difficulty': 'Medium',
                'spice_level': 'None',
                'is_vegan': 1,
                'is_vegetarian': 1,
                'is_gluten_free': 1,
                'health_benefits': 'High in carbohydrates for energy, good source of fiber, provides potassium and vitamin C',
                'ingredients': '2 cups cassava flour|1 cup plantain flour|3-4 cups water|Pinch of salt',
                'steps': 'Boil water with salt in a large pot|Gradually add cassava flour while stirring continuously|Stir vigorously to prevent lumps|Add plantain flour gradually|Continue stirring until mixture is smooth and thick|Cook for 15-20 minutes, stirring constantly|The fufu is ready when it becomes very thick and stretchy|Serve hot with soup or stew|Traditionally eaten by hand, pinched off and dipped in soup'
            },
            {
                'name': 'Biltong',
                'country': 'South Africa',
                'origin': 'South Africa',
                'cuisine_type': 'South African Snack',
                'description': 'Air-dried seasoned meat, similar to jerky but with unique spicing',
                'image': 'https://images.unsplash.com/photo-1544025162-d76694265947?w=400&h=300&fit=crop',
                'prep_time': '7 days (drying time)',
                'difficulty': 'Hard',
                'spice_level': 'Mild',
                'is_vegan': 0,
                'is_vegetarian': 0,
                'is_gluten_free': 1,
                'health_benefits': 'Very high in protein, low in fat, rich in iron and B vitamins, long shelf life',
                'ingredients': '2kg beef silverside|200g coarse salt|2 tbsp coriander seeds, crushed|2 tbsp black pepper|1 tbsp brown sugar|2 tbsp vinegar',
                'steps': 'Cut meat into long strips with the grain|Mix salt, coriander, pepper, and sugar|Rub spice mixture into meat strips|Hang in vinegar for 1 minute|Hang strips in well-ventilated, dry area|Ensure good air circulation around meat|Dry for 5-7 days depending on thickness|Test for dryness - should be firm but not hard|Slice thinly against the grain to serve|Store in airtight container'
            },
            {
                'name': 'Thieboudienne',
                'country': 'Senegal',
                'origin': 'West Africa',
                'cuisine_type': 'Senegalese Traditional',
                'description': 'National dish of Senegal - fish and rice with vegetables',
                'image': 'https://images.unsplash.com/photo-1563379091339-03246963d51a?w=400&h=300&fit=crop',
                'prep_time': '90 mins',
                'difficulty': 'Hard',
                'spice_level': 'Medium',
                'is_vegan': 0,
                'is_vegetarian': 0,
                'is_gluten_free': 1,
                'health_benefits': 'High in omega-3 fatty acids, rich in protein, provides vitamins from vegetables',
                'ingredients': '1kg white fish fillets|3 cups jasmine rice|2 onions, quartered|3 carrots, sliced|2 eggplants, cubed|1 cabbage, quartered|4 tomatoes, chopped|6 cloves garlic|2cm ginger|2 tbsp tomato paste|3 tbsp palm oil|Scotch bonnet pepper|Parsley|Thyme|Salt to taste',
                'steps': 'Make a paste with garlic, ginger, and herbs|Stuff fish with paste and season|Brown fish in oil and set aside|Sauté onions until golden|Add tomato paste and cook for 5 minutes|Add tomatoes and cook until soft|Add enough water to cover rice|Add vegetables in order of cooking time|Return fish to pot|Simmer for 45 minutes until rice is cooked|Serve fish and vegetables over rice'
            },
            {
                'name': 'Doro Wat',
                'country': 'Ethiopia',
                'origin': 'East Africa (Ethiopia)',
                'cuisine_type': 'Ethiopian Traditional',
                'description': 'Spicy chicken stew with hard-boiled eggs and berbere spice',
                'image': 'https://images.unsplash.com/photo-1544025162-d76694265947?w=400&h=300&fit=crop',
                'prep_time': '120 mins',
                'difficulty': 'Hard',
                'spice_level': 'Hot',
                'is_vegan': 0,
                'is_vegetarian': 0,
                'is_gluten_free': 1,
                'health_benefits': 'High in protein, rich in iron, contains antioxidants from spices, provides healthy fats',
                'ingredients': '1 whole chicken, cut into pieces|6 hard-boiled eggs|3 large onions, chopped|4 cloves garlic, minced|2cm ginger, minced|3 tbsp berbere spice blend|2 tbsp paprika|1/4 cup red wine|3 tbsp clarified butter|2 cups chicken stock|Salt to taste',
                'steps': 'Dry roast onions in heavy pot until caramelized (30 mins)|Add garlic and ginger, cook 5 minutes|Add berbere and paprika, cook 2 minutes|Add wine and cook until evaporated|Add butter and chicken pieces|Brown chicken well on all sides|Add stock gradually while stirring|Simmer covered for 45 minutes|Add peeled hard-boiled eggs|Simmer 15 minutes more|Serve with injera bread'
            },
            {
                'name': 'Bunny Suya',
                'country': 'Nigeria',
                'origin': 'West Africa (Northern Nigeria)',
                'cuisine_type': 'Nigerian Street Food',
                'description': 'Spicy grilled meat skewers with peanut spice mix',
                'image': 'https://images.unsplash.com/photo-1544025162-d76694265947?w=400&h=300&fit=crop',
                'prep_time': '45 mins',
                'difficulty': 'Medium',
                'spice_level': 'Hot',
                'is_vegan': 0,
                'is_vegetarian': 0,
                'is_gluten_free': 1,
                'health_benefits': 'High in protein, contains healthy fats from peanuts, rich in antioxidants from spices',
                'ingredients': '1kg beef, cut into cubes|1 cup roasted peanuts, ground|2 tsp ginger powder|2 tsp garlic powder|1 tsp cayenne pepper|1 tsp paprika|1 tsp onion powder|Salt to taste|Vegetable oil|Wooden skewers',
                'steps': 'Soak wooden skewers in water for 30 minutes|Mix ground peanuts with all spices and salt|Thread meat onto skewers|Brush meat with oil|Sprinkle suya spice mix generously over meat|Let marinate for 20 minutes|Grill over medium-high heat for 15-20 minutes|Turn frequently and baste with oil|Sprinkle more spice mix before serving|Serve hot with sliced onions and tomatoes'
            },
            {
                'name': 'Pap en Vleis',
                'country': 'South Africa',
                'origin': 'South Africa',
                'cuisine_type': 'South African Traditional',
                'description': 'Maize porridge served with grilled meat, a staple combination',
                'image': 'https://images.unsplash.com/photo-1586511925558-a4c6376fe65f?w=400&h=300&fit=crop',
                'prep_time': '40 mins',
                'difficulty': 'Easy',
                'spice_level': 'Mild',
                'is_vegan': 0,
                'is_vegetarian': 0,
                'is_gluten_free': 1,
                'health_benefits': 'Provides sustained energy from complex carbs, high in protein from meat, contains essential minerals',
                'ingredients': '2 cups white maize meal|4 cups water|1 tsp salt|1kg beef steak or boerewors|2 tbsp vegetable oil|Black pepper|Salt for seasoning meat',
                'steps': 'Bring water and salt to boil in heavy pot|Gradually add maize meal while stirring|Stir continuously to prevent lumps|Cook for 25-30 minutes, stirring regularly|Meanwhile, season meat with salt and pepper|Grill meat over medium-high heat|Cook steak for 4-5 minutes per side|Or grill boerewors for 15-20 minutes, turning frequently|Let meat rest before slicing|Serve hot pap with grilled meat alongside'
            }
        ]
        
        # Famous European recipes
        european_recipes = [
            {
                'name': 'Pasta Carbonara',
                'country': 'Italy',
                'origin': 'Central Italy (Rome)',
                'cuisine_type': 'Italian Traditional',
                'description': 'Classic Roman pasta with eggs, cheese, pancetta, and black pepper',
                'image': 'https://images.unsplash.com/photo-1621996346565-e3dbc353d2e5?w=400&h=300&fit=crop',
                'prep_time': '20 mins',
                'difficulty': 'Medium',
                'spice_level': 'Mild',
                'is_vegan': 0,
                'is_vegetarian': 0,
                'is_gluten_free': 0,
                'health_benefits': 'High in protein from eggs and pancetta, provides energy from pasta, contains calcium from cheese',
                'ingredients': '400g spaghetti|200g pancetta, diced|4 large eggs|100g Parmesan cheese, grated|2 cloves garlic, minced|Freshly ground black pepper|2 tbsp olive oil|Salt for pasta water',
                'steps': 'Bring large pot of salted water to boil|Cook spaghetti according to package directions|Meanwhile, heat oil in large pan|Cook pancetta until crispy|Add garlic and cook for 1 minute|Beat eggs with Parmesan and black pepper|Drain pasta, reserving 1 cup pasta water|Add hot pasta to pancetta pan|Remove from heat and quickly stir in egg mixture|Add pasta water gradually until creamy|Serve immediately with extra Parmesan and pepper'
            },
            {
                'name': 'Paella',
                'country': 'Spain',
                'origin': 'Valencia, Spain',
                'cuisine_type': 'Spanish Traditional',
                'description': 'Saffron-infused rice dish with seafood, chicken, and vegetables',
                'image': 'https://images.unsplash.com/photo-1534080564583-6be75777b70a?w=400&h=300&fit=crop',
                'prep_time': '60 mins',
                'difficulty': 'Hard',
                'spice_level': 'Mild',
                'is_vegan': 0,
                'is_vegetarian': 0,
                'is_gluten_free': 1,
                'health_benefits': 'High in protein from seafood, rich in omega-3 fatty acids, contains antioxidants from saffron',
                'ingredients': '2 cups bomba or short-grain rice|500g mixed seafood (mussels, prawns, squid)|400g chicken thighs|1 red bell pepper|1 cup green beans|4 cups chicken stock|Pinch of saffron|4 cloves garlic, minced|2 tomatoes, grated|4 tbsp olive oil|Salt and pepper|Lemon wedges|Fresh parsley',
                'steps': 'Heat olive oil in large paella pan|Season and brown chicken pieces, set aside|Sauté bell pepper and green beans, set aside|Cook garlic and tomatoes until thick|Add rice and stir for 2 minutes|Heat stock with saffron in separate pot|Add hot stock to rice, bring to boil|Return chicken and vegetables to pan|Simmer for 10 minutes without stirring|Add seafood in last 8 minutes|Let rest for 5 minutes before serving|Garnish with parsley and lemon'
            },
            {
                'name': 'Fish and Chips',
                'country': 'United Kingdom',
                'origin': 'England',
                'cuisine_type': 'British Traditional',
                'description': 'Beer-battered fish with thick-cut chips, a British classic',
                'image': 'https://images.unsplash.com/photo-1544025162-d76694265947?w=400&h=300&fit=crop',
                'prep_time': '45 mins',
                'difficulty': 'Medium',
                'spice_level': 'None',
                'is_vegan': 0,
                'is_vegetarian': 0,
                'is_gluten_free': 0,
                'health_benefits': 'High in protein and omega-3 fatty acids, provides carbohydrates from potatoes',
                'ingredients': '4 large cod fillets|1kg large potatoes|2 cups all-purpose flour|1 bottle beer|1 tsp baking powder|Salt and pepper|Vegetable oil for frying|Mushy peas and tartar sauce for serving',
                'steps': 'Cut potatoes into thick chips and soak in cold water|Heat oil to 140°C, fry chips for 5 minutes|Remove and drain on paper towels|Make batter with flour, beer, baking powder, and salt|Heat oil to 180°C|Dip fish in flour, then batter|Fry fish for 4-5 minutes until golden|Fry chips again at 180°C until crispy|Season with salt and serve with mushy peas|Add malt vinegar and tartar sauce'
            },
            {
                'name': 'Coq au Vin',
                'country': 'France',
                'origin': 'Burgundy, France',
                'cuisine_type': 'French Traditional',
                'description': 'Chicken braised in red wine with mushrooms and bacon',
                'image': 'https://images.unsplash.com/photo-1544025162-d76694265947?w=400&h=300&fit=crop',
                'prep_time': '90 mins',
                'difficulty': 'Medium',
                'spice_level': 'Mild',
                'is_vegan': 0,
                'is_vegetarian': 0,
                'is_gluten_free': 0,
                'health_benefits': 'High in protein, contains antioxidants from red wine, provides B vitamins',
                'ingredients': '1 whole chicken, cut into pieces|200g bacon, diced|500ml red wine|250g mushrooms, quartered|12 small onions|3 cloves garlic, minced|2 tbsp flour|2 tbsp butter|2 bay leaves|Fresh thyme|2 tbsp olive oil|Salt and pepper|Fresh parsley',
                'steps': 'Season chicken pieces with salt and pepper|Heat oil in heavy pot, brown chicken and set aside|Cook bacon until crispy, set aside|Sauté onions and mushrooms until golden|Add garlic and cook for 1 minute|Sprinkle flour and cook for 2 minutes|Gradually add wine, stirring constantly|Return chicken and bacon to pot|Add herbs and bring to simmer|Cover and cook for 45 minutes until tender|Serve with mashed potatoes and crusty bread'
            },
            {
                'name': 'Wiener Schnitzel',
                'country': 'Austria',
                'origin': 'Austria',
                'cuisine_type': 'Austrian Traditional',
                'description': 'Breaded and fried veal cutlet, a classic Austrian dish',
                'image': 'https://images.unsplash.com/photo-1544025162-d76694265947?w=400&h=300&fit=crop',
                'prep_time': '30 mins',
                'difficulty': 'Medium',
                'spice_level': 'None',
                'is_vegan': 0,
                'is_vegetarian': 0,
                'is_gluten_free': 0,
                'health_benefits': 'High in protein and iron, provides essential amino acids and B vitamins',
                'ingredients': '4 veal cutlets, pounded thin|2 cups breadcrumbs|2 eggs, beaten|1/2 cup flour|Vegetable oil for frying|Salt and pepper|Lemon wedges|Fresh parsley',
                'steps': 'Pound veal cutlets until very thin|Season with salt and pepper|Set up breading station: flour, beaten eggs, breadcrumbs|Dredge cutlets in flour, then egg, then breadcrumbs|Press coating gently to adhere|Heat oil in large skillet to 350°F|Fry schnitzels for 2-3 minutes per side until golden|Drain on paper towels|Serve immediately with lemon wedges|Traditionally served with potato salad and lingonberry sauce'
            },
            {
                'name': 'Moussaka',
                'country': 'Greece',
                'origin': 'Greece',
                'cuisine_type': 'Greek Traditional',
                'description': 'Layered casserole with eggplant, meat sauce, and béchamel',
                'image': 'https://images.unsplash.com/photo-1563379091339-03246963d51a?w=400&h=300&fit=crop',
                'prep_time': '120 mins',
                'difficulty': 'Hard',
                'spice_level': 'Mild',
                'is_vegan': 0,
                'is_vegetarian': 0,
                'is_gluten_free': 0,
                'health_benefits': 'High in protein, contains fiber from eggplant, provides calcium from cheese and milk',
                'ingredients': '3 large eggplants, sliced|500g ground lamb|2 onions, chopped|400ml canned tomatoes|3 cloves garlic, minced|1 tsp cinnamon|1/2 cup red wine|For béchamel: 4 tbsp butter|4 tbsp flour|2 cups milk|100g cheese, grated|2 egg yolks|Olive oil|Salt and pepper',
                'steps': 'Slice eggplants, salt and let drain 30 minutes|Brush with oil and grill until golden|Brown lamb with onions and garlic|Add tomatoes, wine, cinnamon, simmer 20 minutes|Make béchamel: melt butter, add flour, gradually add milk|Whisk until thick, add cheese and egg yolks|Layer eggplant, meat sauce, repeat|Top with béchamel sauce|Bake at 180°C for 45 minutes until golden|Let rest 10 minutes before serving'
            },
            {
                'name': 'Ratatouille',
                'country': 'France',
                'origin': 'Provence, France',
                'cuisine_type': 'French Traditional',
                'description': 'Traditional vegetable stew from southern France',
                'image': 'https://images.unsplash.com/photo-1576045057995-568f588f82fb?w=400&h=300&fit=crop',
                'prep_time': '60 mins',
                'difficulty': 'Easy',
                'spice_level': 'Mild',
                'is_vegan': 1,
                'is_vegetarian': 1,
                'is_gluten_free': 1,
                'health_benefits': 'Rich in vitamins and antioxidants, high in fiber, low in calories, provides potassium',
                'ingredients': '2 eggplants, cubed|4 zucchini, sliced|4 tomatoes, chopped|2 bell peppers, sliced|1 large onion, sliced|4 cloves garlic, minced|4 tbsp olive oil|2 tsp herbes de Provence|1 bay leaf|Salt and pepper|Fresh basil',
                'steps': 'Heat olive oil in large heavy pot|Sauté onion until translucent|Add garlic and cook 1 minute|Add eggplant and cook for 5 minutes|Add bell peppers and zucchini|Add tomatoes, herbs, bay leaf|Season with salt and pepper|Simmer covered for 30 minutes|Stir occasionally until vegetables are tender|Remove bay leaf|Garnish with fresh basil|Serve as side dish or main with bread'
            }
        ]
        
        # Combine all African recipes
        all_african_recipes = kenyan_recipes + other_african_recipes
        
        # Popular Asian recipes
        asian_recipes = [
            {
                'name': 'Pad Thai',
                'country': 'Thailand',
                'origin': 'Thailand',
                'cuisine_type': 'Thai Traditional',
                'description': 'Stir-fried rice noodles with sweet, sour, and savory flavors',
                'image': 'https://images.unsplash.com/photo-1559847844-d2104c53b694?w=400&h=300&fit=crop',
                'prep_time': '30 mins',
                'difficulty': 'Medium',
                'spice_level': 'Medium',
                'is_vegan': 0,
                'is_vegetarian': 0,
                'is_gluten_free': 1,
                'health_benefits': 'Good source of protein, contains vitamin E from peanuts, provides complex carbohydrates',
                'ingredients': '400g rice noodles|200g shrimp or chicken|3 eggs|1 cup bean sprouts|3 cloves garlic, minced|3 tbsp fish sauce|2 tbsp tamarind paste|2 tbsp palm sugar|3 tbsp vegetable oil|1/4 cup peanuts, crushed|2 green onions, chopped|1 lime, cut in wedges|Chili flakes',
                'steps': 'Soak rice noodles in warm water until soft|Heat oil in large wok or pan|Scramble eggs and set aside|Stir-fry garlic until fragrant|Add shrimp or chicken, cook until done|Add drained noodles and sauce ingredients|Toss everything together for 2-3 minutes|Add bean sprouts and scrambled eggs|Stir-fry for another minute|Garnish with peanuts, green onions, lime|Serve immediately while hot'
            },
            {
                'name': 'Sushi',
                'country': 'Japan',
                'origin': 'Japan',
                'cuisine_type': 'Japanese Traditional',
                'description': 'Vinegared rice with fresh fish and vegetables',
                'image': 'https://images.unsplash.com/photo-1579952363873-27d3bfaa0103?w=400&h=300&fit=crop',
                'prep_time': '60 mins',
                'difficulty': 'Hard',
                'spice_level': 'None',
                'is_vegan': 0,
                'is_vegetarian': 0,
                'is_gluten_free': 1,
                'health_benefits': 'High in omega-3 fatty acids, low in calories, provides high-quality protein, contains iodine',
                'ingredients': '2 cups sushi rice|3 cups water|1/4 cup rice vinegar|2 tbsp sugar|1 tsp salt|200g sashimi-grade fish|Nori sheets|Wasabi|Pickled ginger|Soy sauce|1 cucumber|1 avocado',
                'steps': 'Rinse rice until water runs clear|Cook rice with water in rice cooker|Mix vinegar, sugar, and salt|When rice is done, add vinegar mixture and cool|Cut fish into thin slices|Wet hands and form rice into oval shapes|Top with fish slice and small dab of wasabi|For maki: place nori on bamboo mat|Spread rice, add fillings, roll tightly|Cut with sharp wet knife|Serve with soy sauce, wasabi, and ginger'
            },
            {
                'name': 'Butter Chicken',
                'country': 'India',
                'origin': 'North India (Delhi)',
                'cuisine_type': 'Indian Traditional',
                'description': 'Creamy tomato-based curry with tender chicken pieces',
                'image': 'https://images.unsplash.com/photo-1563379091339-03246963d51a?w=400&h=300&fit=crop',
                'prep_time': '60 mins',
                'difficulty': 'Medium',
                'spice_level': 'Medium',
                'is_vegan': 0,
                'is_vegetarian': 0,
                'is_gluten_free': 1,
                'health_benefits': 'High in protein, contains antioxidants from tomatoes and spices, provides healthy fats',
                'ingredients': '1kg chicken, cubed|400ml canned tomatoes|200ml heavy cream|1 onion, chopped|4 cloves garlic, minced|2cm ginger, minced|2 tsp garam masala|1 tsp turmeric|1 tsp cumin|2 tbsp butter|2 tbsp oil|Salt to taste|Fresh coriander|Basmati rice for serving',
                'steps': 'Marinate chicken with salt, turmeric for 30 minutes|Heat oil in large pan, brown chicken and set aside|Melt butter, sauté onions until golden|Add garlic and ginger, cook 2 minutes|Add tomatoes and spices, cook 10 minutes|Blend sauce until smooth if desired|Return to pan, add chicken|Simmer for 15 minutes|Add cream and simmer 5 minutes more|Garnish with coriander|Serve with basmati rice and naan'
            },
            {
                'name': 'Fried Rice',
                'country': 'China',
                'origin': 'China',
                'cuisine_type': 'Chinese Traditional',
                'description': 'Wok-fried rice with vegetables, eggs, and choice of protein',
                'image': 'https://images.unsplash.com/photo-1563379091339-03246963d51a?w=400&h=300&fit=crop',
                'prep_time': '20 mins',
                'difficulty': 'Easy',
                'spice_level': 'Mild',
                'is_vegan': 0,
                'is_vegetarian': 0,
                'is_gluten_free': 0,
                'health_benefits': 'Provides complex carbohydrates, good source of protein from eggs, contains vitamins from vegetables',
                'ingredients': '4 cups cooked jasmine rice (day-old)|3 eggs, beaten|200g cooked chicken or shrimp|1 cup mixed vegetables (peas, carrots, corn)|3 cloves garlic, minced|2 green onions, chopped|3 tbsp soy sauce|2 tbsp vegetable oil|1 tsp sesame oil|White pepper to taste',
                'steps': 'Heat oil in large wok or pan over high heat|Scramble eggs and set aside|Add more oil if needed|Stir-fry garlic until fragrant|Add cooked protein and vegetables|Stir-fry for 2 minutes|Add cold rice, breaking up clumps|Stir-fry for 3-4 minutes|Add soy sauce and sesame oil|Return eggs to pan and mix|Garnish with green onions|Serve immediately while hot'
            },
            {
                'name': 'Pho',
                'country': 'Vietnam',
                'origin': 'North Vietnam',
                'cuisine_type': 'Vietnamese Traditional',
                'description': 'Aromatic noodle soup with herbs, meat, and fragrant broth',
                'image': 'https://images.unsplash.com/photo-1559847844-5315695dadae?w=400&h=300&fit=crop',
                'prep_time': '180 mins',
                'difficulty': 'Hard',
                'spice_level': 'Mild',
                'is_vegan': 0,
                'is_vegetarian': 0,
                'is_gluten_free': 1,
                'health_benefits': 'Rich in protein and collagen, contains antioxidants from herbs, provides essential amino acids',
                'ingredients': '400g rice noodles|1kg beef bones|500g beef brisket|1 onion, halved|5cm ginger|4 star anise|1 cinnamon stick|4 cloves|1 tbsp coriander seeds|Fish sauce to taste|Rock sugar|200g raw beef, thinly sliced|Bean sprouts|Thai basil|Cilantro|Lime wedges|Chili slices',
                'steps': 'Char onion and ginger over open flame until blackened|Roast spices in dry pan until fragrant|Boil bones and brisket for 3 hours with aromatics|Strain broth and season with fish sauce and sugar|Cook rice noodles according to package directions|Slice raw beef paper-thin|Place noodles in bowls, top with raw beef|Ladle boiling broth over to cook beef|Serve with fresh herbs, bean sprouts, lime|Add chili and extra fish sauce to taste'
            },
            {
                'name': 'Ramen',
                'country': 'Japan',
                'origin': 'Japan',
                'cuisine_type': 'Japanese Traditional',
                'description': 'Rich noodle soup with various toppings and flavorful broth',
                'image': 'https://images.unsplash.com/photo-1559847844-5315695dadae?w=400&h=300&fit=crop',
                'prep_time': '240 mins',
                'difficulty': 'Hard',
                'spice_level': 'Mild',
                'is_vegan': 0,
                'is_vegetarian': 0,
                'is_gluten_free': 0,
                'health_benefits': 'High in protein, contains B vitamins, provides essential amino acids, rich in minerals',
                'ingredients': '4 portions fresh ramen noodles|1kg pork bones|500g pork belly|4 eggs|2 onions|6 cloves garlic|5cm ginger|Miso paste|Soy sauce|Mirin|Green onions|Nori sheets|Bamboo shoots|Corn kernels',
                'steps': 'Simmer pork bones for 4 hours to make rich broth|Cook pork belly until tender, slice thin|Soft-boil eggs for 6 minutes, marinate in soy sauce|Prepare toppings: slice green onions, corn, bamboo shoots|Cook ramen noodles according to package directions|Season broth with miso, soy sauce, and mirin|Place noodles in bowls|Ladle hot broth over noodles|Top with pork belly, egg, and vegetables|Garnish with nori and green onions'
            },
            {
                'name': 'Biryani',
                'country': 'India',
                'origin': 'Indian Subcontinent',
                'cuisine_type': 'Indian Traditional',
                'description': 'Fragrant layered rice dish with spiced meat and aromatic spices',
                'image': 'https://images.unsplash.com/photo-1563379091339-03246963d51a?w=400&h=300&fit=crop',
                'prep_time': '90 mins',
                'difficulty': 'Hard',
                'spice_level': 'Medium',
                'is_vegan': 0,
                'is_vegetarian': 0,
                'is_gluten_free': 1,
                'health_benefits': 'High in protein, contains antioxidants from spices, provides complex carbohydrates',
                'ingredients': '3 cups basmati rice|1kg mutton or chicken|1 cup yogurt|2 onions, sliced|6 cloves garlic|3cm ginger|4 green chilies|1 tsp turmeric|2 tsp red chili powder|1 tsp garam masala|Saffron soaked in milk|4 tbsp ghee|Fresh mint|Coriander|Salt to taste',
                'steps': 'Marinate meat with yogurt and spices for 2 hours|Fry onions until golden and crispy|Cook rice 70% done with whole spices|Cook marinated meat until tender|Layer rice and meat in heavy pot|Sprinkle fried onions, herbs, saffron milk|Cover with foil, then lid|Cook on high heat 3 minutes, then low for 45 minutes|Let rest 10 minutes before opening|Gently mix and serve with raita and boiled eggs'
            },
            {
                'name': 'Tom Yum Soup',
                'country': 'Thailand',
                'origin': 'Thailand',
                'cuisine_type': 'Thai Traditional',
                'description': 'Hot and sour soup with shrimp and aromatic herbs',
                'image': 'https://images.unsplash.com/photo-1559847844-5315695dadae?w=400&h=300&fit=crop',
                'prep_time': '25 mins',
                'difficulty': 'Medium',
                'spice_level': 'Hot',
                'is_vegan': 0,
                'is_vegetarian': 0,
                'is_gluten_free': 1,
                'health_benefits': 'Low in calories, rich in antioxidants, contains vitamin C, supports immune system',
                'ingredients': '500g large shrimp|4 cups chicken stock|3 lemongrass stalks|4 kaffir lime leaves|3cm galangal, sliced|4 bird\'s eye chilies|200g mushrooms|3 tomatoes, quartered|3 tbsp fish sauce|2 tbsp lime juice|1 tbsp palm sugar|Fresh cilantro',
                'steps': 'Bring stock to boil in large pot|Add lemongrass, galangal, lime leaves|Simmer for 10 minutes to infuse flavors|Add mushrooms and tomatoes|Cook for 5 minutes|Add shrimp and chilies|Cook until shrimp turn pink|Season with fish sauce, lime juice, sugar|Taste and adjust seasoning|Remove lemongrass before serving|Garnish with fresh cilantro|Serve hot with jasmine rice'
            }
        ]
        
        # Famous American recipes
        american_recipes = [
            {
                'name': 'BBQ Ribs',
                'country': 'USA',
                'origin': 'Southern United States',
                'cuisine_type': 'American BBQ',
                'description': 'Slow-cooked pork ribs with smoky barbecue sauce',
                'image': 'https://images.unsplash.com/photo-1544025162-d76694265947?w=400&h=300&fit=crop',
                'prep_time': '240 mins',
                'difficulty': 'Medium',
                'spice_level': 'Medium',
                'is_vegan': 0,
                'is_vegetarian': 0,
                'is_gluten_free': 1,
                'health_benefits': 'High in protein and iron, provides B vitamins, contains zinc for immune support',
                'ingredients': '2kg pork ribs|2 tbsp brown sugar|2 tbsp paprika|1 tbsp garlic powder|1 tbsp onion powder|1 tsp cayenne pepper|2 tsp salt|1 tsp black pepper|BBQ sauce|Apple cider vinegar|Liquid smoke (optional)',
                'steps': 'Mix all dry spices to make rub|Coat ribs generously with spice rub|Let marinate for 2 hours or overnight|Preheat oven to 275°F (135°C)|Wrap ribs in foil with apple cider vinegar|Bake for 2.5 hours until tender|Remove foil and brush with BBQ sauce|Increase heat to 425°F (220°C)|Bake 15 minutes more until caramelized|Let rest 10 minutes before cutting|Serve with extra BBQ sauce and coleslaw'
            },
            {
                'name': 'Tacos',
                'country': 'Mexico',
                'origin': 'Mexico',
                'cuisine_type': 'Mexican Traditional',
                'description': 'Soft or hard shell tortillas filled with seasoned meat and toppings',
                'image': 'https://images.unsplash.com/photo-1565299624946-b28f40a0ca4b?w=400&h=300&fit=crop',
                'prep_time': '30 mins',
                'difficulty': 'Easy',
                'spice_level': 'Medium',
                'is_vegan': 0,
                'is_vegetarian': 0,
                'is_gluten_free': 1,
                'health_benefits': 'Good source of protein, contains fiber from beans, provides vitamins from vegetables',
                'ingredients': '500g ground beef or chicken|12 corn tortillas|1 onion, diced|3 cloves garlic, minced|2 tsp chili powder|1 tsp cumin|1 tsp paprika|Salt and pepper|Lettuce, shredded|Tomatoes, diced|Cheese, grated|Sour cream|Salsa|Lime wedges',
                'steps': 'Brown ground meat in large skillet|Add onions and garlic, cook until soft|Add spices and cook for 2 minutes|Season with salt and pepper|Warm tortillas in dry pan or microwave|Fill tortillas with meat mixture|Top with lettuce, tomatoes, cheese|Add sour cream and salsa|Serve with lime wedges|Offer hot sauce on the side'
            },
            {
                'name': 'Hamburger',
                'country': 'USA',
                'origin': 'United States',
                'cuisine_type': 'American Classic',
                'description': 'Grilled beef patty served in a bun with classic toppings',
                'image': 'https://images.unsplash.com/photo-1568901346375-23c9450c58cd?w=400&h=300&fit=crop',
                'prep_time': '25 mins',
                'difficulty': 'Easy',
                'spice_level': 'Mild',
                'is_vegan': 0,
                'is_vegetarian': 0,
                'is_gluten_free': 0,
                'health_benefits': 'High in protein and iron, provides B vitamins, contains essential amino acids',
                'ingredients': '600g ground beef (80/20)|4 hamburger buns|4 slices cheese|1 large tomato, sliced|1 onion, sliced|Lettuce leaves|Pickles|Ketchup|Mustard|Mayonnaise|Salt and pepper',
                'steps': 'Form ground beef into 4 equal patties|Season both sides with salt and pepper|Heat grill or skillet to medium-high heat|Cook patties 4-5 minutes per side for medium|Add cheese in last minute of cooking|Toast buns lightly on grill|Assemble burgers: bottom bun, sauce, lettuce|Add patty with cheese, tomato, onion, pickles|Top with more sauce and top bun|Serve immediately with fries'
            },
            {
                'name': 'Mac and Cheese',
                'country': 'USA',
                'origin': 'United States',
                'cuisine_type': 'American Comfort Food',
                'description': 'Creamy baked macaroni pasta with cheese sauce',
                'image': 'https://images.unsplash.com/photo-1621996346565-e3dbc353d2e5?w=400&h=300&fit=crop',
                'prep_time': '45 mins',
                'difficulty': 'Easy',
                'spice_level': 'None',
                'is_vegan': 0,
                'is_vegetarian': 1,
                'is_gluten_free': 0,
                'health_benefits': 'Good source of calcium and protein, provides energy from pasta, contains vitamin A',
                'ingredients': '400g elbow macaroni|3 cups sharp cheddar cheese, grated|1 cup milk|3 tbsp butter|3 tbsp flour|1/2 tsp mustard powder|1/4 tsp paprika|Salt and white pepper|1/2 cup breadcrumbs|Extra cheese for topping',
                'steps': 'Preheat oven to 375°F (190°C)|Cook macaroni according to package directions|Melt butter in saucepan, whisk in flour|Gradually add milk, whisking constantly|Cook until thickened, about 5 minutes|Add mustard powder and seasonings|Remove from heat, stir in cheese until melted|Combine cheese sauce with cooked pasta|Transfer to greased baking dish|Top with breadcrumbs and extra cheese|Bake 25 minutes until golden and bubbly'
            },
            {
                'name': 'Fried Chicken',
                'country': 'USA',
                'origin': 'Southern United States',
                'cuisine_type': 'American Southern',
                'description': 'Crispy seasoned fried chicken with golden crust',
                'image': 'https://images.unsplash.com/photo-1544025162-d76694265947?w=400&h=300&fit=crop',
                'prep_time': '60 mins',
                'difficulty': 'Medium',
                'spice_level': 'Mild',
                'is_vegan': 0,
                'is_vegetarian': 0,
                'is_gluten_free': 0,
                'health_benefits': 'High in protein, provides essential amino acids, contains B vitamins and selenium',
                'ingredients': '1 whole chicken, cut into pieces|2 cups buttermilk|3 cups all-purpose flour|2 tbsp paprika|1 tbsp garlic powder|1 tbsp onion powder|2 tsp salt|1 tsp black pepper|1 tsp cayenne pepper|Vegetable oil for frying',
                'steps': 'Marinate chicken in buttermilk for 2-4 hours|Mix flour with all spices in large bowl|Heat oil to 350°F (175°C) in heavy pot|Remove chicken from buttermilk, dredge in seasoned flour|Shake off excess flour|Fry chicken pieces in batches, don\'t overcrowd|Cook 12-15 minutes until golden and internal temp reaches 165°F|Drain on paper towels|Serve hot with mashed potatoes and gravy'
            },
            {
                'name': 'Apple Pie',
                'country': 'USA',
                'origin': 'United States',
                'cuisine_type': 'American Dessert',
                'description': 'Classic American dessert with spiced apple filling in flaky crust',
                'image': 'https://images.unsplash.com/photo-1621996346565-e3dbc353d2e5?w=400&h=300&fit=crop',
                'prep_time': '90 mins',
                'difficulty': 'Medium',
                'spice_level': 'Mild',
                'is_vegan': 0,
                'is_vegetarian': 1,
                'is_gluten_free': 0,
                'health_benefits': 'Contains fiber and vitamin C from apples, provides antioxidants, moderate calories',
                'ingredients': '8 large apples, peeled and sliced|2 pie crusts|3/4 cup sugar|2 tbsp flour|1 tsp cinnamon|1/4 tsp nutmeg|1/4 tsp salt|2 tbsp butter|1 egg for wash|1 tbsp milk',
                'steps': 'Preheat oven to 425°F (220°C)|Line pie dish with bottom crust|Mix sliced apples with sugar, flour, and spices|Fill crust with apple mixture|Dot with butter pieces|Cover with top crust and crimp edges|Cut vents in top crust|Brush with egg wash mixed with milk|Bake 45-50 minutes until golden|Cool before serving|Serve with vanilla ice cream'
            }
        ]
        
        # Korean recipes
        korean_recipes = [
            {
                'name': 'Kimchi',
                'country': 'South Korea',
                'origin': 'Korea',
                'cuisine_type': 'Korean Traditional',
                'description': 'Fermented napa cabbage with chili peppers, garlic, and ginger',
                'image': 'https://images.unsplash.com/photo-1610415946035-bad6d5b9dbb6?w=400&h=300&fit=crop',
                'prep_time': '30 mins + 3 days fermentation',
                'difficulty': 'Medium',
                'spice_level': 'Hot',
                'is_vegan': 1,
                'is_vegetarian': 1,
                'is_gluten_free': 1,
                'health_benefits': 'Rich in probiotics for gut health, high in vitamins A and C, contains antioxidants, supports immune system',
                'ingredients': '1 large napa cabbage|1/4 cup sea salt|1 tbsp grated ginger|5 cloves garlic, minced|1 tsp sugar|3 tbsp fish sauce (or soy sauce for vegan)|1-5 tbsp Korean red pepper flakes (gochugaru)|4 scallions, chopped|1 daikon radish, julienned',
                'steps': 'Cut cabbage into 2-inch pieces and salt generously|Let sit for 2 hours, then rinse and drain|Mix ginger, garlic, sugar, and fish sauce into paste|Add red pepper flakes to create gochujang-like mixture|Combine cabbage with paste, scallions, and radish|Mix thoroughly with clean hands|Pack into clean jar, leaving 1 inch headspace|Ferment at room temperature for 3-5 days|Taste daily and refrigerate when desired sourness is reached|Serve as banchan (side dish) with Korean meals'
            },
            {
                'name': 'Bulgogi',
                'country': 'South Korea',
                'origin': 'Korea',
                'cuisine_type': 'Korean BBQ',
                'description': 'Marinated grilled beef with sweet and savory flavors',
                'image': 'https://images.unsplash.com/photo-1548940740-204726a19be3?w=400&h=300&fit=crop',
                'prep_time': '45 mins + marinating',
                'difficulty': 'Medium',
                'spice_level': 'Mild',
                'is_vegan': 0,
                'is_vegetarian': 0,
                'is_gluten_free': 0,
                'health_benefits': 'High in protein and iron, provides B vitamins, contains antioxidants from garlic and ginger',
                'ingredients': '1kg thinly sliced ribeye or sirloin|1/2 cup soy sauce|1/4 cup brown sugar|2 tbsp sesame oil|1 Asian pear, grated|1 onion, sliced|6 cloves garlic, minced|1 tbsp fresh ginger, minced|2 green onions, chopped|1 tbsp toasted sesame seeds|2 tsp black pepper',
                'steps': 'Freeze beef for 30 minutes for easier slicing|Slice beef paper-thin against the grain|Mix soy sauce, brown sugar, sesame oil, and grated pear|Add garlic, ginger, and black pepper to marinade|Marinate beef for at least 30 minutes (or overnight)|Heat grill or large skillet over high heat|Cook beef in batches, don\'t overcrowd|Cook for 2-3 minutes until caramelized|Garnish with green onions and sesame seeds|Serve with steamed rice and kimchi'
            },
            {
                'name': 'Bibimbap',
                'country': 'South Korea',
                'origin': 'Korea',
                'cuisine_type': 'Korean Traditional',
                'description': 'Mixed rice bowl with seasoned vegetables, meat, and fried egg',
                'image': 'https://images.unsplash.com/photo-1498654896293-37aacf113fd9?w=400&h=300&fit=crop',
                'prep_time': '60 mins',
                'difficulty': 'Hard',
                'spice_level': 'Medium',
                'is_vegan': 0,
                'is_vegetarian': 0,
                'is_gluten_free': 0,
                'health_benefits': 'Balanced nutrition from vegetables and protein, rich in vitamins and minerals, provides healthy fats',
                'ingredients': '4 cups cooked short-grain rice|200g beef bulgogi|4 shiitake mushrooms, sliced|1 cup bean sprouts|1 carrot, julienned|1 cucumber, julienned|1 cup spinach|4 eggs|4 tbsp gochujang|2 tbsp sesame oil|Soy sauce|Garlic|Vegetable oil',
                'steps': 'Prepare bulgogi beef and set aside|Blanch spinach, season with sesame oil and garlic|Sauté mushrooms with soy sauce|Blanch bean sprouts briefly|Salt cucumber and let drain, then rinse|Sauté carrot until tender-crisp|Fry eggs sunny-side up|Place rice in bowls|Arrange vegetables in sections on top of rice|Top with beef and fried egg|Serve with gochujang on the side|Mix everything together before eating'
            },
            {
                'name': 'Korean Fried Chicken',
                'country': 'South Korea',
                'origin': 'Korea',
                'cuisine_type': 'Korean Street Food',
                'description': 'Extra crispy double-fried chicken with sweet and spicy glaze',
                'image': 'https://images.unsplash.com/photo-1562967916-eb82221dfb92?w=400&h=300&fit=crop',
                'prep_time': '90 mins',
                'difficulty': 'Hard',
                'spice_level': 'Hot',
                'is_vegan': 0,
                'is_vegetarian': 0,
                'is_gluten_free': 0,
                'health_benefits': 'High in protein, provides essential amino acids, contains antioxidants from garlic and ginger',
                'ingredients': '1kg chicken wings or drumettes|1 cup potato starch|1/2 cup all-purpose flour|1 cup cold water|1 tsp salt|For sauce: 1/4 cup gochujang|3 tbsp soy sauce|3 tbsp honey|2 tbsp rice vinegar|4 cloves garlic, minced|1 tbsp ginger, minced|1 tbsp sesame oil|Oil for frying',
                'steps': 'Mix potato starch, flour, and salt|Add cold water to make smooth batter|Let batter rest for 30 minutes|Heat oil to 325°F (160°C)|Dip chicken in batter and fry for 10 minutes|Remove and drain on rack|Meanwhile, mix all sauce ingredients|Heat oil to 375°F (190°C)|Fry chicken again for 5 minutes until golden|Toss hot chicken with sauce immediately|Garnish with sesame seeds and green onions|Serve immediately while crispy'
            },
            {
                'name': 'Japchae',
                'country': 'South Korea',
                'origin': 'Korea',
                'cuisine_type': 'Korean Traditional',
                'description': 'Stir-fried sweet potato noodles with vegetables and beef',
                'image': 'https://images.unsplash.com/photo-1553621042-f6e147245754?w=400&h=300&fit=crop',
                'prep_time': '45 mins',
                'difficulty': 'Medium',
                'spice_level': 'Mild',
                'is_vegan': 0,
                'is_vegetarian': 0,
                'is_gluten_free': 1,
                'health_benefits': 'Gluten-free noodles, rich in vegetables, provides protein from beef, contains antioxidants',
                'ingredients': '200g sweet potato noodles (dangmyeon)|200g beef, thinly sliced|1 carrot, julienned|1 bell pepper, sliced|4 shiitake mushrooms, sliced|2 cups spinach|3 green onions, chopped|4 tbsp soy sauce|2 tbsp sugar|3 tbsp sesame oil|2 cloves garlic, minced|1 tbsp vegetable oil',
                'steps': 'Soak noodles in warm water for 30 minutes until soft|Marinate beef with 1 tbsp soy sauce and garlic|Blanch spinach and squeeze out excess water|Stir-fry beef until cooked, set aside|Stir-fry each vegetable separately, seasoning lightly|Boil noodles for 6-7 minutes until tender|Drain noodles and rinse with cold water|Mix soy sauce, sugar, and sesame oil for sauce|Combine noodles with sauce and all ingredients|Toss everything together gently|Garnish with sesame seeds and serve at room temperature'
            },
            {
                'name': 'Korean Corn Dog',
                'country': 'South Korea',
                'origin': 'Korea',
                'cuisine_type': 'Korean Street Food',
                'description': 'Hot dog coated in potato cubes and fried until golden',
                'image': 'https://images.unsplash.com/photo-1601050690597-df0568f70950?w=400&h=300&fit=crop',
                'prep_time': '30 mins',
                'difficulty': 'Medium',
                'spice_level': 'None',
                'is_vegan': 0,
                'is_vegetarian': 0,
                'is_gluten_free': 0,
                'health_benefits': 'Provides protein, contains carbohydrates for energy, fun comfort food option',
                'ingredients': '6 hot dogs or mozzarella sticks|1 cup all-purpose flour|1/2 cup cornstarch|1 tsp baking powder|1 tsp salt|1 cup milk|1 egg|2 cups small potato cubes|Wooden skewers|Oil for frying|Ketchup and mustard for serving',
                'steps': 'Insert wooden skewers into hot dogs|Mix flour, cornstarch, baking powder, and salt|Add milk and egg to make smooth batter|Dip hot dogs in batter, coating completely|Roll in potato cubes, pressing gently to adhere|Heat oil to 350°F (175°C)|Fry corn dogs for 3-4 minutes until golden|Turn occasionally for even browning|Drain on paper towels|Serve hot with ketchup and mustard|Best enjoyed immediately while crispy'
            },
            {
                'name': 'Tteokbokki',
                'country': 'South Korea',
                'origin': 'Korea',
                'cuisine_type': 'Korean Street Food',
                'description': 'Chewy rice cakes in sweet and spicy sauce',
                'image': 'https://images.unsplash.com/photo-1590736969955-71cc94901144?w=400&h=300&fit=crop',
                'prep_time': '20 mins',
                'difficulty': 'Easy',
                'spice_level': 'Hot',
                'is_vegan': 1,
                'is_vegetarian': 1,
                'is_gluten_free': 1,
                'health_benefits': 'Provides quick energy from rice, contains antioxidants from chili, low in fat',
                'ingredients': '500g cylindrical rice cakes|3 tbsp gochujang|1 tbsp soy sauce|1 tbsp sugar|2 cups water|2 green onions, chopped|1 tbsp vegetable oil|1 clove garlic, minced|Sesame seeds for garnish',
                'steps': 'Soak rice cakes in warm water to soften|Mix gochujang, soy sauce, and sugar in small bowl|Heat oil in large pan over medium heat|Add garlic and cook for 30 seconds|Add sauce mixture and water|Bring to simmer and add rice cakes|Cook for 8-10 minutes until sauce thickens|Add green onions in last minute|Garnish with sesame seeds|Serve hot as a snack or light meal'
            },
            {
                'name': 'Korean Fried Rice (Kimchi Bokkeumbap)',
                'country': 'South Korea',
                'origin': 'Korea',
                'cuisine_type': 'Korean Home Cooking',
                'description': 'Fried rice with kimchi, vegetables, and optional protein',
                'image': 'https://images.unsplash.com/photo-1563379091339-03246963d51a?w=400&h=300&fit=crop',
                'prep_time': '20 mins',
                'difficulty': 'Easy',
                'spice_level': 'Medium',
                'is_vegan': 0,
                'is_vegetarian': 0,
                'is_gluten_free': 1,
                'health_benefits': 'Contains probiotics from kimchi, provides protein and carbohydrates, rich in vitamins from vegetables',
                'ingredients': '4 cups day-old cooked rice|1 cup aged kimchi, chopped|200g spam or bacon, diced|2 eggs|2 green onions, chopped|2 cloves garlic, minced|2 tbsp vegetable oil|1 tbsp sesame oil|1 tbsp soy sauce|Sesame seeds|Nori sheets, shredded',
                'steps': 'Heat oil in large wok or skillet|Cook spam or bacon until crispy|Add garlic and cook for 1 minute|Add kimchi and stir-fry for 3 minutes|Add cold rice, breaking up clumps|Stir-fry for 5 minutes until heated through|Push rice to one side, scramble eggs|Mix eggs into rice|Add soy sauce and sesame oil|Garnish with green onions, sesame seeds, and nori|Serve hot as a main dish'
            }
        ]
        
        # Middle Eastern and other global recipes
        global_recipes = [
            {
                'name': 'Hummus',
                'country': 'Lebanon',
                'origin': 'Middle East',
                'cuisine_type': 'Middle Eastern Traditional',
                'description': 'Creamy chickpea dip with tahini, lemon, and garlic',
                'image': 'https://images.unsplash.com/photo-1571197119282-7c4fe7c2f9f5?w=400&h=300&fit=crop',
                'prep_time': '15 mins',
                'difficulty': 'Easy',
                'spice_level': 'Mild',
                'is_vegan': 1,
                'is_vegetarian': 1,
                'is_gluten_free': 1,
                'health_benefits': 'High in protein and fiber, contains healthy fats, rich in folate and magnesium',
                'ingredients': '2 cups cooked chickpeas|1/4 cup tahini|3 cloves garlic, minced|Juice of 2 lemons|3 tbsp olive oil|1 tsp ground cumin|Salt to taste|Water as needed|Paprika for garnish|Pine nuts (optional)',
                'steps': 'Drain and rinse chickpeas, reserve cooking liquid|Add chickpeas to food processor|Add tahini, garlic, lemon juice, and cumin|Process until smooth|With processor running, drizzle in olive oil|Add reserved liquid until desired consistency|Season with salt to taste|Transfer to serving plate|Drizzle with olive oil and sprinkle paprika|Serve with pita bread or vegetables'
            },
            {
                'name': 'Kebabs',
                'country': 'Turkey',
                'origin': 'Middle East',
                'cuisine_type': 'Turkish Traditional',
                'description': 'Grilled seasoned meat skewers with herbs and spices',
                'image': 'https://images.unsplash.com/photo-1544025162-d76694265947?w=400&h=300&fit=crop',
                'prep_time': '45 mins',
                'difficulty': 'Medium',
                'spice_level': 'Medium',
                'is_vegan': 0,
                'is_vegetarian': 0,
                'is_gluten_free': 1,
                'health_benefits': 'High in protein and iron, provides essential amino acids, contains antioxidants from herbs',
                'ingredients': '1kg lamb or beef, cubed|2 onions, grated|4 cloves garlic, minced|2cm ginger, minced|2 tsp ground cumin|2 tsp paprika|1 tsp cinnamon|1/4 cup fresh parsley, chopped|1/4 cup fresh mint, chopped|3 tbsp olive oil|Salt and pepper|Wooden skewers',
                'steps': 'Soak wooden skewers in water for 30 minutes|Mix grated onions with meat in large bowl|Add garlic, ginger, and all spices|Add herbs and olive oil|Season with salt and pepper|Mix well and marinate for 2 hours|Thread meat onto skewers|Grill over medium-high heat for 12-15 minutes|Turn frequently for even cooking|Serve with rice, flatbread, and yogurt sauce'
            },
            {
                'name': 'Falafel',
                'country': 'Egypt',
                'origin': 'Middle East',
                'cuisine_type': 'Middle Eastern Traditional',
                'description': 'Deep-fried chickpea balls with herbs and spices',
                'image': 'https://images.unsplash.com/photo-1601050690597-df0568f70950?w=400&h=300&fit=crop',
                'prep_time': '30 mins + soaking',
                'difficulty': 'Medium',
                'spice_level': 'Mild',
                'is_vegan': 1,
                'is_vegetarian': 1,
                'is_gluten_free': 1,
                'health_benefits': 'High in protein and fiber, contains iron and folate, provides healthy plant proteins',
                'ingredients': '2 cups dried chickpeas (soaked overnight)|1 onion, roughly chopped|4 cloves garlic|1/4 cup fresh parsley|1/4 cup fresh cilantro|2 tsp ground cumin|1 tsp ground coriander|1/2 tsp cayenne pepper|1 tsp salt|2 tbsp flour|Oil for frying',
                'steps': 'Drain soaked chickpeas completely|Add chickpeas to food processor with onion and garlic|Pulse until coarsely ground, not smooth|Add herbs and spices|Pulse to combine|Add flour and mix|Let mixture rest 30 minutes|Form into small balls with wet hands|Heat oil to 350°F (175°C)|Fry falafel in batches until golden brown|Drain on paper towels|Serve in pita with tahini sauce and vegetables'
            },
            {
                'name': 'Pizza Margherita',
                'country': 'Italy',
                'origin': 'Naples, Italy',
                'cuisine_type': 'Italian Traditional',
                'description': 'Classic Neapolitan pizza with tomato, mozzarella, and basil',
                'image': 'https://images.unsplash.com/photo-1621996346565-e3dbc353d2e5?w=400&h=300&fit=crop',
                'prep_time': '120 mins',
                'difficulty': 'Medium',
                'spice_level': 'Mild',
                'is_vegan': 0,
                'is_vegetarian': 1,
                'is_gluten_free': 0,
                'health_benefits': 'Provides calcium from cheese, contains lycopene from tomatoes, includes antioxidants from basil',
                'ingredients': 'For dough: 3 cups flour|1 tsp active dry yeast|1 tsp salt|1 tbsp olive oil|1 cup warm water|For topping: 1/2 cup tomato sauce|200g fresh mozzarella, sliced|Fresh basil leaves|Extra virgin olive oil|Salt and pepper',
                'steps': 'Dissolve yeast in warm water for 5 minutes|Mix flour and salt in large bowl|Add yeast mixture and oil|Knead for 10 minutes until smooth|Let rise for 1 hour until doubled|Preheat oven to 475°F (245°C)|Roll dough into thin circle|Spread tomato sauce evenly|Add mozzarella slices|Bake for 12-15 minutes until golden|Add fresh basil leaves|Drizzle with olive oil before serving'
            },
            {
                'name': 'Shawarma',
                'country': 'Lebanon',
                'origin': 'Middle East',
                'cuisine_type': 'Middle Eastern Street Food',
                'description': 'Marinated meat cooked on rotating spit, served in pita',
                'image': 'https://images.unsplash.com/photo-1565299624946-b28f40a0ca4b?w=400&h=300&fit=crop',
                'prep_time': '60 mins + marinating',
                'difficulty': 'Medium',
                'spice_level': 'Medium',
                'is_vegan': 0,
                'is_vegetarian': 0,
                'is_gluten_free': 0,
                'health_benefits': 'High in protein, contains antioxidants from spices, provides B vitamins',
                'ingredients': '1kg lamb or chicken, thinly sliced|1/4 cup olive oil|4 cloves garlic, minced|2 tsp ground cumin|2 tsp paprika|1 tsp turmeric|1 tsp cinnamon|Juice of 2 lemons|Salt and pepper|Pita bread|Tahini sauce|Pickled vegetables|Fresh parsley',
                'steps': 'Mix olive oil with garlic and all spices|Marinate meat in spice mixture for 4+ hours|Cook meat in hot skillet in batches|Cook until crispy edges form|Warm pita bread|Spread tahini sauce on pita|Fill with cooked meat|Add pickled vegetables and parsley|Roll tightly and serve immediately|Offer extra sauce on the side'
            },
            {
                'name': 'Pierogies',
                'country': 'Poland',
                'origin': 'Eastern Europe',
                'cuisine_type': 'Polish Traditional',
                'description': 'Filled dumplings with potato, cheese, or meat filling',
                'image': 'https://images.unsplash.com/photo-1601050690597-df0568f70950?w=400&h=300&fit=crop',
                'prep_time': '90 mins',
                'difficulty': 'Medium',
                'spice_level': 'None',
                'is_vegan': 0,
                'is_vegetarian': 1,
                'is_gluten_free': 0,
                'health_benefits': 'Good source of carbohydrates, provides protein from cheese, contains potassium',
                'ingredients': '3 cups flour|1 egg|1/2 cup sour cream|1/4 cup butter, melted|1 tsp salt|For filling: 4 potatoes, mashed|1 cup farmer\'s cheese|1 onion, diced|2 tbsp butter|Salt and pepper|Sour cream for serving',
                'steps': 'Make dough with flour, egg, sour cream, melted butter, salt|Knead until smooth, let rest 30 minutes|Cook onions in butter until golden|Mix mashed potatoes with cheese and onions|Season filling with salt and pepper|Roll dough thin and cut into circles|Place filling in center of each circle|Fold and seal edges well|Boil in salted water until they float|Sauté in butter until golden|Serve with sour cream and fried onions'
            },
            {
                'name': 'Butter Croissant',
                'country': 'France',
                'origin': 'France',
                'cuisine_type': 'French Pastry',
                'description': 'Flaky, buttery pastry with layers of dough and butter',
                'image': 'https://images.unsplash.com/photo-1549007994-cb92caebd54b?w=400&h=300&fit=crop',
                'prep_time': '8 hours (with rising)',
                'difficulty': 'Hard',
                'spice_level': 'None',
                'is_vegan': 0,
                'is_vegetarian': 1,
                'is_gluten_free': 0,
                'health_benefits': 'Provides energy from carbohydrates, contains some protein, source of B vitamins',
                'ingredients': '4 cups bread flour|1/4 cup sugar|2 tsp salt|1 packet active dry yeast|1 cup warm milk|250g unsalted butter, cold|1 egg for wash|1 tbsp milk for wash',
                'steps': 'Dissolve yeast in warm milk with 1 tbsp sugar|Mix flour, remaining sugar, and salt|Add yeast mixture and knead 10 minutes|Let rise 1 hour|Roll butter into rectangle between parchment|Roll dough into rectangle twice the size of butter|Place butter on half of dough, fold over|Roll and fold 3 times, chilling between folds|Cut into triangles and shape into crescents|Let rise 2 hours|Brush with egg wash|Bake at 400°F for 15-20 minutes until golden'
            }
        ]
        
        # Brazilian recipes
        brazilian_recipes = [
            {
                'name': 'Feijoada',
                'country': 'Brazil',
                'origin': 'Brazil',
                'cuisine_type': 'Brazilian Traditional',
                'description': 'Brazil\'s national dish - black bean stew with pork and beef',
                'image': 'https://images.unsplash.com/photo-1586511925558-a4c6376fe65f?w=400&h=300&fit=crop',
                'prep_time': '180 mins',
                'difficulty': 'Medium',
                'spice_level': 'Mild',
                'is_vegan': 0,
                'is_vegetarian': 0,
                'is_gluten_free': 1,
                'health_benefits': 'High in protein and fiber, rich in iron, provides complex carbohydrates, contains antioxidants',
                'ingredients': '2 cups dried black beans|500g pork shoulder, cubed|300g beef, cubed|200g Portuguese chorizo|200g bacon, diced|2 onions, chopped|6 cloves garlic, minced|2 bay leaves|1 orange, zested|Salt and pepper|For serving: white rice|Collard greens|Orange slices|Farofa (toasted cassava flour)',
                'steps': 'Soak black beans overnight|Cook beans with bay leaves for 1 hour until tender|In large pot, brown bacon until crispy|Add pork and beef, brown on all sides|Add chorizo and cook for 5 minutes|Add onions and garlic, cook until soft|Add cooked beans with cooking liquid|Add orange zest and seasonings|Simmer for 45 minutes until meat is tender|Adjust seasoning with salt and pepper|Serve with white rice, sautéed collard greens|Garnish with orange slices and farofa'
            },
            {
                'name': 'Brigadeiros',
                'country': 'Brazil',
                'origin': 'Brazil',
                'cuisine_type': 'Brazilian Dessert',
                'description': 'Rich chocolate truffles covered in chocolate sprinkles',
                'image': 'https://images.unsplash.com/photo-1549007994-cb92caebd54b?w=400&h=300&fit=crop',
                'prep_time': '30 mins + chilling',
                'difficulty': 'Easy',
                'spice_level': 'None',
                'is_vegan': 0,
                'is_vegetarian': 1,
                'is_gluten_free': 1,
                'health_benefits': 'Contains antioxidants from cocoa, provides quick energy, comfort food in moderation',
                'ingredients': '1 can (14oz) sweetened condensed milk|3 tbsp unsweetened cocoa powder|2 tbsp butter|Pinch of salt|1 cup chocolate sprinkles (granulado)|Butter for hands',
                'steps': 'Combine condensed milk, cocoa powder, and butter in saucepan|Cook over medium-low heat, stirring constantly|Stir for 8-10 minutes until mixture thickens|Mixture is ready when it pulls away from pan sides|Remove from heat and let cool completely|Butter hands and roll mixture into small balls|Roll each ball in chocolate sprinkles|Place in small paper cups|Chill for at least 1 hour before serving|Serve at room temperature for best flavor'
            },
            {
                'name': 'Coxinha',
                'country': 'Brazil',
                'origin': 'Brazil',
                'cuisine_type': 'Brazilian Street Food',
                'description': 'Teardrop-shaped croquettes filled with shredded chicken',
                'image': 'https://images.unsplash.com/photo-1601050690597-df0568f70950?w=400&h=300&fit=crop',
                'prep_time': '120 mins',
                'difficulty': 'Hard',
                'spice_level': 'Mild',
                'is_vegan': 0,
                'is_vegetarian': 0,
                'is_gluten_free': 0,
                'health_benefits': 'Good source of protein from chicken, provides carbohydrates, contains B vitamins',
                'ingredients': '500g chicken breast|2 cups chicken stock|2 tbsp butter|2 cups all-purpose flour|2 eggs, beaten|2 cups breadcrumbs|1 onion, minced|2 cloves garlic, minced|Salt and pepper|Oil for frying|Fresh parsley',
                'steps': 'Boil chicken in seasoned water until tender|Shred chicken finely and season|Sauté onion and garlic, mix with chicken|Bring stock to boil, add butter|Gradually add flour, stirring constantly|Cook until dough forms and pulls from sides|Let dough cool completely|Form dough around chicken filling into teardrop shapes|Dip in beaten eggs, then breadcrumbs|Deep fry until golden brown|Drain on paper towels|Serve hot as appetizer or snack'
            },
            {
                'name': 'Moqueca',
                'country': 'Brazil',
                'origin': 'Bahia, Brazil',
                'cuisine_type': 'Brazilian Coastal',
                'description': 'Brazilian fish stew with coconut milk, dendê oil, and peppers',
                'image': 'https://images.unsplash.com/photo-1563379091339-03246963d51a?w=400&h=300&fit=crop',
                'prep_time': '40 mins',
                'difficulty': 'Medium',
                'spice_level': 'Medium',
                'is_vegan': 0,
                'is_vegetarian': 0,
                'is_gluten_free': 1,
                'health_benefits': 'High in omega-3 fatty acids, rich in protein, contains healthy fats from coconut and dendê',
                'ingredients': '1kg white fish fillets|400ml coconut milk|3 tbsp dendê oil (palm oil)|2 onions, sliced|1 red bell pepper, sliced|1 yellow bell pepper, sliced|4 tomatoes, chopped|4 cloves garlic, minced|2 limes, juiced|2 malagueta peppers (or jalapeños)|Fresh cilantro|Salt to taste',
                'steps': 'Season fish with salt and lime juice|Let marinate for 15 minutes|Heat dendê oil in heavy pot or clay moquequeira|Sauté onions until translucent|Add garlic and cook for 1 minute|Add bell peppers and cook for 5 minutes|Add tomatoes and cook until soft|Add coconut milk and bring to gentle simmer|Add fish pieces and peppers|Cook for 10-12 minutes until fish is done|Garnish with fresh cilantro|Serve with white rice and farofa'
            },
            {
                'name': 'Pão de Açúcar',
                'country': 'Brazil',
                'origin': 'Brazil',
                'cuisine_type': 'Brazilian Dessert',
                'description': 'Brazilian sugar bread, sweet and fluffy breakfast bread',
                'image': 'https://images.unsplash.com/photo-1549007994-cb92caebd54b?w=400&h=300&fit=crop',
                'prep_time': '120 mins',
                'difficulty': 'Medium',
                'spice_level': 'None',
                'is_vegan': 0,
                'is_vegetarian': 1,
                'is_gluten_free': 0,
                'health_benefits': 'Provides energy from carbohydrates, contains protein from eggs and milk, source of B vitamins',
                'ingredients': '4 cups bread flour|1/2 cup sugar|2 tsp active dry yeast|1 cup warm milk|2 eggs|4 tbsp butter, melted|1 tsp salt|1 tsp vanilla extract|Egg wash for brushing',
                'steps': 'Dissolve yeast in warm milk with 1 tbsp sugar|Mix flour, remaining sugar, and salt in large bowl|Add yeast mixture, eggs, melted butter, and vanilla|Knead for 10 minutes until smooth and elastic|Place in greased bowl, let rise for 1 hour|Punch down and shape into small rolls|Place on baking sheets, let rise 45 minutes|Brush with egg wash|Bake at 375°F for 15-20 minutes until golden|Serve warm with butter and jam'
            },
            {
                'name': 'Açaí Bowl',
                'country': 'Brazil',
                'origin': 'Amazon, Brazil',
                'cuisine_type': 'Brazilian Healthy',
                'description': 'Superfruit smoothie bowl topped with granola and fresh fruits',
                'image': 'https://images.unsplash.com/photo-1571197119282-7c4fe7c2f9f5?w=400&h=300&fit=crop',
                'prep_time': '15 mins',
                'difficulty': 'Easy',
                'spice_level': 'None',
                'is_vegan': 1,
                'is_vegetarian': 1,
                'is_gluten_free': 1,
                'health_benefits': 'Extremely high in antioxidants, provides healthy fats, rich in fiber, supports heart health',
                'ingredients': '2 packets frozen açaí purée|1 banana|1/2 cup blueberries|1/4 cup coconut milk|1 tbsp honey|For toppings: granola|sliced banana|strawberries|coconut flakes|chia seeds|nuts',
                'steps': 'Partially thaw açaí packets for 5 minutes|Break into chunks and add to blender|Add banana, blueberries, and coconut milk|Blend until smooth and thick|Add honey to taste|Pour into serving bowls|Arrange toppings in sections on top|Serve immediately for best texture|Popular breakfast or post-workout meal'
            }
        ]
        
        # Vietnamese recipes (additional to existing Pho)
        vietnamese_recipes = [
            {
                'name': 'Banh Mi',
                'country': 'Vietnam',
                'origin': 'Vietnam',
                'cuisine_type': 'Vietnamese Street Food',
                'description': 'Vietnamese baguette sandwich with pickled vegetables and meat',
                'image': 'https://images.unsplash.com/photo-1565299624946-b28f40a0ca4b?w=400&h=300&fit=crop',
                'prep_time': '30 mins',
                'difficulty': 'Medium',
                'spice_level': 'Mild',
                'is_vegan': 0,
                'is_vegetarian': 0,
                'is_gluten_free': 0,
                'health_benefits': 'Balanced nutrition, contains probiotics from pickled vegetables, provides protein and carbohydrates',
                'ingredients': '4 small baguettes|300g pork belly or chicken|1 carrot, julienned|1 daikon radish, julienned|1/4 cup rice vinegar|2 tbsp sugar|1 tsp salt|Mayonnaise|Pâté (optional)|Cucumber slices|Fresh cilantro|Jalapeño slices|Soy sauce|Fish sauce',
                'steps': 'Make quick pickles: combine carrot, daikon with vinegar, sugar, salt|Let sit for 30 minutes|Season and grill pork or chicken until cooked|Slice meat thinly|Slice baguettes lengthwise, remove some bread|Spread mayonnaise and pâté on bread|Layer with meat, pickled vegetables|Add cucumber, cilantro, and jalapeño|Season with soy sauce and fish sauce|Serve immediately while bread is crispy'
            },
            {
                'name': 'Fresh Spring Rolls (Goi Cuon)',
                'country': 'Vietnam',
                'origin': 'Vietnam',
                'cuisine_type': 'Vietnamese Traditional',
                'description': 'Fresh rice paper rolls with herbs, vegetables, and shrimp',
                'image': 'https://images.unsplash.com/photo-1559847844-d2104c53b694?w=400&h=300&fit=crop',
                'prep_time': '45 mins',
                'difficulty': 'Medium',
                'spice_level': 'None',
                'is_vegan': 0,
                'is_vegetarian': 0,
                'is_gluten_free': 1,
                'health_benefits': 'Low in calories, rich in fresh vegetables, provides protein, contains vitamins and minerals',
                'ingredients': '12 rice paper rounds|200g cooked shrimp|100g rice vermicelli noodles|1 cup lettuce leaves|1 cup fresh mint|1 cup fresh cilantro|1 cucumber, julienned|1 carrot, julienned|For dipping sauce: 3 tbsp fish sauce|2 tbsp lime juice|2 tbsp sugar|1/4 cup water|1 chili, minced',
                'steps': 'Cook rice noodles according to package directions, drain and cool|Prepare all vegetables and herbs|Mix dipping sauce ingredients until sugar dissolves|Soften rice paper in warm water for 10 seconds|Place on flat surface|Add lettuce, herbs, noodles, vegetables|Place shrimp on top|Roll tightly, folding in sides|Place seam-side down|Cover with damp towel until serving|Serve with dipping sauce'
            },
            {
                'name': 'Bun Bo Hue',
                'country': 'Vietnam',
                'origin': 'Hue, Vietnam',
                'cuisine_type': 'Vietnamese Traditional',
                'description': 'Spicy beef noodle soup from the imperial city of Hue',
                'image': 'https://images.unsplash.com/photo-1559847844-5315695dadae?w=400&h=300&fit=crop',
                'prep_time': '240 mins',
                'difficulty': 'Hard',
                'spice_level': 'Hot',
                'is_vegan': 0,
                'is_vegetarian': 0,
                'is_gluten_free': 1,
                'health_benefits': 'Rich in protein and collagen, contains antioxidants from lemongrass, provides essential nutrients',
                'ingredients': '400g thick rice noodles|1kg beef bones|500g pork bones|300g beef brisket|200g pork hock|3 lemongrass stalks|4 tbsp shrimp paste|3 tbsp chili oil|Fish sauce|Sugar|200g Vietnamese ham|Blood sausage (optional)|Bean sprouts|Banana flower|Fresh herbs',
                'steps': 'Simmer beef and pork bones for 4 hours|Add brisket and pork hock, cook 2 hours more|Strain broth and season with shrimp paste|Add lemongrass and simmer 30 minutes|Cook noodles according to package directions|Slice meats thinly|Place noodles in bowls with meat|Ladle hot broth over noodles|Serve with chili oil, herbs, bean sprouts|Add banana flower and lime wedges'
            },
            {
                'name': 'Vietnamese Coffee (Cà Phê Sữa Đá)',
                'country': 'Vietnam',
                'origin': 'Vietnam',
                'cuisine_type': 'Vietnamese Beverage',
                'description': 'Strong coffee with sweetened condensed milk served over ice',
                'image': 'https://images.unsplash.com/photo-1571934811356-5cc061b6821f?w=400&h=300&fit=crop',
                'prep_time': '10 mins',
                'difficulty': 'Easy',
                'spice_level': 'None',
                'is_vegan': 0,
                'is_vegetarian': 1,
                'is_gluten_free': 1,
                'health_benefits': 'Contains antioxidants from coffee, provides energy from caffeine, calcium from condensed milk',
                'ingredients': '3 tbsp Vietnamese ground coffee (dark roast)|2-3 tbsp sweetened condensed milk|Hot water|Ice cubes|Vietnamese coffee filter (phin)',
                'steps': 'Place condensed milk in bottom of glass|Set up Vietnamese coffee filter (phin) on top|Add ground coffee to filter|Pour small amount of hot water to bloom coffee|Wait 30 seconds|Slowly add remaining hot water|Let coffee drip slowly (about 5 minutes)|Stir coffee and condensed milk together|Add ice cubes to serve cold|Can be served hot without ice'
            }
        ]
        
        # French recipes (additional to existing)
        french_recipes = [
            {
                'name': 'Bouillabaisse',
                'country': 'France',
                'origin': 'Marseille, France',
                'cuisine_type': 'French Traditional',
                'description': 'Traditional Provençal fish stew with saffron and rouille',
                'image': 'https://images.unsplash.com/photo-1559847844-5315695dadae?w=400&h=300&fit=crop',
                'prep_time': '90 mins',
                'difficulty': 'Hard',
                'spice_level': 'Mild',
                'is_vegan': 0,
                'is_vegetarian': 0,
                'is_gluten_free': 1,
                'health_benefits': 'High in omega-3 fatty acids, rich in protein, contains antioxidants from saffron and tomatoes',
                'ingredients': '1kg mixed fish (sea bass, red mullet, John Dory)|500g mussels|300g prawns|2 onions, chopped|4 tomatoes, chopped|4 cloves garlic, minced|1/4 cup olive oil|1 cup white wine|Pinch of saffron|2 bay leaves|Fresh thyme|Parsley|Orange zest|For rouille: mayonnaise|garlic|saffron|cayenne',
                'steps': 'Clean and prepare all seafood|Heat olive oil in large pot|Sauté onions until translucent|Add garlic, cook for 1 minute|Add tomatoes, herbs, orange zest|Add wine and reduce slightly|Add firm fish first, cook 5 minutes|Add delicate fish and shellfish|Add saffron and simmer 10 minutes|Season with salt and pepper|Make rouille by mixing mayo with garlic, saffron, cayenne|Serve in bowls with crusty bread and rouille'
            },
            {
                'name': 'French Onion Soup',
                'country': 'France',
                'origin': 'France',
                'cuisine_type': 'French Traditional',
                'description': 'Rich onion soup topped with cheese and bread',
                'image': 'https://images.unsplash.com/photo-1559847844-5315695dadae?w=400&h=300&fit=crop',
                'prep_time': '75 mins',
                'difficulty': 'Medium',
                'spice_level': 'Mild',
                'is_vegan': 0,
                'is_vegetarian': 1,
                'is_gluten_free': 0,
                'health_benefits': 'Contains antioxidants from onions, provides calcium from cheese, supports immune system',
                'ingredients': '6 large onions, thinly sliced|4 tbsp butter|2 tbsp olive oil|1 tsp sugar|1/2 cup dry white wine|6 cups beef stock|2 bay leaves|Fresh thyme|Salt and pepper|6 slices French bread|2 cups Gruyère cheese, grated',
                'steps': 'Heat butter and oil in large heavy pot|Add onions and sugar|Cook slowly for 45 minutes until caramelized|Stir occasionally to prevent burning|Add wine and cook until evaporated|Add stock, bay leaves, and thyme|Simmer for 20 minutes|Season with salt and pepper|Preheat broiler|Ladle soup into oven-safe bowls|Top with bread slice and cheese|Broil until cheese is bubbly and golden|Serve immediately while hot'
            },
            {
                'name': 'Crème Brûlée',
                'country': 'France',
                'origin': 'France',
                'cuisine_type': 'French Dessert',
                'description': 'Creamy vanilla custard with caramelized sugar top',
                'image': 'https://images.unsplash.com/photo-1549007994-cb92caebd54b?w=400&h=300&fit=crop',
                'prep_time': '4 hours (with chilling)',
                'difficulty': 'Medium',
                'spice_level': 'None',
                'is_vegan': 0,
                'is_vegetarian': 1,
                'is_gluten_free': 1,
                'health_benefits': 'Good source of calcium and protein, contains vitamins from cream and eggs',
                'ingredients': '2 cups heavy cream|6 egg yolks|1/3 cup sugar (plus extra for topping)|1 tsp vanilla extract|Pinch of salt',
                'steps': 'Preheat oven to 325°F (160°C)|Heat cream in saucepan until just simmering|Whisk egg yolks with sugar until pale|Slowly add hot cream to eggs, whisking constantly|Add vanilla and salt|Strain mixture through fine mesh|Pour into ramekins|Bake in water bath for 35-40 minutes|Custard should be set but still jiggly|Chill for at least 3 hours|Before serving, sprinkle sugar on top|Caramelize with kitchen torch|Serve immediately'
            }
        ]
        
        # Additional European Western dishes
        more_european_recipes = [
            {
                'name': 'Bangers and Mash',
                'country': 'United Kingdom',
                'origin': 'England',
                'cuisine_type': 'British Traditional',
                'description': 'British sausages served with mashed potatoes and onion gravy',
                'image': 'https://images.unsplash.com/photo-1544025162-d76694265947?w=400&h=300&fit=crop',
                'prep_time': '35 mins',
                'difficulty': 'Easy',
                'spice_level': 'None',
                'is_vegan': 0,
                'is_vegetarian': 0,
                'is_gluten_free': 0,
                'health_benefits': 'High in protein, provides carbohydrates from potatoes, contains B vitamins',
                'ingredients': '8 pork sausages|1kg potatoes, peeled|1/4 cup butter|1/4 cup milk|2 large onions, sliced|2 tbsp flour|2 cups beef stock|2 tbsp vegetable oil|Salt and pepper|Fresh thyme',
                'steps': 'Boil potatoes until tender, about 20 minutes|Meanwhile, cook sausages in oil until browned all over|Remove sausages and keep warm|Add onions to same pan, cook until caramelized|Sprinkle flour over onions, cook 2 minutes|Gradually add stock, stirring constantly|Simmer until thickened|Mash potatoes with butter and milk|Season with salt and pepper|Serve sausages on mashed potatoes|Pour onion gravy over top|Garnish with fresh thyme'
            },
            {
                'name': 'Shepherd\'s Pie',
                'country': 'United Kingdom',
                'origin': 'England/Ireland',
                'cuisine_type': 'British Traditional',
                'description': 'Ground lamb with vegetables topped with mashed potatoes',
                'image': 'https://images.unsplash.com/photo-1544025162-d76694265947?w=400&h=300&fit=crop',
                'prep_time': '60 mins',
                'difficulty': 'Medium',
                'spice_level': 'None',
                'is_vegan': 0,
                'is_vegetarian': 0,
                'is_gluten_free': 0,
                'health_benefits': 'High in protein and iron, contains vitamins from vegetables, provides carbohydrates',
                'ingredients': '1kg ground lamb|1kg potatoes|2 carrots, diced|1 cup peas|1 onion, diced|2 cloves garlic, minced|2 tbsp tomato paste|1 cup beef stock|2 tbsp Worcestershire sauce|2 tbsp flour|1/4 cup butter|1/4 cup milk|2 tbsp olive oil|Salt and pepper|Fresh rosemary',
                'steps': 'Preheat oven to 400°F (200°C)|Boil and mash potatoes with butter and milk|Heat oil in large pan, brown lamb|Add onions, carrots, cook until soft|Add garlic, cook 1 minute|Stir in tomato paste and flour|Add stock and Worcestershire sauce|Add peas, simmer until thick|Season with salt, pepper, rosemary|Transfer to baking dish|Top with mashed potatoes|Bake 25 minutes until golden|Let rest 5 minutes before serving'
            },
            {
                'name': 'Beef Wellington',
                'country': 'United Kingdom',
                'origin': 'England',
                'cuisine_type': 'British Fine Dining',
                'description': 'Beef tenderloin wrapped in puff pastry with mushroom duxelles',
                'image': 'https://images.unsplash.com/photo-1544025162-d76694265947?w=400&h=300&fit=crop',
                'prep_time': '120 mins',
                'difficulty': 'Hard',
                'spice_level': 'None',
                'is_vegan': 0,
                'is_vegetarian': 0,
                'is_gluten_free': 0,
                'health_benefits': 'High in protein and iron, provides B vitamins, contains antioxidants from mushrooms',
                'ingredients': '1kg beef tenderloin|500g puff pastry|500g mushrooms, chopped|200g pâté|8 slices prosciutto|2 egg yolks|2 tbsp Dijon mustard|2 tbsp olive oil|2 shallots, minced|2 cloves garlic|1/4 cup brandy|Salt and pepper|Fresh thyme',
                'steps': 'Season beef and sear in hot oil until browned|Brush with mustard and let cool|Cook mushrooms with shallots until moisture evaporates|Add garlic, thyme, brandy, cook until dry|Cool completely|Lay prosciutto on plastic wrap|Spread pâté over prosciutto|Add mushroom mixture|Wrap beef in prosciutto mixture|Chill 30 minutes|Roll pastry around beef|Brush with egg wash|Bake at 425°F for 25-30 minutes|Rest 10 minutes before slicing'
            },
            {
                'name': 'Sauerbraten',
                'country': 'Germany',
                'origin': 'Rhine Valley, Germany',
                'cuisine_type': 'German Traditional',
                'description': 'German pot roast marinated in vinegar and wine with sweet-sour gravy',
                'image': 'https://images.unsplash.com/photo-1544025162-d76694265947?w=400&h=300&fit=crop',
                'prep_time': '4 days + 3 hours cooking',
                'difficulty': 'Hard',
                'spice_level': 'Mild',
                'is_vegan': 0,
                'is_vegetarian': 0,
                'is_gluten_free': 0,
                'health_benefits': 'High in protein and iron, provides B vitamins, contains antioxidants from wine',
                'ingredients': '2kg beef roast|2 cups red wine vinegar|1 cup red wine|2 onions, sliced|2 carrots, sliced|2 bay leaves|1 tsp peppercorns|4 cloves|1 tsp juniper berries|3 tbsp vegetable oil|3 tbsp flour|1/4 cup raisins|2 tbsp sugar|Gingersnap cookies for thickening',
                'steps': 'Combine vinegar, wine, vegetables, and spices for marinade|Marinate beef for 3-4 days in refrigerator|Turn daily|Remove beef, strain and reserve marinade|Pat beef dry and brown in oil|Add strained vegetables and cook|Add 2 cups marinade and bring to boil|Cover and simmer 2.5 hours until tender|Remove beef and strain liquid|Make gravy with flour, add raisins and sugar|Thicken with crushed gingersnaps|Slice beef and serve with gravy and red cabbage'
            },
            {
                'name': 'Schnitzel',
                'country': 'Germany',
                'origin': 'Austria/Germany',
                'cuisine_type': 'German Traditional',
                'description': 'Breaded and fried meat cutlet served with lemon',
                'image': 'https://images.unsplash.com/photo-1544025162-d76694265947?w=400&h=300&fit=crop',
                'prep_time': '30 mins',
                'difficulty': 'Medium',
                'spice_level': 'None',
                'is_vegan': 0,
                'is_vegetarian': 0,
                'is_gluten_free': 0,
                'health_benefits': 'High in protein, provides essential amino acids, source of B vitamins and iron',
                'ingredients': '4 pork or chicken cutlets|2 cups fine breadcrumbs|2 eggs, beaten|1/2 cup flour|Vegetable oil for frying|Salt and pepper|Lemon wedges|Fresh parsley|Potato salad for serving',
                'steps': 'Pound cutlets until very thin|Season with salt and pepper|Set up breading station: flour, beaten eggs, breadcrumbs|Dredge cutlets in flour, then egg, then breadcrumbs|Press coating to adhere well|Heat oil in large skillet|Fry schnitzels 2-3 minutes per side until golden|Drain on paper towels|Serve immediately with lemon wedges|Traditionally served with potato salad and lingonberry sauce|Garnish with fresh parsley'
            },
            {
                'name': 'Beef Stroganoff',
                'country': 'Russia',
                'origin': 'Russia',
                'cuisine_type': 'Russian Traditional',
                'description': 'Tender beef in creamy mushroom and sour cream sauce',
                'image': 'https://images.unsplash.com/photo-1563379091339-03246963d51a?w=400&h=300&fit=crop',
                'prep_time': '45 mins',
                'difficulty': 'Medium',
                'spice_level': 'None',
                'is_vegan': 0,
                'is_vegetarian': 0,
                'is_gluten_free': 0,
                'health_benefits': 'High in protein and iron, provides B vitamins, contains antioxidants from mushrooms',
                'ingredients': '1kg beef sirloin, sliced thin|500g mushrooms, sliced|1 onion, chopped|3 cloves garlic, minced|1 cup sour cream|1 cup beef stock|3 tbsp flour|3 tbsp butter|2 tbsp vegetable oil|2 tbsp Dijon mustard|Salt and pepper|Fresh dill|Egg noodles for serving',
                'steps': 'Season beef strips with salt and pepper|Heat oil in large skillet, brown beef in batches|Remove beef and set aside|Add butter to pan, sauté mushrooms until golden|Add onions and garlic, cook until soft|Sprinkle flour over vegetables, cook 2 minutes|Gradually add stock, stirring constantly|Add mustard and simmer until thickened|Return beef to pan|Stir in sour cream and heat through|Garnish with fresh dill|Serve over egg noodles'
            },
            {
                'name': 'Swedish Meatballs',
                'country': 'Sweden',
                'origin': 'Scandinavia',
                'cuisine_type': 'Scandinavian Traditional',
                'description': 'Tender meatballs in cream sauce, served with lingonberry jam',
                'image': 'https://images.unsplash.com/photo-1544025162-d76694265947?w=400&h=300&fit=crop',
                'prep_time': '60 mins',
                'difficulty': 'Medium',
                'spice_level': 'None',
                'is_vegan': 0,
                'is_vegetarian': 0,
                'is_gluten_free': 0,
                'health_benefits': 'High in protein, provides iron and B vitamins, contains calcium from cream',
                'ingredients': '500g ground beef|250g ground pork|1 onion, finely minced|1/2 cup breadcrumbs|1/4 cup milk|1 egg|1/2 tsp allspice|1/4 tsp nutmeg|Salt and pepper|2 tbsp butter|2 tbsp flour|2 cups beef stock|1/2 cup heavy cream|Lingonberry jam',
                'steps': 'Soak breadcrumbs in milk|Mix ground meats with onion, egg, soaked breadcrumbs|Season with allspice, nutmeg, salt, pepper|Form into small meatballs|Brown meatballs in butter in large skillet|Remove meatballs, add flour to pan|Cook flour for 2 minutes|Gradually add stock, whisking constantly|Return meatballs to pan|Simmer 15 minutes until cooked through|Stir in cream|Serve with boiled potatoes and lingonberry jam'
            },
            {
                'name': 'Dutch Pancakes (Pannenkoeken)',
                'country': 'Netherlands',
                'origin': 'Netherlands',
                'cuisine_type': 'Dutch Traditional',
                'description': 'Large thin pancakes served sweet or savory',
                'image': 'https://images.unsplash.com/photo-1549007994-cb92caebd54b?w=400&h=300&fit=crop',
                'prep_time': '30 mins',
                'difficulty': 'Easy',
                'spice_level': 'None',
                'is_vegan': 0,
                'is_vegetarian': 1,
                'is_gluten_free': 0,
                'health_benefits': 'Provides energy from carbohydrates, contains protein from eggs, source of calcium',
                'ingredients': '2 cups all-purpose flour|3 eggs|2 cups milk|1/2 tsp salt|2 tbsp melted butter|Butter for cooking|Toppings: powdered sugar|syrup|bacon|cheese|apples|jam',
                'steps': 'Whisk flour and salt in large bowl|Beat eggs with milk|Gradually add milk mixture to flour|Whisk until smooth batter forms|Stir in melted butter|Let batter rest 30 minutes|Heat large skillet or crepe pan|Add butter and pour in batter to cover pan|Cook until golden brown, flip once|Add desired toppings while still in pan|Fold or roll pancake|Serve immediately while hot'
            },
            {
                'name': 'Spanish Tortilla',
                'country': 'Spain',
                'origin': 'Spain',
                'cuisine_type': 'Spanish Traditional',
                'description': 'Thick potato omelet, a Spanish classic served hot or cold',
                'image': 'https://images.unsplash.com/photo-1601050690597-df0568f70950?w=400&h=300&fit=crop',
                'prep_time': '45 mins',
                'difficulty': 'Medium',
                'spice_level': 'None',
                'is_vegan': 0,
                'is_vegetarian': 1,
                'is_gluten_free': 1,
                'health_benefits': 'High in protein from eggs, provides potassium from potatoes, contains healthy fats',
                'ingredients': '6 large potatoes, thinly sliced|6 large eggs|1 large onion, thinly sliced|1 cup olive oil|Salt to taste|Fresh parsley for garnish',
                'steps': 'Heat olive oil in large skillet|Add sliced potatoes and onions|Cook slowly for 20 minutes until tender, not browned|Drain potatoes and onions, reserve oil|Beat eggs in large bowl|Add warm potatoes and onions to eggs|Season with salt and mix gently|Heat 2 tbsp reserved oil in same skillet|Pour in egg mixture and cook 8-10 minutes|Flip carefully using large plate|Cook 5 minutes more until set|Serve warm or at room temperature|Cut into wedges like a pie'
            },
            {
                'name': 'Goulash',
                'country': 'Hungary',
                'origin': 'Hungary',
                'cuisine_type': 'Hungarian Traditional',
                'description': 'Hearty beef stew with paprika, vegetables, and potatoes',
                'image': 'https://images.unsplash.com/photo-1563379091339-03246963d51a?w=400&h=300&fit=crop',
                'prep_time': '120 mins',
                'difficulty': 'Medium',
                'spice_level': 'Mild',
                'is_vegan': 0,
                'is_vegetarian': 0,
                'is_gluten_free': 1,
                'health_benefits': 'High in protein and iron, rich in vitamin C from peppers, contains antioxidants from paprika',
                'ingredients': '1kg beef chuck, cubed|3 large onions, chopped|3 tbsp Hungarian paprika|2 red bell peppers, chopped|3 tomatoes, chopped|4 potatoes, cubed|3 cloves garlic, minced|2 tbsp tomato paste|3 cups beef stock|2 tbsp vegetable oil|1 tsp caraway seeds|Salt and pepper|Sour cream for serving',
                'steps': 'Heat oil in large heavy pot|Brown beef cubes in batches|Remove beef and sauté onions until golden|Add paprika and cook for 1 minute|Return beef to pot|Add tomato paste, garlic, caraway seeds|Add chopped tomatoes and bell peppers|Pour in stock to cover|Bring to boil, then simmer covered 1 hour|Add potatoes and cook 30 minutes more|Season with salt and pepper|Serve hot with sour cream and crusty bread'
            }
        ]
        
        # More American regional dishes
        more_american_recipes = [
            {
                'name': 'New England Clam Chowder',
                'country': 'USA',
                'origin': 'New England, USA',
                'cuisine_type': 'American Regional',
                'description': 'Creamy white soup with clams, potatoes, and bacon',
                'image': 'https://images.unsplash.com/photo-1559847844-5315695dadae?w=400&h=300&fit=crop',
                'prep_time': '45 mins',
                'difficulty': 'Medium',
                'spice_level': 'None',
                'is_vegan': 0,
                'is_vegetarian': 0,
                'is_gluten_free': 0,
                'health_benefits': 'High in protein from clams, provides iodine, contains calcium from cream',
                'ingredients': '2 cans chopped clams with juice|6 slices bacon, diced|1 onion, diced|2 celery stalks, diced|3 potatoes, cubed|3 tbsp flour|2 cups milk|1 cup heavy cream|2 bay leaves|1 tsp thyme|Salt and pepper|Oyster crackers',
                'steps': 'Cook bacon in large pot until crispy|Remove bacon, leave fat in pot|Sauté onion and celery until soft|Add flour and cook 2 minutes|Gradually add clam juice, stirring constantly|Add potatoes, bay leaves, thyme|Simmer until potatoes are tender|Add clams, milk, and cream|Heat through but don\'t boil|Season with salt and pepper|Remove bay leaves|Serve hot with oyster crackers and crispy bacon'
            },
            {
                'name': 'Jambalaya',
                'country': 'USA',
                'origin': 'Louisiana, USA',
                'cuisine_type': 'American Creole',
                'description': 'Louisiana rice dish with sausage, shrimp, and the holy trinity',
                'image': 'https://images.unsplash.com/photo-1563379091339-03246963d51a?w=400&h=300&fit=crop',
                'prep_time': '60 mins',
                'difficulty': 'Medium',
                'spice_level': 'Medium',
                'is_vegan': 0,
                'is_vegetarian': 0,
                'is_gluten_free': 1,
                'health_benefits': 'High in protein, provides complex carbohydrates, contains antioxidants from vegetables and spices',
                'ingredients': '2 cups long-grain rice|500g andouille sausage, sliced|500g large shrimp|1 onion, diced|1 bell pepper, diced|2 celery stalks, diced|4 cloves garlic, minced|400g canned tomatoes|3 cups chicken stock|2 bay leaves|1 tsp paprika|1/2 tsp cayenne|1/4 tsp thyme|3 tbsp vegetable oil|Salt and pepper|Green onions',
                'steps': 'Cook sausage in large heavy pot until browned|Remove sausage, cook shrimp until pink|Remove shrimp, add vegetables to pot|Cook until soft, about 8 minutes|Add garlic and spices, cook 1 minute|Add tomatoes and cook 5 minutes|Add rice and stir to coat|Add stock and bring to boil|Return sausage to pot|Cover and simmer 18 minutes|Add shrimp in last 5 minutes|Remove bay leaves|Garnish with green onions'
            },
            {
                'name': 'Philly Cheesesteak',
                'country': 'USA',
                'origin': 'Philadelphia, USA',
                'cuisine_type': 'American Regional',
                'description': 'Sliced beef and cheese on a hoagie roll, Philadelphia\'s signature sandwich',
                'image': 'https://images.unsplash.com/photo-1565299624946-b28f40a0ca4b?w=400&h=300&fit=crop',
                'prep_time': '20 mins',
                'difficulty': 'Easy',
                'spice_level': 'None',
                'is_vegan': 0,
                'is_vegetarian': 0,
                'is_gluten_free': 0,
                'health_benefits': 'High in protein and iron, provides calcium from cheese, contains B vitamins',
                'ingredients': '1kg ribeye steak, thinly sliced|4 hoagie rolls|8 slices provolone or Cheez Whiz|2 onions, sliced|1 bell pepper, sliced|3 tbsp vegetable oil|Salt and pepper',
                'steps': 'Freeze steak for 30 minutes for easier slicing|Slice steak paper-thin against grain|Heat oil in large skillet over high heat|Cook onions and peppers until caramelized|Remove vegetables, add beef to pan|Cook quickly, stirring constantly for 2-3 minutes|Season with salt and pepper|Return vegetables to pan and mix|Split rolls and warm them|Fill rolls with meat mixture|Top with cheese while hot|Serve immediately while cheese is melted'
            },
            {
                'name': 'Buffalo Wings',
                'country': 'USA',
                'origin': 'Buffalo, New York',
                'cuisine_type': 'American Bar Food',
                'description': 'Spicy chicken wings with hot sauce and butter, served with blue cheese',
                'image': 'https://images.unsplash.com/photo-1544025162-d76694265947?w=400&h=300&fit=crop',
                'prep_time': '30 mins',
                'difficulty': 'Easy',
                'spice_level': 'Hot',
                'is_vegan': 0,
                'is_vegetarian': 0,
                'is_gluten_free': 1,
                'health_benefits': 'High in protein, provides B vitamins, contains capsaicin which may boost metabolism',
                'ingredients': '2kg chicken wings|1/2 cup hot sauce (Frank\'s RedHot)|1/4 cup butter|1 tbsp white vinegar|1/4 tsp garlic powder|Salt to taste|For blue cheese dip: 1/2 cup blue cheese|1/2 cup sour cream|1/4 cup mayonnaise|2 tbsp milk|Celery sticks',
                'steps': 'Preheat oven to 425°F (220°C)|Pat wings dry and season with salt|Arrange on wire rack over baking sheet|Bake 45 minutes until crispy|Meanwhile, melt butter in small saucepan|Whisk in hot sauce, vinegar, garlic powder|Make blue cheese dip by mixing all ingredients|Toss hot wings with sauce|Serve immediately with celery sticks and blue cheese dip|Provide extra napkins'
            },
            {
                'name': 'Fish Tacos',
                'country': 'USA',
                'origin': 'California, USA',
                'cuisine_type': 'Californian Mexican',
                'description': 'Grilled fish in soft tortillas with cabbage slaw and lime crema',
                'image': 'https://images.unsplash.com/photo-1565299624946-b28f40a0ca4b?w=400&h=300&fit=crop',
                'prep_time': '30 mins',
                'difficulty': 'Easy',
                'spice_level': 'Mild',
                'is_vegan': 0,
                'is_vegetarian': 0,
                'is_gluten_free': 1,
                'health_benefits': 'High in omega-3 fatty acids, contains fiber from cabbage, provides vitamin C',
                'ingredients': '600g white fish fillets|8 corn tortillas|2 cups cabbage, shredded|1/4 cup mayonnaise|1/4 cup sour cream|2 limes, juiced|1 tsp cumin|1 tsp chili powder|1/2 tsp paprika|Salt and pepper|Fresh cilantro|Avocado slices|Pico de gallo',
                'steps': 'Season fish with cumin, chili powder, paprika, salt, pepper|Grill fish for 4-5 minutes per side until flaky|Make lime crema by mixing mayo, sour cream, lime juice|Season crema with salt|Warm tortillas in dry pan|Flake fish into bite-sized pieces|Assemble tacos: tortilla, fish, cabbage|Top with lime crema, cilantro, avocado|Serve with pico de gallo and lime wedges|Best served immediately while warm'
            }
        ]
        
        # Canadian and Australian dishes
        anglo_western_recipes = [
            {
                'name': 'Poutine',
                'country': 'Canada',
                'origin': 'Quebec, Canada',
                'cuisine_type': 'Canadian Traditional',
                'description': 'French fries topped with cheese curds and gravy',
                'image': 'https://images.unsplash.com/photo-1601050690597-df0568f70950?w=400&h=300&fit=crop',
                'prep_time': '40 mins',
                'difficulty': 'Medium',
                'spice_level': 'None',
                'is_vegan': 0,
                'is_vegetarian': 1,
                'is_gluten_free': 0,
                'health_benefits': 'Provides energy from potatoes, contains calcium from cheese curds, comfort food in moderation',
                'ingredients': '1kg large potatoes|2 cups cheese curds|3 tbsp butter|3 tbsp flour|2 cups beef stock|1 tbsp soy sauce|Salt and pepper|Vegetable oil for frying',
                'steps': 'Cut potatoes into thick fries|Soak in cold water for 30 minutes|Make gravy: melt butter, whisk in flour|Gradually add stock, whisking constantly|Add soy sauce and simmer until thick|Season with salt and pepper|Heat oil to 350°F (175°C)|Fry chips twice: first at 325°F for 5 mins|Then at 375°F for 2-3 mins until golden|Drain and season with salt|Top hot fries with cheese curds|Pour hot gravy over top|Serve immediately while cheese melts'
            },
            {
                'name': 'Tourtière',
                'country': 'Canada',
                'origin': 'Quebec, Canada',
                'cuisine_type': 'Canadian Traditional',
                'description': 'Traditional French-Canadian meat pie, especially popular at Christmas',
                'image': 'https://images.unsplash.com/photo-1544025162-d76694265947?w=400&h=300&fit=crop',
                'prep_time': '90 mins',
                'difficulty': 'Medium',
                'spice_level': 'None',
                'is_vegan': 0,
                'is_vegetarian': 0,
                'is_gluten_free': 0,
                'health_benefits': 'High in protein, provides iron and B vitamins, contains healthy fats from pastry',
                'ingredients': '2 pie crusts|500g ground pork|250g ground beef|1 onion, minced|2 cloves garlic, minced|1 tsp sage|1/2 tsp thyme|1/4 tsp cloves|1/4 tsp cinnamon|1/2 cup chicken stock|Salt and pepper|1 egg for wash',
                'steps': 'Cook ground meats in large skillet until browned|Add onion and garlic, cook until soft|Add spices and cook 2 minutes|Add stock and simmer until liquid evaporates|Season with salt and pepper|Cool completely|Line pie dish with bottom crust|Fill with meat mixture|Cover with top crust and crimp edges|Cut vents in top|Brush with beaten egg|Bake at 425°F for 15 minutes|Reduce to 350°F and bake 30 minutes more|Cool 10 minutes before serving'
            },
            {
                'name': 'Meat Pie',
                'country': 'Australia',
                'origin': 'Australia',
                'cuisine_type': 'Australian Traditional',
                'description': 'Individual pastry filled with seasoned ground meat and gravy',
                'image': 'https://images.unsplash.com/photo-1544025162-d76694265947?w=400&h=300&fit=crop',
                'prep_time': '60 mins',
                'difficulty': 'Medium',
                'spice_level': 'None',
                'is_vegan': 0,
                'is_vegetarian': 0,
                'is_gluten_free': 0,
                'health_benefits': 'High in protein and iron, provides energy from pastry, contains B vitamins',
                'ingredients': '500g ground beef|1 onion, diced|2 cloves garlic, minced|2 tbsp tomato paste|1 tbsp Worcestershire sauce|1 cup beef stock|2 tbsp flour|2 tbsp vegetable oil|Salt and pepper|6 individual pie tins|2 sheets puff pastry|1 sheet shortcrust pastry|1 egg for wash',
                'steps': 'Heat oil in large pan, brown ground beef|Add onion and garlic, cook until soft|Stir in tomato paste and cook 2 minutes|Add Worcestershire sauce and flour|Gradually add stock, stirring constantly|Simmer until thickened|Season and cool completely|Line pie tins with shortcrust pastry|Fill with meat mixture|Top with puff pastry and crimp edges|Cut small vents in top|Brush with beaten egg|Bake at 400°F for 25 minutes until golden|Serve hot with tomato sauce'
            },
            {
                'name': 'Pavlova',
                'country': 'Australia',
                'origin': 'Australia/New Zealand',
                'cuisine_type': 'Australian Dessert',
                'description': 'Meringue cake topped with cream and fresh fruits',
                'image': 'https://images.unsplash.com/photo-1549007994-cb92caebd54b?w=400&h=300&fit=crop',
                'prep_time': '3 hours (with cooling)',
                'difficulty': 'Medium',
                'spice_level': 'None',
                'is_vegan': 0,
                'is_vegetarian': 1,
                'is_gluten_free': 1,
                'health_benefits': 'Contains vitamin C from fruits, provides calcium from cream, naturally gluten-free',
                'ingredients': '6 egg whites|1 1/2 cups superfine sugar|1 tsp vanilla extract|1 tsp white vinegar|2 tsp cornstarch|2 cups heavy cream|2 tbsp powdered sugar|Mixed fresh fruits: strawberries|kiwi|passionfruit|mango',
                'steps': 'Preheat oven to 300°F (150°C)|Beat egg whites until soft peaks form|Gradually add sugar, beating until stiff peaks form|Fold in vanilla, vinegar, and cornstarch|Spoon onto parchment-lined baking sheet|Shape into circle with shallow well|Bake 1 hour 15 minutes|Turn off oven, cool in oven with door ajar|Whip cream with powdered sugar|Top meringue with cream and fresh fruits|Serve immediately after assembling'
            },
            {
                'name': 'Maple Glazed Salmon',
                'country': 'Canada',
                'origin': 'Canada',
                'cuisine_type': 'Canadian Modern',
                'description': 'Fresh salmon with sweet maple syrup glaze and herbs',
                'image': 'https://images.unsplash.com/photo-1544025162-d76694265947?w=400&h=300&fit=crop',
                'prep_time': '25 mins',
                'difficulty': 'Easy',
                'spice_level': 'None',
                'is_vegan': 0,
                'is_vegetarian': 0,
                'is_gluten_free': 1,
                'health_benefits': 'Very high in omega-3 fatty acids, excellent source of protein, contains antioxidants',
                'ingredients': '4 salmon fillets|1/4 cup pure maple syrup|2 tbsp soy sauce|2 tbsp olive oil|2 cloves garlic, minced|1 tbsp fresh ginger, minced|1 tbsp Dijon mustard|Salt and pepper|Fresh dill|Lemon wedges',
                'steps': 'Preheat oven to 400°F (200°C)|Mix maple syrup, soy sauce, garlic, ginger, mustard|Season salmon with salt and pepper|Heat oil in oven-safe skillet|Sear salmon skin-side up for 3 minutes|Flip and brush with maple glaze|Transfer to oven for 8-10 minutes|Baste with glaze once more|Remove when fish flakes easily|Garnish with fresh dill|Serve with roasted vegetables and lemon wedges'
            }
        ]
        
        # Additional Italian classics
        more_italian_recipes = [
            {
                'name': 'Risotto',
                'country': 'Italy',
                'origin': 'Northern Italy',
                'cuisine_type': 'Italian Traditional',
                'description': 'Creamy rice dish cooked slowly with stock and finished with cheese',
                'image': 'https://images.unsplash.com/photo-1563379091339-03246963d51a?w=400&h=300&fit=crop',
                'prep_time': '40 mins',
                'difficulty': 'Medium',
                'spice_level': 'None',
                'is_vegan': 0,
                'is_vegetarian': 1,
                'is_gluten_free': 1,
                'health_benefits': 'Provides complex carbohydrates, contains calcium from cheese, source of B vitamins',
                'ingredients': '2 cups Arborio rice|6 cups warm chicken stock|1 onion, finely diced|1/2 cup white wine|1/2 cup Parmesan cheese, grated|3 tbsp butter|2 tbsp olive oil|Salt and pepper|Fresh parsley',
                'steps': 'Heat stock in separate saucepan and keep warm|Heat oil in large heavy pan|Sauté onion until translucent|Add rice and stir for 2 minutes until coated|Add wine and stir until absorbed|Add warm stock one ladle at a time|Stir constantly, adding more stock as absorbed|Continue for 18-20 minutes until rice is creamy|Stir in butter and Parmesan|Season with salt and pepper|Garnish with parsley and serve immediately'
            },
            {
                'name': 'Osso Buco',
                'country': 'Italy',
                'origin': 'Milan, Italy',
                'cuisine_type': 'Italian Traditional',
                'description': 'Braised veal shanks with vegetables, white wine, and broth',
                'image': 'https://images.unsplash.com/photo-1544025162-d76694265947?w=400&h=300&fit=crop',
                'prep_time': '150 mins',
                'difficulty': 'Medium',
                'spice_level': 'None',
                'is_vegan': 0,
                'is_vegetarian': 0,
                'is_gluten_free': 0,
                'health_benefits': 'High in protein and collagen, rich in iron, provides B vitamins and minerals',
                'ingredients': '4 veal shanks, thick cut|1/2 cup flour|1 onion, diced|1 carrot, diced|1 celery stalk, diced|3 cloves garlic, minced|1 cup white wine|2 cups beef stock|400g canned tomatoes|2 bay leaves|Fresh thyme|4 tbsp olive oil|Salt and pepper|Gremolata: lemon zest|garlic|parsley',
                'steps': 'Season veal shanks and dredge in flour|Heat oil in heavy Dutch oven|Brown shanks on all sides|Remove shanks and sauté vegetables until soft|Add garlic and cook 1 minute|Add wine and cook until reduced by half|Return shanks to pot|Add tomatoes, stock, herbs|Bring to simmer, cover and braise 1.5 hours|Turn shanks halfway through|Make gremolata by mixing lemon zest, minced garlic, parsley|Serve shanks with sauce|Garnish with gremolata|Traditionally served with risotto alla milanese'
            }
        ]
        
        # Combine all recipes including new Western dishes
        all_recipes = (all_african_recipes + european_recipes + asian_recipes + american_recipes + 
                      global_recipes + korean_recipes + brazilian_recipes + vietnamese_recipes + 
                      french_recipes + more_european_recipes + more_american_recipes + 
                      anglo_western_recipes + more_italian_recipes)
        
        for recipe in all_recipes:
            conn.execute('''
                INSERT INTO recipes (name, country, origin, cuisine_type, description, image, prep_time, difficulty, spice_level, is_vegan, is_vegetarian, is_gluten_free, health_benefits, ingredients, steps)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (recipe['name'], recipe['country'], recipe['origin'], recipe['cuisine_type'], recipe['description'], recipe['image'], 
                  recipe['prep_time'], recipe['difficulty'], recipe['spice_level'], recipe['is_vegan'], recipe['is_vegetarian'], 
                  recipe['is_gluten_free'], recipe['health_benefits'], recipe['ingredients'], recipe['steps']))
    
    conn.commit()
    conn.close()

def format_recipe(row):
    """Convert database row to recipe dictionary"""
    return {
        'id': row['id'],
        'name': row['name'],
        'country': row['country'],
        'origin': row['origin'] if 'origin' in row.keys() else '',
        'cuisine_type': row['cuisine_type'] if 'cuisine_type' in row.keys() else '',
        'description': row['description'],
        'image': row['image'],
        'prep_time': row['prep_time'],
        'difficulty': row['difficulty'],
        'spice_level': row['spice_level'] if 'spice_level' in row.keys() else '',
        'is_vegan': bool(row['is_vegan']) if 'is_vegan' in row.keys() else False,
        'is_vegetarian': bool(row['is_vegetarian']) if 'is_vegetarian' in row.keys() else False,
        'is_gluten_free': bool(row['is_gluten_free']) if 'is_gluten_free' in row.keys() else False,
        'health_benefits': row['health_benefits'],
        'ingredients': row['ingredients'].split('|') if row['ingredients'] else [],
        'steps': row['steps'].split('|') if row['steps'] else []
    }

@app.route('/')
def index():
    """Serve the main page"""
    return render_template('index.html')

@app.route('/login')
def login_page():
    """Serve the login page"""
    return render_template('login.html')

@app.route('/signup')
def signup_page():
    """Serve the signup page"""
    return render_template('signup.html')

@app.route('/api/login', methods=['POST'])
def api_login():
    """Handle user login"""
    data = request.get_json()
    
    if not data or 'email' not in data or 'password' not in data:
        return jsonify({'error': 'Email and password are required'}), 400
    
    email = data['email'].lower().strip()
    password = data['password']
    
    # Get user from database
    conn = get_db_connection()
    user = conn.execute(
        'SELECT * FROM users WHERE email = ? AND is_active = 1', 
        (email,)
    ).fetchone()
    conn.close()
    
    if user and verify_password(password, user['password_hash']):
        # Create session
        session['user_id'] = user['id']
        session['user_email'] = user['email']
        session['user_name'] = f"{user['first_name']} {user['last_name']}"
        
        return jsonify({
            'success': True,
            'user': {
                'id': user['id'],
                'email': user['email'],
                'first_name': user['first_name'],
                'last_name': user['last_name'],
                'cuisine_preferences': user['cuisine_preferences']
            }
        })
    else:
        return jsonify({'error': 'Invalid email or password'}), 401

@app.route('/api/signup', methods=['POST'])
def api_signup():
    """Handle user registration"""
    data = request.get_json()
    
    required_fields = ['firstName', 'lastName', 'email', 'password']
    if not data or not all(field in data for field in required_fields):
        return jsonify({'error': 'All fields are required'}), 400
    
    email = data['email'].lower().strip()
    password = data['password']
    first_name = data['firstName'].strip()
    last_name = data['lastName'].strip()
    cuisine_preferences = ','.join(data.get('cuisinePreferences', []))
    newsletter_subscribed = 1 if data.get('newsletter', False) else 0
    
    # Validate password strength
    if len(password) < 8:
        return jsonify({'error': 'Password must be at least 8 characters long'}), 400
    
    # Check if user already exists
    conn = get_db_connection()
    existing_user = conn.execute(
        'SELECT email FROM users WHERE email = ?', 
        (email,)
    ).fetchone()
    
    if existing_user:
        conn.close()
        return jsonify({'error': 'Email address is already registered'}), 409
    
    # Hash password and create user
    password_hash = hash_password(password)
    
    try:
        conn.execute(
            '''INSERT INTO users (email, password_hash, first_name, last_name, 
                                 cuisine_preferences, newsletter_subscribed)
               VALUES (?, ?, ?, ?, ?, ?)''',
            (email, password_hash, first_name, last_name, cuisine_preferences, newsletter_subscribed)
        )
        conn.commit()
        
        # Get the created user
        user = conn.execute(
            'SELECT * FROM users WHERE email = ?', 
            (email,)
        ).fetchone()
        conn.close()
        
        # Create session
        session['user_id'] = user['id']
        session['user_email'] = user['email']
        session['user_name'] = f"{user['first_name']} {user['last_name']}"
        
        return jsonify({
            'success': True,
            'user': {
                'id': user['id'],
                'email': user['email'],
                'first_name': user['first_name'],
                'last_name': user['last_name'],
                'cuisine_preferences': user['cuisine_preferences']
            }
        }), 201
        
    except Exception as e:
        conn.close()
        return jsonify({'error': 'Registration failed. Please try again.'}), 500

@app.route('/api/logout', methods=['POST'])
def api_logout():
    """Handle user logout"""
    session.clear()
    return jsonify({'success': True})

@app.route('/api/user')
def get_current_user():
    """Get current logged-in user information"""
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    conn = get_db_connection()
    user = conn.execute(
        'SELECT id, email, first_name, last_name, cuisine_preferences, created_at FROM users WHERE id = ?',
        (session['user_id'],)
    ).fetchone()
    conn.close()
    
    if user:
        return jsonify({
            'id': user['id'],
            'email': user['email'],
            'first_name': user['first_name'],
            'last_name': user['last_name'],
            'cuisine_preferences': user['cuisine_preferences'],
            'created_at': user['created_at']
        })
    else:
        session.clear()
        return jsonify({'error': 'User not found'}), 404

def hash_password(password):
    """Hash a password using SHA-256 with salt"""
    salt = os.urandom(32)
    pwd_hash = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 100000)
    return salt + pwd_hash

def verify_password(password, hashed):
    """Verify a password against its hash"""
    salt = hashed[:32]
    pwd_hash = hashed[32:]
    pwd_check = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 100000)
    return pwd_hash == pwd_check

def find_or_create_oauth_user(email, first_name, last_name, provider, oauth_id, avatar_url=None):
    """Find existing OAuth user or create new one"""
    conn = get_db_connection()
    
    # First, try to find user by email
    user = conn.execute(
        'SELECT * FROM users WHERE email = ?', (email,)
    ).fetchone()
    
    if user:
        # Update OAuth info if user exists
        conn.execute(
            '''UPDATE users SET oauth_provider = ?, oauth_id = ?, avatar_url = ? 
               WHERE email = ?''',
            (provider, oauth_id, avatar_url, email)
        )
        conn.commit()
    else:
        # Create new OAuth user
        conn.execute(
            '''INSERT INTO users (email, first_name, last_name, oauth_provider, 
                                 oauth_id, avatar_url, password_hash)
               VALUES (?, ?, ?, ?, ?, ?, NULL)''',
            (email, first_name, last_name, provider, oauth_id, avatar_url)
        )
        conn.commit()
        
        # Get the newly created user
        user = conn.execute(
            'SELECT * FROM users WHERE email = ?', (email,)
        ).fetchone()
    
    conn.close()
    return user

def create_user_session(user):
    """Create user session"""
    session['user_id'] = user['id']
    session['user_email'] = user['email']
    session['user_name'] = f"{user['first_name']} {user['last_name']}"
    session['oauth_provider'] = user['oauth_provider']

# OAuth Routes
@app.route('/auth/google')
def google_login():
    """Redirect to Google OAuth"""
    redirect_uri = url_for('google_callback', _external=True)
    return google.authorize_redirect(redirect_uri)

@app.route('/auth/google/callback')
def google_callback():
    """Handle Google OAuth callback"""
    try:
        token = google.authorize_access_token()
        user_info = token.get('userinfo')
        
        if user_info:
            user = find_or_create_oauth_user(
                email=user_info['email'],
                first_name=user_info.get('given_name', ''),
                last_name=user_info.get('family_name', ''),
                provider='google',
                oauth_id=user_info['sub'],
                avatar_url=user_info.get('picture')
            )
            
            create_user_session(user)
            return redirect('/')
        else:
            return redirect('/login?error=oauth_failed')
            
    except Exception as e:
        print(f"Google OAuth error: {e}")
        return redirect('/login?error=oauth_failed')

@app.route('/auth/facebook')
def facebook_login():
    """Redirect to Facebook OAuth"""
    redirect_uri = url_for('facebook_callback', _external=True)
    return facebook.authorize_redirect(redirect_uri)

@app.route('/auth/facebook/callback')
def facebook_callback():
    """Handle Facebook OAuth callback"""
    try:
        token = facebook.authorize_access_token()
        
        # Get user info from Facebook Graph API
        resp = facebook.get('me?fields=id,email,first_name,last_name,picture', token=token)
        user_info = resp.json()
        
        if user_info and 'email' in user_info:
            user = find_or_create_oauth_user(
                email=user_info['email'],
                first_name=user_info.get('first_name', ''),
                last_name=user_info.get('last_name', ''),
                provider='facebook',
                oauth_id=user_info['id'],
                avatar_url=user_info.get('picture', {}).get('data', {}).get('url')
            )
            
            create_user_session(user)
            return redirect('/')
        else:
            return redirect('/login?error=oauth_failed')
            
    except Exception as e:
        print(f"Facebook OAuth error: {e}")
        return redirect('/login?error=oauth_failed')

@app.route('/api/recipes')
def get_all_recipes():
    """Get all recipes"""
    conn = get_db_connection()
    recipes = conn.execute('SELECT * FROM recipes ORDER BY name').fetchall()
    conn.close()
    
    return jsonify([format_recipe(recipe) for recipe in recipes])

@app.route('/api/search')
def search_recipes():
    """Search recipes by name, country, origin, cuisine type, or description"""
    query = request.args.get('q', '').lower()
    
    if not query:
        return get_all_recipes()
    
    conn = get_db_connection()
    recipes = conn.execute('''
        SELECT * FROM recipes 
        WHERE LOWER(name) LIKE ? 
           OR LOWER(country) LIKE ? 
           OR LOWER(origin) LIKE ?
           OR LOWER(cuisine_type) LIKE ?
           OR LOWER(description) LIKE ?
           OR LOWER(ingredients) LIKE ?
        ORDER BY name
    ''', (f'%{query}%', f'%{query}%', f'%{query}%', f'%{query}%', f'%{query}%', f'%{query}%')).fetchall()
    conn.close()
    
    return jsonify([format_recipe(recipe) for recipe in recipes])

@app.route('/api/surprise')
def surprise_recipes():
    """Get 6 random recipes"""
    conn = get_db_connection()
    recipes = conn.execute('SELECT * FROM recipes ORDER BY RANDOM() LIMIT 6').fetchall()
    conn.close()
    
    return jsonify([format_recipe(recipe) for recipe in recipes])

@app.route('/api/recipe/<int:recipe_id>')
def get_recipe_details(recipe_id):
    """Get detailed information for a specific recipe"""
    conn = get_db_connection()
    recipe = conn.execute('SELECT * FROM recipes WHERE id = ?', (recipe_id,)).fetchone()
    conn.close()
    
    if recipe:
        return jsonify(format_recipe(recipe))
    else:
        return jsonify({'error': 'Recipe not found'}), 404

@app.route('/api/countries')
def get_countries():
    """Get list of all countries represented in recipes"""
    conn = get_db_connection()
    countries = conn.execute('SELECT DISTINCT country FROM recipes ORDER BY country').fetchall()
    conn.close()
    
    return jsonify([country['country'] for country in countries])

@app.route('/api/cuisines')
def get_cuisines():
    """Get list of all cuisine types represented in recipes"""
    conn = get_db_connection()
    cuisines = conn.execute('SELECT DISTINCT cuisine_type FROM recipes ORDER BY cuisine_type').fetchall()
    conn.close()
    
    return jsonify([cuisine['cuisine_type'] for cuisine in cuisines])

# Authentication decorator
def require_auth(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'error': 'Authentication required'}), 401
        return f(*args, **kwargs)
    return decorated_function



# Rating System Endpoints
@app.route('/api/rate-recipe', methods=['POST'])
@require_auth
def rate_recipe_frontend():
    """Add or update a rating for a recipe (frontend compatible endpoint)"""
    data = request.get_json()
    
    if not data or 'recipe_id' not in data or 'rating' not in data:
        return jsonify({'error': 'Recipe ID and rating are required'}), 400
    
    recipe_id = data['recipe_id']
    rating = data['rating']
    review_text = data.get('review', '').strip()
    recipe_type = 'regular'  # Only handle regular recipes
    
    # Validate rating
    if not isinstance(rating, int) or rating < 1 or rating > 5:
        return jsonify({'error': 'Rating must be between 1 and 5'}), 400
    
    # Validate recipe exists
    conn = get_db_connection()
    
    recipe_exists = conn.execute(
        'SELECT id FROM recipes WHERE id = ?', 
        (recipe_id,)
    ).fetchone()
    
    if not recipe_exists:
        conn.close()
        return jsonify({'error': 'Recipe not found'}), 404
    
    try:
        # Insert or update rating
        conn.execute('''
            INSERT INTO recipe_ratings (recipe_id, recipe_type, user_id, rating, review_text)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(recipe_id, recipe_type, user_id) DO UPDATE SET
            rating = excluded.rating,
            review_text = excluded.review_text,
            updated_at = CURRENT_TIMESTAMP
        ''', (str(recipe_id), recipe_type, session['user_id'], rating, review_text))
        
        conn.commit()
        
        # Get updated statistics
        rating_stats = conn.execute('''
            SELECT 
                AVG(rating) as average_rating,
                COUNT(*) as rating_count
            FROM recipe_ratings 
            WHERE recipe_id = ? AND recipe_type = ?
        ''', (str(recipe_id), recipe_type)).fetchone()
        
        conn.close()
        
        return jsonify({
            'success': True,
            'message': 'Rating saved successfully',
            'average_rating': round(rating_stats['average_rating'], 1) if rating_stats['average_rating'] else rating,
            'rating_count': rating_stats['rating_count']
        })
        
    except Exception as e:
        conn.close()
        print(f"Rating error: {e}")
        return jsonify({'error': 'Failed to save rating'}), 500

@app.route('/api/ratings/<int:recipe_id>', methods=['POST'])
@require_auth
def rate_recipe(recipe_id):
    """Add or update a rating for a recipe"""
    data = request.get_json()
    
    if not data or 'rating' not in data:
        return jsonify({'error': 'Rating is required'}), 400
    
    rating = data['rating']
    review_text = data.get('review', '').strip()
    recipe_type = data.get('recipe_type', 'regular')  # 'regular' or 'ai'
    
    # Validate rating
    if not isinstance(rating, int) or rating < 1 or rating > 5:
        return jsonify({'error': 'Rating must be between 1 and 5'}), 400
    
    # Validate recipe exists
    conn = get_db_connection()
    
    recipe_exists = conn.execute(
        'SELECT id FROM recipes WHERE id = ?', 
        (recipe_id,)
    ).fetchone()
    
    if not recipe_exists:
        conn.close()
        return jsonify({'error': 'Recipe not found'}), 404
    
    try:
        # Insert or update rating
        conn.execute('''
            INSERT INTO recipe_ratings (recipe_id, recipe_type, user_id, rating, review_text)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(recipe_id, recipe_type, user_id) DO UPDATE SET
            rating = excluded.rating,
            review_text = excluded.review_text,
            updated_at = CURRENT_TIMESTAMP
        ''', (recipe_id, recipe_type, session['user_id'], rating, review_text))
        
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True,
            'message': 'Rating saved successfully'
        })
        
    except Exception as e:
        conn.close()
        return jsonify({'error': 'Failed to save rating'}), 500

@app.route('/api/ratings/<int:recipe_id>')
def get_recipe_ratings(recipe_id):
    """Get ratings and reviews for a recipe"""
    recipe_type = request.args.get('recipe_type', 'regular')
    
    conn = get_db_connection()
    
    # Get average rating and count
    rating_stats = conn.execute('''
        SELECT 
            AVG(rating) as average_rating,
            COUNT(*) as total_ratings
        FROM recipe_ratings 
        WHERE recipe_id = ? AND recipe_type = ?
    ''', (recipe_id, recipe_type)).fetchone()
    
    # Get individual reviews
    reviews = conn.execute('''
        SELECT 
            rr.rating,
            rr.review_text,
            rr.created_at,
            u.first_name,
            u.last_name
        FROM recipe_ratings rr
        JOIN users u ON rr.user_id = u.id
        WHERE rr.recipe_id = ? AND rr.recipe_type = ?
        ORDER BY rr.created_at DESC
        LIMIT 10
    ''', (recipe_id, recipe_type)).fetchall()
    
    # Get user's own rating if logged in
    user_rating = None
    if 'user_id' in session:
        user_rating = conn.execute('''
            SELECT rating, review_text 
            FROM recipe_ratings 
            WHERE recipe_id = ? AND recipe_type = ? AND user_id = ?
        ''', (recipe_id, recipe_type, session['user_id'])).fetchone()
    
    conn.close()
    
    return jsonify({
        'average_rating': round(rating_stats['average_rating'], 1) if rating_stats['average_rating'] else None,
        'total_ratings': rating_stats['total_ratings'],
        'user_rating': {
            'rating': user_rating['rating'],
            'review': user_rating['review_text']
        } if user_rating else None,
        'reviews': [
            {
                'rating': review['rating'],
                'review_text': review['review_text'],
                'author_name': f"{review['first_name']} {review['last_name']}",
                'created_at': review['created_at']
            }
            for review in reviews if review['review_text']
        ]
    })

@app.route('/api/user/ratings')
@require_auth
def get_user_ratings():
    """Get all ratings by the current user"""
    conn = get_db_connection()
    
    ratings = conn.execute('''
        SELECT 
            rr.recipe_id,
            rr.recipe_type,
            rr.rating,
            rr.review_text,
            rr.created_at,
            r.name as recipe_name
        FROM recipe_ratings rr
        LEFT JOIN recipes r ON rr.recipe_id = r.id AND rr.recipe_type = 'regular'
        WHERE rr.user_id = ?
        ORDER BY rr.created_at DESC
    ''', (session['user_id'],)).fetchall()
    
    conn.close()
    
    return jsonify([
        {
            'recipe_id': rating['recipe_id'],
            'recipe_type': rating['recipe_type'],
            'recipe_name': rating['recipe_name'],
            'rating': rating['rating'],
            'review_text': rating['review_text'],
            'created_at': rating['created_at']
        }
        for rating in ratings
    ])


if __name__ == '__main__':
    # Initialize database on startup
    init_database()
    
    # Production vs Development settings
    debug_mode = os.getenv('FLASK_ENV') != 'production'
    port = int(os.getenv('PORT', 5000))
    
    if debug_mode:
        print("🍳 Recipe Recommender Server Starting (Development Mode)...")
        print("🌐 Navigate to http://localhost:5000 to view the app")
    else:
        print("🍳 Recipe Recommender Server Starting (Production Mode)...")
    
    print("🌟 Features: Search, Voice Search, Surprise Me, Favorites, Recipe Ratings")
    print("📊 Global Recipes: Kenyan, African, Asian, European, American cuisines")
    
    app.run(debug=debug_mode, host='0.0.0.0', port=port)
