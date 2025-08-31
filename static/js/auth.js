class AuthHandler {
    constructor() {
        this.selectedCuisines = [];
        this.init();
    }

    init() {
        this.bindEvents();
        this.initPasswordStrength();
        this.initCuisineTags();
        this.initFormValidation();
    }

    bindEvents() {
        // Password toggle functionality
        this.initPasswordToggles();

        // Form submissions
        const loginForm = document.getElementById('loginForm');
        const signupForm = document.getElementById('signupForm');

        if (loginForm) {
            loginForm.addEventListener('submit', (e) => this.handleLogin(e));
        }

        if (signupForm) {
            signupForm.addEventListener('submit', (e) => this.handleSignup(e));
        }

        // Social login buttons
        document.querySelectorAll('.social-btn').forEach(btn => {
            btn.addEventListener('click', (e) => this.handleSocialLogin(e));
        });

        // Input focus effects
        document.querySelectorAll('.form-group input').forEach(input => {
            input.addEventListener('focus', (e) => this.handleInputFocus(e));
            input.addEventListener('blur', (e) => this.handleInputBlur(e));
        });
    }

    initPasswordToggles() {
        document.querySelectorAll('.password-toggle').forEach(toggle => {
            toggle.addEventListener('click', (e) => {
                const input = e.target.closest('.password-input-wrapper').querySelector('input');
                const icon = e.target.querySelector('i') || e.target;
                
                if (input.type === 'password') {
                    input.type = 'text';
                    icon.className = 'fas fa-eye-slash';
                } else {
                    input.type = 'password';
                    icon.className = 'fas fa-eye';
                }
            });
        });
    }

    initPasswordStrength() {
        const passwordInput = document.getElementById('signupPassword');
        if (!passwordInput) return;

        passwordInput.addEventListener('input', (e) => {
            this.updatePasswordStrength(e.target.value);
        });
    }

    updatePasswordStrength(password) {
        const strengthFill = document.getElementById('strengthFill');
        const strengthText = document.getElementById('strengthText');
        
        if (!strengthFill || !strengthText) return;

        const strength = this.calculatePasswordStrength(password);
        
        // Remove all strength classes
        strengthFill.className = 'strength-fill';
        
        if (password.length === 0) {
            strengthText.textContent = 'Password strength';
            return;
        }

        switch (strength.level) {
            case 1:
                strengthFill.classList.add('weak');
                strengthText.textContent = 'Weak password';
                strengthText.style.color = '#e74c3c';
                break;
            case 2:
                strengthFill.classList.add('fair');
                strengthText.textContent = 'Fair password';
                strengthText.style.color = '#f39c12';
                break;
            case 3:
                strengthFill.classList.add('good');
                strengthText.textContent = 'Good password';
                strengthText.style.color = '#27ae60';
                break;
            case 4:
                strengthFill.classList.add('strong');
                strengthText.textContent = 'Strong password';
                strengthText.style.color = '#FF6B35';
                break;
        }
    }

    calculatePasswordStrength(password) {
        let score = 0;
        const checks = {
            length: password.length >= 8,
            lowercase: /[a-z]/.test(password),
            uppercase: /[A-Z]/.test(password),
            numbers: /\d/.test(password),
            symbols: /[^A-Za-z0-9]/.test(password)
        };

        Object.values(checks).forEach(check => {
            if (check) score++;
        });

        return {
            score,
            level: Math.min(Math.floor(score), 4),
            checks
        };
    }

    initCuisineTags() {
        const cuisineTags = document.querySelectorAll('.cuisine-tag');
        const cuisineInput = document.getElementById('cuisinePreferences');
        
        if (!cuisineTags.length) return;

        cuisineTags.forEach(tag => {
            tag.addEventListener('click', () => {
                const cuisine = tag.dataset.cuisine;
                
                if (tag.classList.contains('selected')) {
                    // Remove from selection
                    tag.classList.remove('selected');
                    this.selectedCuisines = this.selectedCuisines.filter(c => c !== cuisine);
                } else {
                    // Add to selection
                    tag.classList.add('selected');
                    this.selectedCuisines.push(cuisine);
                }
                
                // Update hidden input
                if (cuisineInput) {
                    cuisineInput.value = this.selectedCuisines.join(',');
                }
            });
        });
    }

    initFormValidation() {
        // Real-time validation
        document.querySelectorAll('.form-group input').forEach(input => {
            input.addEventListener('input', (e) => this.validateField(e.target));
            input.addEventListener('blur', (e) => this.validateField(e.target));
        });

        // Password confirmation validation
        const confirmPassword = document.getElementById('confirmPassword');
        const signupPassword = document.getElementById('signupPassword');
        
        if (confirmPassword && signupPassword) {
            confirmPassword.addEventListener('input', () => {
                this.validatePasswordMatch(signupPassword.value, confirmPassword.value);
            });
        }
    }

    validateField(field) {
        const formGroup = field.closest('.form-group');
        const errorElement = formGroup.querySelector('.error-message');
        
        // Clear previous states
        formGroup.classList.remove('error', 'success');
        if (errorElement) {
            errorElement.classList.remove('show');
        }

        let isValid = true;
        let errorMessage = '';

        // Field-specific validation
        switch (field.type) {
            case 'email':
                if (field.value && !this.isValidEmail(field.value)) {
                    isValid = false;
                    errorMessage = 'Please enter a valid email address';
                }
                break;
            case 'password':
                if (field.value && field.value.length < 8) {
                    isValid = false;
                    errorMessage = 'Password must be at least 8 characters long';
                }
                break;
            case 'text':
                if (field.required && field.value.trim().length < 2) {
                    isValid = false;
                    errorMessage = 'This field must be at least 2 characters long';
                }
                break;
        }

        // Update UI
        if (field.value) {
            if (isValid) {
                formGroup.classList.add('success');
            } else {
                formGroup.classList.add('error');
                this.showError(errorElement, errorMessage);
            }
        }

        return isValid;
    }

    validatePasswordMatch(password, confirmPassword) {
        const confirmFormGroup = document.getElementById('confirmPassword').closest('.form-group');
        const errorElement = confirmFormGroup.querySelector('.error-message');
        
        confirmFormGroup.classList.remove('error', 'success');
        if (errorElement) {
            errorElement.classList.remove('show');
        }

        if (confirmPassword && password !== confirmPassword) {
            confirmFormGroup.classList.add('error');
            this.showError(errorElement, 'Passwords do not match');
            return false;
        } else if (confirmPassword && password === confirmPassword) {
            confirmFormGroup.classList.add('success');
            return true;
        }

        return true;
    }

    isValidEmail(email) {
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        return emailRegex.test(email);
    }

    showError(errorElement, message) {
        if (errorElement) {
            errorElement.textContent = message;
            errorElement.classList.add('show');
        }
    }

    hideError(errorElement) {
        if (errorElement) {
            errorElement.classList.remove('show');
        }
    }

    handleInputFocus(e) {
        const formGroup = e.target.closest('.form-group');
        formGroup.classList.add('focused');
    }

    handleInputBlur(e) {
        const formGroup = e.target.closest('.form-group');
        formGroup.classList.remove('focused');
    }

    async handleLogin(e) {
        e.preventDefault();
        
        const form = e.target;
        const email = form.email.value;
        const password = form.password.value;
        const rememberMe = form.rememberMe.checked;

        // Validate form
        if (!this.validateLoginForm(email, password)) {
            return;
        }

        this.showLoading('Signing you in...');

        try {
            const response = await fetch('/api/login', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    email,
                    password,
                    rememberMe
                })
            });

            const data = await response.json();

            if (response.ok && data.success) {
                // Store user session
                this.storeUserSession({
                    ...data.user,
                    rememberMe,
                    loginTime: new Date().toISOString()
                });

                // Show success and redirect
                this.showSuccess('Login successful! Redirecting...', () => {
                    window.location.href = '/';
                });
            } else {
                this.hideLoading();
                this.showError(document.getElementById('passwordError'), data.error || 'Login failed');
            }

        } catch (error) {
            this.hideLoading();
            this.showError(document.getElementById('passwordError'), 'Network error. Please try again.');
        }
    }

    async handleSignup(e) {
        e.preventDefault();
        
        const form = e.target;
        const formData = {
            firstName: form.firstName.value,
            lastName: form.lastName.value,
            email: form.email.value,
            password: form.password.value,
            confirmPassword: form.confirmPassword.value,
            cuisinePreferences: this.selectedCuisines,
            agreeTerms: form.agreeTerms.checked,
            newsletter: form.newsletter.checked
        };

        // Validate form
        if (!this.validateSignupForm(formData)) {
            return;
        }

        this.showLoading('Creating your account...');

        try {
            const response = await fetch('/api/signup', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(formData)
            });

            const data = await response.json();

            if (response.ok && data.success) {
                // Store user session
                this.storeUserSession({
                    ...data.user,
                    signupTime: new Date().toISOString()
                });

                // Show success and redirect
                this.showSuccess('Account created successfully! Welcome to SPICE PILOT!', () => {
                    window.location.href = '/';
                });
            } else {
                this.hideLoading();
                this.showError(document.getElementById('signupEmailError'), data.error || 'Registration failed');
            }

        } catch (error) {
            this.hideLoading();
            this.showError(document.getElementById('signupEmailError'), 'Network error. Please try again.');
        }
    }

    validateLoginForm(email, password) {
        let isValid = true;

        // Email validation
        if (!email) {
            this.showError(document.getElementById('emailError'), 'Email is required');
            isValid = false;
        } else if (!this.isValidEmail(email)) {
            this.showError(document.getElementById('emailError'), 'Please enter a valid email');
            isValid = false;
        }

        // Password validation
        if (!password) {
            this.showError(document.getElementById('passwordError'), 'Password is required');
            isValid = false;
        }

        return isValid;
    }

    validateSignupForm(data) {
        let isValid = true;

        // First name validation
        if (!data.firstName.trim()) {
            this.showError(document.getElementById('firstNameError'), 'First name is required');
            isValid = false;
        }

        // Last name validation
        if (!data.lastName.trim()) {
            this.showError(document.getElementById('lastNameError'), 'Last name is required');
            isValid = false;
        }

        // Email validation
        if (!data.email) {
            this.showError(document.getElementById('signupEmailError'), 'Email is required');
            isValid = false;
        } else if (!this.isValidEmail(data.email)) {
            this.showError(document.getElementById('signupEmailError'), 'Please enter a valid email');
            isValid = false;
        }

        // Password validation
        const passwordStrength = this.calculatePasswordStrength(data.password);
        if (!data.password) {
            this.showError(document.getElementById('signupPasswordError'), 'Password is required');
            isValid = false;
        } else if (passwordStrength.level < 2) {
            this.showError(document.getElementById('signupPasswordError'), 'Password is too weak');
            isValid = false;
        }

        // Password confirmation
        if (data.password !== data.confirmPassword) {
            this.showError(document.getElementById('confirmPasswordError'), 'Passwords do not match');
            isValid = false;
        }

        // Terms agreement
        if (!data.agreeTerms) {
            this.showError(document.getElementById('termsError'), 'You must agree to the terms');
            isValid = false;
        }

        return isValid;
    }

    async handleSocialLogin(e) {
        const provider = e.target.closest('.social-btn').classList.contains('google-btn') ? 'google' : 'facebook';
        
        this.showLoading(`Connecting with ${provider.charAt(0).toUpperCase() + provider.slice(1)}...`);
        
        try {
            // Redirect to OAuth provider
            window.location.href = `/auth/${provider}`;
        } catch (error) {
            this.hideLoading();
            alert(`${provider.charAt(0).toUpperCase() + provider.slice(1)} login failed. Please try again.`);
        }
    }

    showLoading(message = 'Loading...') {
        const overlay = document.getElementById('loadingOverlay');
        const messageElement = overlay.querySelector('p');
        
        if (messageElement) {
            messageElement.textContent = message;
        }
        
        overlay.classList.remove('hidden');
    }

    hideLoading() {
        const overlay = document.getElementById('loadingOverlay');
        overlay.classList.add('hidden');
    }

    showSuccess(message, callback) {
        this.hideLoading();
        
        // Create success message element
        const successDiv = document.createElement('div');
        successDiv.className = 'success-message';
        successDiv.innerHTML = `
            <i class="fas fa-check-circle"></i>
            <span>${message}</span>
        `;
        
        // Insert at top of form
        const form = document.querySelector('.auth-form');
        form.insertBefore(successDiv, form.firstChild);
        
        // Execute callback after delay
        setTimeout(() => {
            if (callback) callback();
        }, 2000);
    }

    storeUserSession(userData) {
        localStorage.setItem('spicePilotUser', JSON.stringify(userData));
        localStorage.setItem('spicePilotLoggedIn', 'true');
    }

    simulateAPICall(delay = 1000) {
        return new Promise((resolve, reject) => {
            setTimeout(() => {
                // Simulate 90% success rate
                if (Math.random() > 0.1) {
                    resolve();
                } else {
                    reject(new Error('API Error'));
                }
            }, delay);
        });
    }

    // Utility Functions
    clearFormErrors() {
        document.querySelectorAll('.error-message').forEach(error => {
            error.classList.remove('show');
        });
        
        document.querySelectorAll('.form-group').forEach(group => {
            group.classList.remove('error', 'success');
        });
    }

    resetForm(formId) {
        const form = document.getElementById(formId);
        if (form) {
            form.reset();
            this.clearFormErrors();
            
            // Reset cuisine selections
            document.querySelectorAll('.cuisine-tag').forEach(tag => {
                tag.classList.remove('selected');
            });
            this.selectedCuisines = [];
            
            // Reset password strength
            const strengthFill = document.getElementById('strengthFill');
            const strengthText = document.getElementById('strengthText');
            if (strengthFill) {
                strengthFill.className = 'strength-fill';
            }
            if (strengthText) {
                strengthText.textContent = 'Password strength';
                strengthText.style.color = '#666';
            }
        }
    }

    // Form enhancement methods
    addInputAnimation() {
        document.querySelectorAll('.form-group input').forEach(input => {
            input.addEventListener('focus', function() {
                this.parentElement.classList.add('focused');
            });
            
            input.addEventListener('blur', function() {
                if (!this.value) {
                    this.parentElement.classList.remove('focused');
                }
            });
        });
    }

    // Keyboard navigation
    initKeyboardNavigation() {
        document.addEventListener('keydown', (e) => {
            // Enter key on cuisine tags
            if (e.target.classList.contains('cuisine-tag') && e.key === 'Enter') {
                e.target.click();
            }
            
            // Escape key to close modals/overlays
            if (e.key === 'Escape') {
                const loadingOverlay = document.getElementById('loadingOverlay');
                if (!loadingOverlay.classList.contains('hidden')) {
                    this.hideLoading();
                }
            }
        });
    }

    // Auto-fill detection and styling
    detectAutofill() {
        const inputs = document.querySelectorAll('input[type="email"], input[type="password"], input[type="text"]');
        
        inputs.forEach(input => {
            // Check for autofill on load
            setTimeout(() => {
                if (input.value) {
                    input.closest('.form-group').classList.add('focused');
                }
            }, 100);
            
            // Check for autofill changes
            input.addEventListener('animationstart', (e) => {
                if (e.animationName === 'autofill') {
                    input.closest('.form-group').classList.add('focused');
                }
            });
        });
    }
}

// Enhanced form validation with better UX
class FormValidator {
    static validateEmail(email) {
        const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        return re.test(email);
    }

    static validatePassword(password) {
        return {
            minLength: password.length >= 8,
            hasUpper: /[A-Z]/.test(password),
            hasLower: /[a-z]/.test(password),
            hasNumber: /\d/.test(password),
            hasSymbol: /[^A-Za-z0-9]/.test(password)
        };
    }

    static validateName(name) {
        return name.trim().length >= 2 && /^[a-zA-Z\s]+$/.test(name.trim());
    }
}

// Initialize authentication handler when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.authHandler = new AuthHandler();
    
    // Add additional enhancements
    authHandler.addInputAnimation();
    authHandler.initKeyboardNavigation();
    authHandler.detectAutofill();
    
    // Add floating label effect
    document.querySelectorAll('.form-group input').forEach(input => {
        // Check if input has value on load
        if (input.value) {
            input.closest('.form-group').classList.add('focused');
        }
    });
});
