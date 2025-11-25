/**
 * Authentication Module
 * Handles authentication via Cloudflare Access or magic code login
 *
 * Priority:
 * 1. Cloudflare Access (Zero Trust) - automatic, no login page needed
 * 2. Session token from magic code login - fallback for non-CF Access deployments
 *
 * @module Auth
 */

const Auth = (function() {
    'use strict';

    const STORAGE_KEYS = {
        SESSION_TOKEN: 'auth_session_token',
        SESSION_EXPIRES: 'auth_session_expires',
        USER_EMAIL: 'auth_user_email',
        AUTH_METHOD: 'auth_method'  // 'cloudflare_access', 'session', or 'api_token'
    };

    // Cache for CF Access status (checked once per page load)
    let cfAccessStatus = null;

    /**
     * Check if user is authenticated
     * @returns {boolean}
     */
    function isAuthenticated() {
        const token = localStorage.getItem(STORAGE_KEYS.SESSION_TOKEN);
        const expires = localStorage.getItem(STORAGE_KEYS.SESSION_EXPIRES);

        if (!token || !expires) return false;

        // Check if session expired
        if (new Date(expires) < new Date()) {
            clearSession();
            return false;
        }

        return true;
    }

    /**
     * Get current session token
     * @returns {string|null}
     */
    function getSessionToken() {
        if (!isAuthenticated()) return null;
        return localStorage.getItem(STORAGE_KEYS.SESSION_TOKEN);
    }

    /**
     * Get current user email
     * @returns {string|null}
     */
    function getUserEmail() {
        return localStorage.getItem(STORAGE_KEYS.USER_EMAIL);
    }

    /**
     * Save session to localStorage
     * @param {string} token - Session token
     * @param {string} expiresAt - ISO date string
     * @param {string} email - User email
     */
    function saveSession(token, expiresAt, email) {
        localStorage.setItem(STORAGE_KEYS.SESSION_TOKEN, token);
        localStorage.setItem(STORAGE_KEYS.SESSION_EXPIRES, expiresAt);
        localStorage.setItem(STORAGE_KEYS.USER_EMAIL, email);
    }

    /**
     * Clear session from localStorage
     */
    function clearSession() {
        localStorage.removeItem(STORAGE_KEYS.SESSION_TOKEN);
        localStorage.removeItem(STORAGE_KEYS.SESSION_EXPIRES);
        localStorage.removeItem(STORAGE_KEYS.USER_EMAIL);
    }

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
     * Request a magic code to be sent to email
     * @param {string} email - Email address
     * @returns {Promise<{success: boolean, message: string, error?: string, retryAfter?: number}>}
     */
    async function requestCode(email) {
        try {
            const endpoint = await getEndpoint();

            const response = await fetch(`${endpoint}/auth/request-code`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ email })
            });

            const data = await response.json();

            if (!response.ok) {
                return {
                    success: false,
                    message: data.message || 'Failed to send code',
                    error: data.error,
                    retryAfter: data.retryAfter
                };
            }

            return data;
        } catch (error) {
            console.error('Request code error:', error);
            return {
                success: false,
                message: 'Network error. Please check your connection.',
                error: 'network_error'
            };
        }
    }

    /**
     * Verify code and create session
     * @param {string} email - Email address
     * @param {string} code - 6-digit code
     * @returns {Promise<{success: boolean, message?: string, session_token?: string, expires_at?: string}>}
     */
    async function verifyCode(email, code) {
        try {
            const endpoint = await getEndpoint();

            const response = await fetch(`${endpoint}/auth/verify-code`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ email, code })
            });

            const data = await response.json();

            if (!response.ok) {
                return {
                    success: false,
                    message: data.message || 'Verification failed',
                    error: data.error
                };
            }

            // Save session on success
            if (data.success && data.session_token) {
                saveSession(data.session_token, data.expires_at, email);
            }

            return data;
        } catch (error) {
            console.error('Verify code error:', error);
            return {
                success: false,
                message: 'Network error. Please check your connection.',
                error: 'network_error'
            };
        }
    }

    /**
     * Check current session status with server
     * @returns {Promise<{authenticated: boolean, email?: string, expires_at?: string}>}
     */
    async function checkSession() {
        const token = getSessionToken();
        if (!token) {
            return { authenticated: false };
        }

        try {
            const endpoint = await getEndpoint();

            const response = await fetch(`${endpoint}/auth/session`, {
                method: 'GET',
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json'
                }
            });

            if (!response.ok) {
                // Session invalid on server, clear local
                clearSession();
                return { authenticated: false };
            }

            return await response.json();
        } catch (error) {
            console.error('Check session error:', error);
            // Network error - keep local session, might be offline
            return { authenticated: isAuthenticated() };
        }
    }

    /**
     * Logout and invalidate session
     * @returns {Promise<void>}
     */
    async function logout() {
        const token = getSessionToken();

        if (token) {
            try {
                const endpoint = await getEndpoint();

                await fetch(`${endpoint}/auth/logout`, {
                    method: 'POST',
                    headers: {
                        'Authorization': `Bearer ${token}`,
                        'Content-Type': 'application/json'
                    }
                });
            } catch (error) {
                console.error('Logout error:', error);
                // Continue with local logout even if server fails
            }
        }

        clearSession();
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
     * Check authentication status from server
     * This detects Cloudflare Access, session tokens, and API tokens
     * @returns {Promise<{authenticated: boolean, method: string|null, email?: string}>}
     */
    async function checkAuthStatus() {
        // Return cached status if available
        if (cfAccessStatus !== null) {
            return cfAccessStatus;
        }

        try {
            const endpoint = await getEndpoint();
            const headers = { 'Content-Type': 'application/json' };

            // Include session token if we have one
            const token = localStorage.getItem(STORAGE_KEYS.SESSION_TOKEN);
            if (token) {
                headers['Authorization'] = `Bearer ${token}`;
            }

            const response = await fetch(`${endpoint}/auth/status`, {
                method: 'GET',
                headers: headers,
                credentials: 'include'  // Important for CF Access cookies
            });

            if (response.ok) {
                const data = await response.json();
                cfAccessStatus = data;

                // Store auth method and email if authenticated
                if (data.authenticated) {
                    localStorage.setItem(STORAGE_KEYS.AUTH_METHOD, data.method);
                    if (data.email) {
                        localStorage.setItem(STORAGE_KEYS.USER_EMAIL, data.email);
                    }
                }

                return data;
            }
        } catch (error) {
            console.error('Auth status check error:', error);
        }

        return { authenticated: false, method: null };
    }

    /**
     * Get current authentication method
     * @returns {string|null} - 'cloudflare_access', 'session', 'api_token', or null
     */
    function getAuthMethod() {
        return localStorage.getItem(STORAGE_KEYS.AUTH_METHOD);
    }

    /**
     * Check if using Cloudflare Access
     * @returns {boolean}
     */
    function isUsingCFAccess() {
        return getAuthMethod() === 'cloudflare_access';
    }

    /**
     * Require authentication - redirect to login if not authenticated
     * Only applies when using cloud API
     * Cloudflare Access users skip login page entirely
     * @returns {Promise<boolean>} - true if authenticated or using local API
     */
    async function requireAuth() {
        const usingCloud = await isUsingCloudAPI();

        // Local API doesn't require session auth
        if (!usingCloud) {
            return true;
        }

        // Check server-side auth status (detects CF Access)
        const authStatus = await checkAuthStatus();

        if (authStatus.authenticated) {
            // User is authenticated (via CF Access, session, or API token)
            return true;
        }

        // Check local session as fallback
        if (isAuthenticated()) {
            return true;
        }

        // Not authenticated - redirect to login
        window.location.href = 'login.html';
        return false;
    }

    /**
     * Initialize auth - check session and redirect if needed
     * Call this on protected pages
     * @returns {Promise<boolean>}
     */
    async function init() {
        return await requireAuth();
    }

    // Public API
    return {
        isAuthenticated,
        getSessionToken,
        getUserEmail,
        requestCode,
        verifyCode,
        checkSession,
        checkAuthStatus,
        getAuthMethod,
        isUsingCFAccess,
        logout,
        requireAuth,
        isUsingCloudAPI,
        init,
        clearSession
    };
})();

// Export globally
window.Auth = Auth;
