/**
 * Authentication utilities for JWT handling
 */

const Auth = {
    /**
     * Check if user is authenticated
     * @returns {boolean} True if authenticated
     */
    isAuthenticated: () => {
        return localStorage.getItem('authToken') !== null;
    },
    
    /**
     * Get the JWT token
     * @returns {string|null} JWT token or null if not authenticated
     */
    getToken: () => {
        return localStorage.getItem('authToken');
    },
    
    /**
     * Get user role
     * @returns {string|null} User role or null if not authenticated
     */
    getUserRole: () => {
        return localStorage.getItem('userRole');
    },
    
    /**
     * Check if user has admin role
     * @returns {boolean} True if user is admin
     */
    isAdmin: () => {
        return localStorage.getItem('userRole') === 'admin';
    },
    
    /**
     * Check if token is expired
     * @returns {boolean} True if token is expired or invalid
     */
    isTokenExpired: () => {
        const token = localStorage.getItem('authToken');
        if (!token) return true;
        
        try {
            // JWT tokens are base64 encoded with 3 parts separated by dots
            const payload = token.split('.')[1];
            // Decode payload
            const decodedPayload = JSON.parse(atob(payload));
            // Check expiration (exp is in seconds)
            return decodedPayload.exp * 1000 < Date.now();
        } catch (error) {
            console.error('Error checking token expiration:', error);
            return true;
        }
    },
    
    /**
     * Logout user by removing auth data
     */
    logout: () => {
        localStorage.removeItem('authToken');
        localStorage.removeItem('userId');
        localStorage.removeItem('userRole');
        window.location.href = '/login';
    },
    
    /**
     * Create headers for fetch API with authorization token
     * @returns {Object} Headers object
     */
    getAuthHeaders: () => {
        return {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${localStorage.getItem('authToken')}`
        };
    },
    
    /**
     * Make authenticated API request
     * @param {string} url - API endpoint
     * @param {Object} options - Fetch options
     * @returns {Promise} Fetch promise
     */
    fetch: async (url, options = {}) => {
        // If not authenticated, redirect to login
        if (!Auth.isAuthenticated() || Auth.isTokenExpired()) {
            Auth.logout();
            return Promise.reject('Not authenticated');
        }
        
        // Add auth headers to request
        const authOptions = {
            ...options,
            headers: {
                ...options.headers,
                ...Auth.getAuthHeaders()
            }
        };
        
        try {
            const response = await fetch(url, authOptions);
            
            // If token is invalid, logout
            if (response.status === 401) {
                Auth.logout();
                return Promise.reject('Authentication failed');
            }
            
            return response;
        } catch (error) {
            console.error('API request error:', error);
            return Promise.reject(error);
        }
    }
};

// Add role-based element control
document.addEventListener('DOMContentLoaded', function() {
    // Handle elements that should only be visible to admins
    document.querySelectorAll('[data-role="admin"]').forEach(element => {
        if (!Auth.isAdmin()) {
            element.style.display = 'none';
        }
    });
    
    // Handle elements that should only be visible to authenticated users
    document.querySelectorAll('[data-auth="required"]').forEach(element => {
        if (!Auth.isAuthenticated()) {
            element.style.display = 'none';
        }
    });
    
    // Handle elements that should only be visible to unauthenticated users
    document.querySelectorAll('[data-auth="guest"]').forEach(element => {
        if (Auth.isAuthenticated()) {
            element.style.display = 'none';
        }
    });
    
    // Handle logout button
    const logoutButton = document.getElementById('logout-button');
    if (logoutButton) {
        logoutButton.addEventListener('click', (e) => {
            e.preventDefault();
            Auth.logout();
        });
    }
});