/**
 * Authentication Module
 * Handles authentication via Cloudflare Access (Zero Trust)
 *
 * @module Auth
 */

const Auth = (function() {
    'use strict';

    const STORAGE_KEYS = {
        USER_EMAIL: 'auth_user_email',
        AUTH_METHOD: 'auth_method'
    };

    // Cache for CF Access status (checked once per page load)
    let cfAccessStatus = null;

    /**
     * Get API endpoint from config
     * @returns {Promise<string>}
     */
    async function getEndpoint() {
        const config = await Storage.loadConfig();
        return config.api.use_cloud
            ? config.api.cloud_endpoint
            : config.api.local_endpoint;
    }

    /**
     * Check if cloud API is being used
     * @returns {Promise<boolean>}
     */
    async function isUsingCloudAPI() {
        try {
            const config = await Storage.loadConfig();
            return config.api.use_cloud === true;
        } catch (error) {
            return false;
        }
    }

    /**
     * Get current user email
     * @returns {string|null}
     */
    function getUserEmail() {
        return localStorage.getItem(STORAGE_KEYS.USER_EMAIL);
    }

    /**
     * Check authentication status from server
     * @returns {Promise<{authenticated: boolean, method: string|null, email?: string}>}
     */
    async function checkAuthStatus() {
        // Return cached status if available
        if (cfAccessStatus !== null) {
            return cfAccessStatus;
        }

        try {
            const endpoint = await getEndpoint();

            const response = await fetch(`${endpoint}/auth/status`, {
                method: 'GET',
                headers: { 'Content-Type': 'application/json' },
                credentials: 'include'  // Important for CF Access cookies
            });

            if (response.ok) {
                const data = await response.json();
                cfAccessStatus = data;

                // Store email if authenticated
                if (data.authenticated && data.email) {
                    localStorage.setItem(STORAGE_KEYS.AUTH_METHOD, data.method);
                    localStorage.setItem(STORAGE_KEYS.USER_EMAIL, data.email);
                }

                return data;
            }
        } catch (error) {
            console.error('Auth status check error:', error);
        }

        return { authenticated: false, method: null };
    }

    /**
     * Check if authenticated
     * @returns {Promise<boolean>}
     */
    async function isAuthenticated() {
        const status = await checkAuthStatus();
        return status.authenticated;
    }

    /**
     * Require authentication - check CF Access
     * @returns {Promise<boolean>} - true if authenticated or using local API
     */
    async function requireAuth() {
        const usingCloud = await isUsingCloudAPI();

        // Local API doesn't require auth
        if (!usingCloud) {
            return true;
        }

        // Check Cloudflare Access authentication
        const authStatus = await checkAuthStatus();
        return authStatus.authenticated;
    }

    /**
     * Initialize auth - check CF Access
     * @returns {Promise<boolean>}
     */
    async function init() {
        return await requireAuth();
    }

    /**
     * Clear local storage (for logout)
     */
    function clearSession() {
        localStorage.removeItem(STORAGE_KEYS.USER_EMAIL);
        localStorage.removeItem(STORAGE_KEYS.AUTH_METHOD);
        cfAccessStatus = null;
    }

    // Public API
    return {
        isAuthenticated,
        getUserEmail,
        checkAuthStatus,
        requireAuth,
        isUsingCloudAPI,
        init,
        clearSession
    };
})();

// Export globally
window.Auth = Auth;
