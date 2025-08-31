class RecipeApp {
    constructor() {
        this.recipes = [];
        this.filteredRecipes = [];
        this.favorites = JSON.parse(localStorage.getItem('favoriteRecipes')) || [];
        this.currentTab = 'all';
        this.recognition = null;
        this.currentSlide = 0;
        this.currentUser = null;
        this.aiGeneratedRecipes = JSON.parse(localStorage.getItem('aiGeneratedRecipes')) || [];
        this.userIngredients = [];
        this.filters = {
            difficulty: '',
            spiceLevel: '',
            cuisineType: '',
            vegan: false,
            vegetarian: false,
            glutenFree: false
        };
        
        this.init();
    }

    init() {
        this.bindEvents();
        this.initAuth();
        this.initBackgroundSlideshow();
        this.initVoiceSearch();
        this.loadAllRecipes();
        this.initFilters();
        this.initScrollEffects();
        this.initParticleEffect();
        this.initAIGenerator();
    }

    bindEvents() {
        // Search functionality
        document.getElementById('searchBtn').addEventListener('click', () => this.performSearch());
        document.getElementById('searchInput').addEventListener('keypress', (e) => {
            if (e.key === 'Enter') this.performSearch();
        });

        // Voice search
        document.getElementById('voiceBtn').addEventListener('click', () => this.toggleVoiceSearch());

        // Surprise me button
        document.getElementById('surpriseBtn').addEventListener('click', () => this.surpriseMe());

        // Tab switching
        document.querySelectorAll('.tab-btn').forEach(btn => {
            btn.addEventListener('click', (e) => this.switchTab(e.target.dataset.tab));
        });

        // Modal controls
        document.querySelector('.close-btn').addEventListener('click', () => this.closeModal());
        document.getElementById('recipeModal').addEventListener('click', (e) => {
            if (e.target.id === 'recipeModal') this.closeModal();
        });

        // Scroll to top button
        document.getElementById('scrollToTop').addEventListener('click', () => this.scrollToTop());
        
        // AI Recipe Generator
        document.getElementById('addIngredientBtn').addEventListener('click', () => this.addIngredient());
        document.getElementById('ingredientInput').addEventListener('keypress', (e) => {
            if (e.key === 'Enter') this.addIngredient();
        });
        document.getElementById('generateRecipeBtn').addEventListener('click', () => this.generateAIRecipe());
    }

    initBackgroundSlideshow() {
        const slides = document.querySelectorAll('.slide');
        
        setInterval(() => {
            slides[this.currentSlide].classList.remove('active');
            this.currentSlide = (this.currentSlide + 1) % slides.length;
            slides[this.currentSlide].classList.add('active');
        }, 10000); // Change every 10 seconds
    }

    initVoiceSearch() {
        if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
            const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
            this.recognition = new SpeechRecognition();
            this.recognition.continuous = false;
            this.recognition.interimResults = false;
            this.recognition.lang = 'en-US';

            this.recognition.onresult = (event) => {
                const transcript = event.results[0][0].transcript;
                document.getElementById('searchInput').value = transcript;
                this.performSearch();
                this.hideVoiceIndicator();
            };

            this.recognition.onerror = () => {
                this.hideVoiceIndicator();
                alert('Voice search failed. Please try again or use text search.');
            };

            this.recognition.onend = () => {
                this.hideVoiceIndicator();
            };
        } else {
            document.getElementById('voiceBtn').style.display = 'none';
        }
    }

    toggleVoiceSearch() {
        if (this.recognition) {
            if (document.getElementById('voiceBtn').classList.contains('listening')) {
                this.recognition.stop();
                this.hideVoiceIndicator();
            } else {
                this.showVoiceIndicator();
                this.recognition.start();
            }
        }
    }

    showVoiceIndicator() {
        document.getElementById('voiceBtn').classList.add('listening');
        
        const indicator = document.createElement('div');
        indicator.className = 'voice-search-indicator';
        indicator.innerHTML = `
            <i class="fas fa-microphone"></i>
            <h3>Listening...</h3>
            <p>Say something like "chicken curry" or "Italian pasta"</p>
        `;
        document.body.appendChild(indicator);
    }

    hideVoiceIndicator() {
        document.getElementById('voiceBtn').classList.remove('listening');
        const indicator = document.querySelector('.voice-search-indicator');
        if (indicator) {
            indicator.remove();
        }
    }

    async loadAllRecipes() {
        this.showLoading();
        try {
            const response = await fetch('/api/recipes');
            this.recipes = await response.json();
            this.displayRecipes(this.recipes);
        } catch (error) {
            console.error('Error loading recipes:', error);
            this.showError('Failed to load recipes. Please try again.');
        }
        this.hideLoading();
    }

    async performSearch() {
        const query = document.getElementById('searchInput').value.trim();
        if (!query) {
            this.displayRecipes(this.recipes);
            return;
        }

        this.showLoading();
        this.scrollToResults();

        try {
            const response = await fetch(`/api/search?q=${encodeURIComponent(query)}`);
            const results = await response.json();
            this.displayRecipes(results);
        } catch (error) {
            console.error('Error searching recipes:', error);
            this.showError('Search failed. Please try again.');
        }
        this.hideLoading();
    }

    async surpriseMe() {
        this.showLoading();
        this.scrollToResults();

        try {
            const response = await fetch('/api/surprise');
            const surpriseRecipes = await response.json();
            this.displayRecipes(surpriseRecipes);
        } catch (error) {
            console.error('Error getting surprise recipes:', error);
            this.showError('Failed to get surprise recipes. Please try again.');
        }
        this.hideLoading();
    }

    switchTab(tab) {
        // Update active tab
        document.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('active'));
        document.querySelector(`[data-tab="${tab}"]`).classList.add('active');
        
        this.currentTab = tab;
        
        if (tab === 'favorites') {
            this.displayFavorites();
        } else if (tab === 'ai-generated') {
            this.displayAIGeneratedRecipes();
        } else {
            this.displayRecipes(this.recipes);
        }
    }

    displayRecipes(recipes) {
        const container = document.getElementById('recipesContainer');
        
        if (!recipes || recipes.length === 0) {
            container.innerHTML = `
                <div class="empty-state">
                    <i class="fas fa-search"></i>
                    <h3>No recipes found</h3>
                    <p>Try adjusting your search terms or click "Surprise Me!" for random recipes</p>
                </div>
            `;
            return;
        }

        container.innerHTML = recipes.map(recipe => this.createRecipeCard(recipe)).join('');
        
        // Bind favorite buttons
        container.querySelectorAll('.favorite-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.stopPropagation();
                this.toggleFavorite(btn.dataset.recipeId);
            });
        });

        // Bind recipe cards
        container.querySelectorAll('.recipe-card').forEach(card => {
            card.addEventListener('click', () => this.showRecipeDetails(card.dataset.recipeId));
        });
        
        // Trigger scroll animations for new recipe cards
        setTimeout(() => {
            this.observeRecipeCards();
        }, 50);
    }

    displayFavorites() {
        const favoriteRecipes = this.recipes.filter(recipe => 
            this.favorites.includes(recipe.id.toString())
        );
        this.displayRecipes(favoriteRecipes);
    }

    createRecipeCard(recipe) {
        const isFavorited = this.favorites.includes(recipe.id.toString());
        
        // Create badges for dietary information
        const badges = [];
        if (recipe.is_vegan) badges.push('<span class="badge vegan"><i class="fas fa-leaf"></i> Vegan</span>');
        else if (recipe.is_vegetarian) badges.push('<span class="badge vegetarian"><i class="fas fa-seedling"></i> Vegetarian</span>');
        if (recipe.is_gluten_free) badges.push('<span class="badge gluten-free"><i class="fas fa-wheat"></i> Gluten-Free</span>');
        
        // Spice level badge
        if (recipe.spice_level && recipe.spice_level !== 'None') {
            const spiceClass = `spice-${recipe.spice_level.toLowerCase()}`;
            badges.push(`<span class="badge ${spiceClass}"><i class="fas fa-pepper-hot"></i> ${recipe.spice_level}</span>`);
        }
        
        // AI Generated badge
        if (recipe.isAIGenerated) {
            badges.push('<span class="badge ai-generated"><i class="fas fa-robot"></i> AI Generated</span>');
        }
        
        // Rating information
        const averageRating = recipe.rating?.average || 0;
        const ratingCount = recipe.rating?.count || 0;
        const userRating = recipe.userRating || 0;
        
        return `
            <div class="recipe-card" data-recipe-id="${recipe.id}">
                <img src="${recipe.image || 'https://via.placeholder.com/350x200?text=Recipe+Image'}" alt="${recipe.name}" class="recipe-image" 
                     onerror="this.src='https://via.placeholder.com/350x200?text=Recipe+Image'">
                <div class="recipe-content">
                    <div class="recipe-header">
                        <div>
                            <h3 class="recipe-title">${recipe.name}</h3>
                            <div class="recipe-country">
                                <i class="fas fa-map-marker-alt"></i>
                                ${recipe.country || 'International'}
                            </div>
                            ${recipe.origin ? `<div class="origin-info"><i class="fas fa-globe"></i> ${recipe.origin}</div>` : ''}
                            ${recipe.cuisine_type ? `<div class="cuisine-type">${recipe.cuisine_type}</div>` : ''}
                        </div>
                        <button class="favorite-btn ${isFavorited ? 'favorited' : ''}" 
                                data-recipe-id="${recipe.id}">
                            <i class="fas fa-heart"></i>
                        </button>
                    </div>
                    <p class="recipe-description">${recipe.description}</p>
                    <div class="recipe-meta">
                        <span class="prep-time">
                            <i class="fas fa-clock"></i>
                            ${recipe.prep_time || 'Not specified'}
                        </span>
                        <span class="difficulty">
                            <i class="fas fa-signal"></i>
                            ${recipe.difficulty || 'Medium'}
                        </span>
                    </div>
                    
                    <!-- Rating Section -->
                    <div class="recipe-rating">
                        <div class="star-rating">
                            ${this.createStarRating(recipe.id, averageRating, true, userRating)}
                        </div>
                        <div class="rating-display">
                            ${averageRating > 0 ? `${averageRating.toFixed(1)} <span class="rating-count">(${ratingCount} reviews)</span>` : 'No ratings yet'}
                        </div>
                    </div>
                    
                    ${badges.length > 0 ? `<div class="recipe-badges">${badges.join('')}</div>` : ''}
                </div>
            </div>
        `;
    }

    async showRecipeDetails(recipeId) {
        try {
            const response = await fetch(`/api/recipe/${recipeId}`);
            const recipe = await response.json();
            
            // Create dietary badges for modal
            const modalBadges = [];
            if (recipe.is_vegan) modalBadges.push('<span class="badge vegan"><i class="fas fa-leaf"></i> Vegan</span>');
            else if (recipe.is_vegetarian) modalBadges.push('<span class="badge vegetarian"><i class="fas fa-seedling"></i> Vegetarian</span>');
            if (recipe.is_gluten_free) modalBadges.push('<span class="badge gluten-free"><i class="fas fa-wheat"></i> Gluten-Free</span>');
            if (recipe.spice_level && recipe.spice_level !== 'None') {
                const spiceClass = `spice-${recipe.spice_level.toLowerCase()}`;
                modalBadges.push(`<span class="badge ${spiceClass}"><i class="fas fa-pepper-hot"></i> ${recipe.spice_level} Spice</span>`);
            }
            
            document.getElementById('modalBody').innerHTML = `
                <img src="${recipe.image}" alt="${recipe.name}" class="modal-recipe-image"
                     onerror="this.src='https://via.placeholder.com/800x300?text=Recipe+Image'">
                <h2 class="modal-recipe-title">${recipe.name}</h2>
                
                <div class="modal-recipe-info">
                    <div class="modal-recipe-country">
                        <span><i class="fas fa-map-marker-alt"></i> ${recipe.country}</span>
                    </div>
                    ${recipe.origin ? `<div class="origin-info" style="text-align: center; margin: 1rem 0;"><i class="fas fa-globe"></i> Origin: ${recipe.origin}</div>` : ''}
                    ${recipe.cuisine_type ? `<div class="cuisine-type" style="text-align: center; margin: 1rem 0;">Cuisine: ${recipe.cuisine_type}</div>` : ''}
                    
                    <div class="recipe-stats" style="display: flex; justify-content: center; gap: 2rem; margin: 1rem 0; flex-wrap: wrap;">
                        <div style="text-align: center;">
                            <i class="fas fa-clock" style="color: #ff6b6b;"></i>
                            <div style="font-weight: 600; margin-top: 0.3rem;">${recipe.prep_time}</div>
                            <div style="font-size: 0.8rem; color: #666;">Prep Time</div>
                        </div>
                        <div style="text-align: center;">
                            <i class="fas fa-signal" style="color: #4ecdc4;"></i>
                            <div style="font-weight: 600; margin-top: 0.3rem;">${recipe.difficulty}</div>
                            <div style="font-size: 0.8rem; color: #666;">Difficulty</div>
                        </div>
                    </div>
                    
                    ${modalBadges.length > 0 ? `<div class="recipe-badges" style="justify-content: center; margin: 1.5rem 0;">${modalBadges.join('')}</div>` : ''}
                </div>
                
                <div class="health-benefits">
                    <h3><i class="fas fa-heart"></i> Health Benefits</h3>
                    <p>${recipe.health_benefits}</p>
                </div>
                
                <div class="recipe-section">
                    <h3><i class="fas fa-list"></i> Ingredients</h3>
                    <div class="ingredients-list">
                        ${recipe.ingredients.map(ingredient => 
                            `<div class="ingredient-item">${ingredient}</div>`
                        ).join('')}
                    </div>
                </div>
                
                <div class="recipe-section">
                    <h3><i class="fas fa-clipboard-list"></i> Preparation Steps</h3>
                    <ol class="steps-list">
                        ${recipe.steps.map(step => 
                            `<li class="step-item">${step}</li>`
                        ).join('')}
                    </ol>
                </div>
            `;
            
            document.getElementById('recipeModal').classList.remove('hidden');
        } catch (error) {
            console.error('Error loading recipe details:', error);
            alert('Failed to load recipe details. Please try again.');
        }
    }

    closeModal() {
        document.getElementById('recipeModal').classList.add('hidden');
    }

    toggleFavorite(recipeId) {
        const index = this.favorites.indexOf(recipeId);
        
        if (index > -1) {
            this.favorites.splice(index, 1);
        } else {
            this.favorites.push(recipeId);
        }
        
        localStorage.setItem('favoriteRecipes', JSON.stringify(this.favorites));
        
        // Update favorite button
        const btn = document.querySelector(`[data-recipe-id="${recipeId}"] .favorite-btn`);
        if (btn) {
            btn.classList.toggle('favorited');
        }
        
        // Refresh favorites tab if currently active
        if (this.currentTab === 'favorites') {
            this.displayFavorites();
        }
    }

    scrollToResults() {
        document.getElementById('resultsSection').scrollIntoView({
            behavior: 'smooth',
            block: 'start'
        });
    }

    showLoading() {
        document.getElementById('loadingSpinner').classList.remove('hidden');
        document.getElementById('recipesContainer').innerHTML = '';
    }

    hideLoading() {
        document.getElementById('loadingSpinner').classList.add('hidden');
    }

    showError(message) {
        document.getElementById('recipesContainer').innerHTML = `
            <div class="empty-state">
                <i class="fas fa-exclamation-triangle"></i>
                <h3>Oops!</h3>
                <p>${message}</p>
            </div>
        `;
    }
    
    applyFilters() {
        // Get current filter values
        this.filters.difficulty = document.getElementById('difficultyFilter').value;
        this.filters.spiceLevel = document.getElementById('spiceFilter').value;
        this.filters.cuisineType = document.getElementById('cuisineFilter').value;
        this.filters.vegan = document.getElementById('veganFilter').checked;
        this.filters.vegetarian = document.getElementById('vegetarianFilter').checked;
        this.filters.glutenFree = document.getElementById('glutenFreeFilter').checked;
        
        console.log('Applying filters:', this.filters);
        console.log('Total recipes:', this.recipes.length);
        
        // Filter recipes
        let filteredRecipes = this.recipes.filter(recipe => {
            // Difficulty filter
            if (this.filters.difficulty && recipe.difficulty !== this.filters.difficulty) {
                return false;
            }
            
            // Spice level filter
            if (this.filters.spiceLevel && recipe.spice_level !== this.filters.spiceLevel) {
                return false;
            }
            
            // Cuisine type filter
            if (this.filters.cuisineType && recipe.cuisine_type !== this.filters.cuisineType) {
                return false;
            }
            
            // Dietary filters
            if (this.filters.vegan && !recipe.is_vegan) {
                return false;
            }
            
            if (this.filters.vegetarian && !recipe.is_vegetarian) {
                return false;
            }
            
            if (this.filters.glutenFree && !recipe.is_gluten_free) {
                return false;
            }
            
            return true;
        });
        
        console.log('Filtered recipes:', filteredRecipes.length);
        this.displayRecipes(filteredRecipes);
        this.scrollToResults();
    }
    
    clearAllFilters() {
        // Reset all filter controls
        document.getElementById('difficultyFilter').value = '';
        document.getElementById('spiceFilter').value = '';
        document.getElementById('cuisineFilter').value = '';
        document.getElementById('veganFilter').checked = false;
        document.getElementById('vegetarianFilter').checked = false;
        document.getElementById('glutenFreeFilter').checked = false;
        
        // Reset filter state
        this.filters = {
            difficulty: '',
            spiceLevel: '',
            cuisineType: '',
            vegan: false,
            vegetarian: false,
            glutenFree: false
        };
        
        // Display all recipes
        this.displayRecipes(this.recipes);
    }
    
    initFilters() {
        // Wait a moment for DOM to be ready, then bind filter events
        setTimeout(() => {
            const difficultyFilter = document.getElementById('difficultyFilter');
            const spiceFilter = document.getElementById('spiceFilter');
            const cuisineFilter = document.getElementById('cuisineFilter');
            const veganFilter = document.getElementById('veganFilter');
            const vegetarianFilter = document.getElementById('vegetarianFilter');
            const glutenFreeFilter = document.getElementById('glutenFreeFilter');
            const clearFilters = document.getElementById('clearFilters');
            
            if (difficultyFilter) {
                difficultyFilter.addEventListener('change', () => this.applyFilters());
            }
            if (spiceFilter) {
                spiceFilter.addEventListener('change', () => this.applyFilters());
            }
            if (cuisineFilter) {
                cuisineFilter.addEventListener('change', () => this.applyFilters());
            }
            if (veganFilter) {
                veganFilter.addEventListener('change', () => this.applyFilters());
            }
            if (vegetarianFilter) {
                vegetarianFilter.addEventListener('change', () => this.applyFilters());
            }
            if (glutenFreeFilter) {
                glutenFreeFilter.addEventListener('change', () => this.applyFilters());
            }
            if (clearFilters) {
                clearFilters.addEventListener('click', () => this.clearAllFilters());
            }
        }, 100);
    }

    // Authentication Methods
    async initAuth() {
        await this.checkAuthStatus();
        this.bindAuthEvents();
    }

    async checkAuthStatus() {
        try {
            // Check localStorage first for quick display
            const localUser = localStorage.getItem('spicePilotUser');
            if (localUser) {
                this.currentUser = JSON.parse(localUser);
                this.updateAuthUI();
            }

            // Verify with server
            const response = await fetch('/api/user');
            if (response.ok) {
                const userData = await response.json();
                this.currentUser = userData;
                this.updateAuthUI();
                // Update localStorage with latest data
                localStorage.setItem('spicePilotUser', JSON.stringify(userData));
                localStorage.setItem('spicePilotLoggedIn', 'true');
            } else {
                // User not authenticated on server
                this.currentUser = null;
                this.updateAuthUI();
                localStorage.removeItem('spicePilotUser');
                localStorage.removeItem('spicePilotLoggedIn');
            }
        } catch (error) {
            console.error('Error checking auth status:', error);
            this.currentUser = null;
            this.updateAuthUI();
        }
    }

    updateAuthUI() {
        const authNav = document.getElementById('authNav');
        const userProfile = document.getElementById('userProfile');

        if (this.currentUser) {
            // User is logged in - show profile, hide auth nav
            authNav.classList.add('hidden');
            userProfile.classList.remove('hidden');
            this.displayUserProfile();
        } else {
            // User not logged in - show auth nav, hide profile
            authNav.classList.remove('hidden');
            userProfile.classList.add('hidden');
        }
    }

    displayUserProfile() {
        if (!this.currentUser) return;

        const userInitials = this.getUserInitials(this.currentUser.first_name, this.currentUser.last_name);
        const fullName = `${this.currentUser.first_name} ${this.currentUser.last_name}`;

        document.getElementById('userInitials').textContent = userInitials;
        document.getElementById('userName').textContent = fullName;
        document.getElementById('userEmail').textContent = this.currentUser.email;
    }

    getUserInitials(firstName, lastName) {
        const first = firstName ? firstName.charAt(0).toUpperCase() : '';
        const last = lastName ? lastName.charAt(0).toUpperCase() : '';
        return first + last;
    }

    bindAuthEvents() {
        // User avatar click to toggle dropdown
        const userAvatar = document.getElementById('userAvatar');
        const userProfile = document.getElementById('userProfile');
        const logoutBtn = document.getElementById('logoutBtn');

        if (userAvatar) {
            userAvatar.addEventListener('click', (e) => {
                e.stopPropagation();
                userProfile.classList.toggle('active');
            });
        }

        // Close dropdown when clicking outside
        document.addEventListener('click', (e) => {
            if (userProfile && !userProfile.contains(e.target)) {
                userProfile.classList.remove('active');
            }
        });

        // Logout button
        if (logoutBtn) {
            logoutBtn.addEventListener('click', () => this.handleLogout());
        }
    }

    async handleLogout() {
        try {
            const response = await fetch('/api/logout', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                }
            });

            if (response.ok) {
                // Clear user data
                this.currentUser = null;
                localStorage.removeItem('spicePilotUser');
                localStorage.removeItem('spicePilotLoggedIn');
                
                // Update UI
                this.updateAuthUI();
                
                // Show success message
                this.showLogoutSuccess();
            } else {
                throw new Error('Logout failed');
            }
        } catch (error) {
            console.error('Logout error:', error);
            alert('Logout failed. Please try again.');
        }
    }

    showLogoutSuccess() {
        // Create success message
        const successDiv = document.createElement('div');
        successDiv.className = 'logout-success-message';
        successDiv.innerHTML = `
            <div class="success-content">
                <i class="fas fa-check-circle"></i>
                <span>Successfully logged out!</span>
            </div>
        `;
        
        // Add CSS for the success message
        successDiv.style.cssText = `
            position: fixed;
            top: 80px;
            right: 20px;
            background: linear-gradient(45deg, #27ae60, #2ecc71);
            color: white;
            padding: 1rem 1.5rem;
            border-radius: 15px;
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
            z-index: 1000;
            animation: slideInRight 0.5s ease-out;
        `;
        
        document.body.appendChild(successDiv);
        
        // Remove after 3 seconds
        setTimeout(() => {
            if (successDiv.parentNode) {
                successDiv.remove();
            }
        }, 3000);
    }

    // Scroll Effects Methods
    initScrollEffects() {
        this.initScrollProgress();
        this.initScrollToTop();
        this.initParallaxEffect();
        this.initScrollRevealAnimations();
        this.initRecipeCardAnimations();
    }

    initScrollProgress() {
        window.addEventListener('scroll', () => {
            const scrollProgress = document.getElementById('scrollProgress');
            const windowHeight = document.documentElement.scrollHeight - document.documentElement.clientHeight;
            const scrolled = window.scrollY;
            const progress = (scrolled / windowHeight) * 100;
            
            scrollProgress.style.width = progress + '%';
        });
    }

    initScrollToTop() {
        const scrollToTopBtn = document.getElementById('scrollToTop');
        
        window.addEventListener('scroll', () => {
            if (window.scrollY > 300) {
                scrollToTopBtn.classList.add('visible');
            } else {
                scrollToTopBtn.classList.remove('visible');
            }
        });
    }

    scrollToTop() {
        window.scrollTo({
            top: 0,
            behavior: 'smooth'
        });
    }

    initParallaxEffect() {
        const parallaxElements = document.querySelectorAll('.parallax-element');
        const backgroundSlideshow = document.querySelector('.background-slideshow');
        
        window.addEventListener('scroll', () => {
            const scrolled = window.scrollY;
            const rate = scrolled * -0.5;
            const backgroundRate = scrolled * -0.3;
            
            // Apply parallax to header elements
            parallaxElements.forEach(element => {
                element.style.transform = `translateY(${rate}px)`;
            });
            
            // Apply parallax to background
            if (backgroundSlideshow) {
                backgroundSlideshow.style.transform = `translateY(${backgroundRate}px)`;
            }
        });
    }

    initScrollRevealAnimations() {
        const revealElements = document.querySelectorAll('.scroll-reveal');
        
        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    entry.target.classList.add('revealed');
                }
            });
        }, {
            threshold: 0.1,
            rootMargin: '0px 0px -50px 0px'
        });
        
        revealElements.forEach(element => {
            observer.observe(element);
        });
    }

    initRecipeCardAnimations() {
        // Create intersection observer for recipe cards
        this.cardObserver = new IntersectionObserver((entries) => {
            entries.forEach((entry, index) => {
                if (entry.isIntersecting) {
                    // Add staggered delay for animation
                    setTimeout(() => {
                        entry.target.classList.add('animate-in');
                    }, index * 100); // 100ms delay between each card
                }
            });
        }, {
            threshold: 0.1,
            rootMargin: '0px 0px -50px 0px'
        });
    }

    observeRecipeCards() {
        // Observe new recipe cards when they're added
        const recipeCards = document.querySelectorAll('.recipe-card:not(.animate-in)');
        recipeCards.forEach(card => {
            if (this.cardObserver) {
                this.cardObserver.observe(card);
            }
        });
    }

    // Particle Disintegration Effect
    initParticleEffect() {
        const title = document.getElementById('spicePilotTitle');
        const titleContainer = title.parentElement;
        
        let particles = [];
        let isDisintegrated = false;
        let reformTimeout = null;
        
        const createParticles = () => {
            const titleRect = title.getBoundingClientRect();
            const containerRect = titleContainer.getBoundingClientRect();
            
            // Clear existing particles
            particles.forEach(particle => particle.remove());
            particles = [];
            
            // Create particles based on title dimensions
            const particleCount = 120;
            const titleWidth = titleRect.width;
            const titleHeight = titleRect.height;
            
            for (let i = 0; i < particleCount; i++) {
                const particle = document.createElement('div');
                particle.className = 'title-particle';
                
                // Random position within title bounds
                const x = Math.random() * titleWidth;
                const y = Math.random() * titleHeight;
                
                // Random scatter direction
                const randomX = (Math.random() - 0.5) * 400;
                const randomY = (Math.random() - 0.5) * 400;
                
                // Random size
                const size = Math.random() * 4 + 2;
                
                particle.style.cssText = `
                    left: ${x}px;
                    top: ${y}px;
                    width: ${size}px;
                    height: ${size}px;
                    --random-x: ${randomX}px;
                    --random-y: ${randomY}px;
                    background: linear-gradient(45deg, #FF6B35, #FF8C42);
                    box-shadow: 0 0 10px rgba(255, 107, 53, 0.5);
                `;
                
                titleContainer.appendChild(particle);
                particles.push(particle);
            }
        };
        
        const disintegrate = () => {
            if (isDisintegrated) return;
            
            isDisintegrated = true;
            createParticles();
            
            // Hide title and animate particles
            title.classList.add('title-disintegrating');
            
            particles.forEach((particle, index) => {
                setTimeout(() => {
                    particle.style.opacity = '1';
                    particle.style.transform = 'scale(1)';
                    
                    setTimeout(() => {
                        particle.classList.add('particle-disintegrate');
                    }, 50);
                }, index * 3);
            });
        };
        
        const reform = () => {
            if (!isDisintegrated) return;
            
            // Clear any pending reform
            if (reformTimeout) {
                clearTimeout(reformTimeout);
            }
            
            // Reform particles back to title
            particles.forEach((particle, index) => {
                particle.classList.remove('particle-disintegrate');
                particle.classList.add('particle-reform');
                
                setTimeout(() => {
                    particle.remove();
                }, 800);
            });
            
            // Show title back
            setTimeout(() => {
                title.classList.remove('title-disintegrating');
                title.classList.add('title-reforming');
                isDisintegrated = false;
                
                setTimeout(() => {
                    title.classList.remove('title-reforming');
                }, 800);
            }, 400);
            
            particles = [];
        };
        
        // Bind hover events
        title.addEventListener('mouseenter', disintegrate);
        title.addEventListener('mouseleave', () => {
            reformTimeout = setTimeout(reform, 100);
        });
        
        // Also bind to title container for better hover detection
        titleContainer.addEventListener('mouseenter', disintegrate);
        titleContainer.addEventListener('mouseleave', () => {
            reformTimeout = setTimeout(reform, 100);
        });
    }

    // AI Recipe Generator Methods
    initAIGenerator() {
        this.updateGenerateButton();
    }

    addIngredient() {
        const input = document.getElementById('ingredientInput');
        const ingredient = input.value.trim();
        
        if (ingredient && !this.userIngredients.includes(ingredient.toLowerCase())) {
            this.userIngredients.push(ingredient.toLowerCase());
            this.displayIngredients();
            input.value = '';
            this.updateGenerateButton();
        }
    }

    removeIngredient(ingredient) {
        const index = this.userIngredients.indexOf(ingredient);
        if (index > -1) {
            this.userIngredients.splice(index, 1);
            this.displayIngredients();
            this.updateGenerateButton();
        }
    }

    displayIngredients() {
        const container = document.getElementById('ingredientsList');
        
        if (this.userIngredients.length === 0) {
            container.innerHTML = '<p style="color: #999; text-align: center; padding: 1rem;">No ingredients added yet. Start by adding some ingredients above!</p>';
            return;
        }
        
        container.innerHTML = this.userIngredients.map(ingredient => `
            <div class="ingredient-tag">
                <span>${ingredient}</span>
                <button class="remove-ingredient" onclick="window.recipeApp.removeIngredient('${ingredient}')">
                    <i class="fas fa-times"></i>
                </button>
            </div>
        `).join('');
    }

    updateGenerateButton() {
        const btn = document.getElementById('generateRecipeBtn');
        btn.disabled = this.userIngredients.length < 2;
    }

    async generateAIRecipe() {
        if (this.userIngredients.length < 2) {
            alert('Please add at least 2 ingredients to generate a recipe.');
            return;
        }

        const btn = document.getElementById('generateRecipeBtn');
        const generatedRecipeDiv = document.getElementById('generatedRecipe');
        
        // Show loading state
        btn.classList.add('generating');
        btn.innerHTML = '<i class="fas fa-magic"></i> Generating...';
        
        generatedRecipeDiv.innerHTML = `
            <div class="ai-loading">
                <i class="fas fa-robot"></i>
                <h3>AI is cooking up something special...</h3>
                <p>Using your ingredients: ${this.userIngredients.join(', ')}</p>
            </div>
        `;
        generatedRecipeDiv.style.display = 'block';

        try {
            const preferences = {
                difficulty: document.getElementById('difficultyPreference').value,
                cuisine: document.getElementById('cuisinePreference').value
            };

            const response = await fetch('/api/generate-recipe', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    ingredients: this.userIngredients,
                    preferences: preferences
                })
            });

            if (response.ok) {
                const aiRecipe = await response.json();
                
                // Add to AI generated recipes
                aiRecipe.id = 'ai_' + Date.now();
                aiRecipe.isAIGenerated = true;
                aiRecipe.rating = { average: 0, count: 0 };
                
                this.aiGeneratedRecipes.unshift(aiRecipe);
                localStorage.setItem('aiGeneratedRecipes', JSON.stringify(this.aiGeneratedRecipes));
                
                this.displayGeneratedRecipe(aiRecipe);
                this.scrollToResults();
            } else {
                throw new Error('Failed to generate recipe');
            }
        } catch (error) {
            console.error('Error generating recipe:', error);
            generatedRecipeDiv.innerHTML = `
                <div class="empty-state">
                    <i class="fas fa-exclamation-triangle"></i>
                    <h3>Recipe Generation Failed</h3>
                    <p>Sorry, we couldn't generate a recipe right now. Please try again later.</p>
                </div>
            `;
        } finally {
            // Reset button state
            btn.classList.remove('generating');
            btn.innerHTML = '<i class="fas fa-magic"></i> Generate Recipe';
        }
    }

    displayGeneratedRecipe(recipe) {
        const container = document.getElementById('generatedRecipe');
        
        container.innerHTML = `
            <div class="recipe-card" style="max-width: none; margin: 0;">
                <div class="recipe-content">
                    <div class="recipe-header">
                        <div>
                            <h3 class="recipe-title">${recipe.name}</h3>
                            <div class="ai-badge">
                                <i class="fas fa-robot"></i> AI Generated
                            </div>
                            ${recipe.cuisine_type ? `<div class="cuisine-type">${recipe.cuisine_type}</div>` : ''}
                        </div>
                        <button class="favorite-btn" data-recipe-id="${recipe.id}">
                            <i class="fas fa-heart"></i>
                        </button>
                    </div>
                    <p class="recipe-description">${recipe.description}</p>
                    
                    <div class="recipe-section">
                        <h4><i class="fas fa-list"></i> Ingredients</h4>
                        <div class="ingredients-list">
                            ${recipe.ingredients.map(ingredient => 
                                `<div class="ingredient-item">${ingredient}</div>`
                            ).join('')}
                        </div>
                    </div>
                    
                    <div class="recipe-section">
                        <h4><i class="fas fa-clipboard-list"></i> Instructions</h4>
                        <ol class="steps-list">
                            ${recipe.steps.map(step => 
                                `<li class="step-item">${step}</li>`
                            ).join('')}
                        </ol>
                    </div>
                    
                    <div class="recipe-actions">
                        <button class="save-recipe-btn" onclick="window.recipeApp.saveAIRecipe('${recipe.id}')">
                            <i class="fas fa-save"></i> Save Recipe
                        </button>
                        <button class="view-full-btn" onclick="window.recipeApp.showRecipeDetails('${recipe.id}')">
                            <i class="fas fa-expand"></i> View Full Recipe
                        </button>
                    </div>
                </div>
            </div>
        `;
        
        // Bind favorite button for generated recipe
        const favoriteBtn = container.querySelector('.favorite-btn');
        if (favoriteBtn) {
            favoriteBtn.addEventListener('click', (e) => {
                e.stopPropagation();
                this.toggleFavorite(recipe.id);
            });
        }
    }

    displayAIGeneratedRecipes() {
        if (this.aiGeneratedRecipes.length === 0) {
            document.getElementById('recipesContainer').innerHTML = `
                <div class="empty-state">
                    <i class="fas fa-robot"></i>
                    <h3>No AI Generated Recipes Yet</h3>
                    <p>Use the AI Recipe Generator above to create custom recipes from your ingredients!</p>
                </div>
            `;
            return;
        }
        
        this.displayRecipes(this.aiGeneratedRecipes);
    }

    saveAIRecipe(recipeId) {
        // This would typically save to a user's personal recipe collection
        alert('Recipe saved to your collection! (Feature would be fully implemented with backend)');
    }

    // Rating System Methods
    createStarRating(recipeId, currentRating = 0, isInteractive = true, userRating = 0) {
        const stars = [];
        
        for (let i = 1; i <= 5; i++) {
            const isActive = i <= currentRating;
            const isUserRated = i <= userRating;
            stars.push(`
                <span class="star ${isActive ? 'active' : ''} ${isUserRated ? 'user-rated' : ''}" 
                      data-rating="${i}" 
                      data-recipe-id="${recipeId}"
                      ${isInteractive ? 'onclick="window.recipeApp.rateRecipe(\''+recipeId+'\', '+i+')"' : ''}>
                    <i class="fas fa-star"></i>
                </span>
            `);
        }
        
        return stars.join('');
    }

    async rateRecipe(recipeId, rating) {
        if (!this.currentUser) {
            alert('Please log in to rate recipes.');
            return;
        }

        try {
            const response = await fetch('/api/rate-recipe', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    recipe_id: recipeId,
                    rating: rating
                })
            });

            if (response.ok) {
                const result = await response.json();
                this.updateRecipeRating(recipeId, result.average_rating, result.rating_count, rating);
                
                // Show success feedback
                this.showRatingSuccess(rating);
            } else {
                throw new Error('Failed to save rating');
            }
        } catch (error) {
            console.error('Error rating recipe:', error);
            alert('Failed to save your rating. Please try again.');
        }
    }

    updateRecipeRating(recipeId, averageRating, ratingCount, userRating) {
        // Update stars in recipe cards
        const recipeCard = document.querySelector(`[data-recipe-id="${recipeId}"]`);
        if (recipeCard) {
            const ratingDisplay = recipeCard.querySelector('.rating-display');
            if (ratingDisplay) {
                ratingDisplay.innerHTML = `${averageRating.toFixed(1)} <span class="rating-count">(${ratingCount} reviews)</span>`;
            }
            
            // Update star visual state
            const stars = recipeCard.querySelectorAll('.star');
            stars.forEach((star, index) => {
                const starRating = index + 1;
                star.classList.toggle('active', starRating <= averageRating);
                star.classList.toggle('user-rated', starRating <= userRating);
            });
        }
        
        // Update in modal if open
        const modal = document.getElementById('recipeModal');
        if (!modal.classList.contains('hidden')) {
            const modalStars = modal.querySelectorAll('.star');
            modalStars.forEach((star, index) => {
                const starRating = index + 1;
                star.classList.toggle('active', starRating <= averageRating);
                star.classList.toggle('user-rated', starRating <= userRating);
            });
            
            const modalRatingDisplay = modal.querySelector('.rating-display');
            if (modalRatingDisplay) {
                modalRatingDisplay.innerHTML = `${averageRating.toFixed(1)} <span class="rating-count">(${ratingCount} reviews)</span>`;
            }
        }
    }

    showRatingSuccess(rating) {
        const message = document.createElement('div');
        message.className = 'rating-success-message';
        message.innerHTML = `
            <div class="success-content">
                <i class="fas fa-star"></i>
                <span>Rated ${rating} star${rating !== 1 ? 's' : ''}!</span>
            </div>
        `;
        
        message.style.cssText = `
            position: fixed;
            top: 80px;
            right: 20px;
            background: linear-gradient(45deg, #FFD700, #FFA500);
            color: #333;
            padding: 1rem 1.5rem;
            border-radius: 15px;
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
            z-index: 1000;
            animation: slideInRight 0.5s ease-out;
        `;
        
        document.body.appendChild(message);
        
        setTimeout(() => {
            if (message.parentNode) {
                message.remove();
            }
        }, 2000);
    }
}

// Initialize the app
document.addEventListener('DOMContentLoaded', () => {
    window.recipeApp = new RecipeApp();
});
