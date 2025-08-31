# 🍳 Global Recipe Recommender

A vibrant, user-friendly web application that showcases recipes from around the world with advanced search capabilities, voice search, and a favorites system.

## ✨ Features

- 🌍 **Global Recipe Collection**: Discover recipes from different countries
- 🔍 **Advanced Search**: Search by recipe name, country, ingredients, or cuisine type  
- 🎤 **Voice Search**: Use voice commands to search for recipes
- 🎲 **Surprise Me**: Get 6 random recipes at the click of a button
- ❤️ **Favorites System**: Save and manage your favorite recipes
- 🖼️ **Dynamic Backgrounds**: Animated food images that change every 10 seconds
- 📱 **Responsive Design**: Works on desktop, tablet, and mobile devices
- 🏥 **Health Information**: View health benefits for each recipe
- 📋 **Detailed Instructions**: Step-by-step cooking instructions with ingredients

## 🚀 Quick Start

### Prerequisites
- Python 3.7 or higher
- Modern web browser (Chrome, Firefox, Safari, Edge)

### Installation & Setup

1. **Navigate to the project directory**:
   ```bash
   cd recipe-recommender
   ```

2. **Run the setup script**:
   ```bash
   python run_app.py
   ```
   
   This will:
   - Install required Python packages
   - Initialize the SQLite database with sample recipes
   - Start the Flask development server

3. **Open your browser** and navigate to:
   ```
   http://localhost:5000
   ```

### Manual Setup (Alternative)

If you prefer to set up manually:

1. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Start the server**:
   ```bash
   cd backend
   python app.py
   ```

## 🏗️ Project Structure

```
recipe-recommender/
├── templates/
│   └── index.html          # Main HTML template
├── static/
│   ├── css/
│   │   └── style.css       # Vibrant styling with animations
│   ├── js/
│   │   └── app.js          # Frontend JavaScript functionality
│   └── images/             # Static images (if needed)
├── backend/
│   └── app.py              # Flask backend server
├── database/
│   └── recipes.db          # SQLite database (auto-created)
├── requirements.txt        # Python dependencies
├── run_app.py             # Setup and run script
└── README.md              # This file
```

## 🎯 Usage

### Search Functionality
- **Text Search**: Type in the search box and press Enter or click the search button
- **Voice Search**: Click the microphone button and speak your search query
- **Auto-scroll**: Results automatically scroll into view after searching

### Surprise Me Feature
- Click the "Surprise Me!" button to get 6 random recipes
- Perfect for discovering new cuisines and dishes

### Favorites Management
- Click the heart icon on any recipe card to add/remove from favorites
- Switch to the "Favorites" tab to view your saved recipes
- Favorites are stored locally in your browser

### Recipe Details
- Click on any recipe card to view detailed information
- Includes health benefits, ingredients list, and step-by-step instructions
- Modal popup with easy-to-read formatting

## 🛠️ Technology Stack

- **Frontend**: HTML5, CSS3, JavaScript (ES6+)
- **Backend**: Python Flask
- **Database**: SQLite
- **Styling**: Custom CSS with CSS Grid and Flexbox
- **Icons**: Font Awesome
- **Images**: Unsplash API for high-quality food photos

## 🎨 Design Features

- **Vibrant Color Scheme**: Eye-catching gradients and modern colors
- **Animated Backgrounds**: Food images that cycle every 10 seconds
- **Responsive Design**: Optimized for all screen sizes
- **Smooth Animations**: Hover effects and transitions
- **Glassmorphism Effects**: Modern UI with backdrop blur effects

## 🌐 API Endpoints

- `GET /` - Main application page
- `GET /api/recipes` - Get all recipes
- `GET /api/search?q={query}` - Search recipes
- `GET /api/surprise` - Get 6 random recipes
- `GET /api/recipe/{id}` - Get detailed recipe information
- `GET /api/countries` - Get list of all countries

## 🔧 Customization

### Adding New Recipes
Recipes are stored in the SQLite database. You can add new recipes by modifying the `sample_recipes` list in `backend/app.py` and restarting the server.

### Changing Background Images
Update the CSS background images in `static/css/style.css` in the `.slide:nth-child()` selectors.

### Modifying Colors
The color scheme can be customized by updating the CSS custom properties and gradient values in the CSS file.

## 🐛 Troubleshooting

### Voice Search Not Working
- Ensure you're using HTTPS or localhost
- Grant microphone permissions in your browser
- Voice search requires a modern browser with Web Speech API support

### Database Issues
- Delete `database/recipes.db` and restart the server to reset the database
- Check file permissions in the database directory

### Port Already in Use
- Change the port in `backend/app.py` by modifying the `app.run()` call
- Or stop any other services running on port 5000

## 📝 Future Enhancements

- User authentication and personal recipe collections
- Recipe rating and review system
- Nutritional information calculator
- Shopping list generator
- Recipe sharing functionality
- Integration with external recipe APIs
- Meal planning features

## 🤝 Contributing

Feel free to contribute to this project by:
- Adding new recipes to the database
- Improving the UI/UX design
- Adding new features
- Fixing bugs or improving performance

---

Enjoy exploring recipes from around the world! 🌍👨‍🍳👩‍🍳
