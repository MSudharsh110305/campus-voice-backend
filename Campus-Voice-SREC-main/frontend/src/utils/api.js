// Use the Vite proxy for local dev so all /api requests go through localhost:8000
// In production set VITE_API_URL to the production API URL
const API_BASE_URL = import.meta.env.VITE_API_URL || '/api';

/**
 * Decodes a JWT token manually to extract the payload.
 * Useful for getting the role and expiration without an external library.
 */
export const decodeToken = (token) => {
    try {
        const base64Url = token.split('.')[1];
        const base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/');
        const jsonPayload = decodeURIComponent(
            window.atob(base64)
                .split('')
                .map((c) => '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2))
                .join('')
        );
        return JSON.parse(jsonPayload);
    } catch (error) {
        console.error('Failed to decode token:', error);
        return null;
    }
};

/**
 * A wrapper around fetch that handles:
 * 1. Attaching the Bearer token.
 * 2. Parsing JSON responses.
 * 3. Handling global errors (401 → redirect to login).
 */
export const api = async (endpoint, options = {}) => {
    const token = localStorage.getItem('token');

    const headers = {
        ...options.headers,
    };

    // Only set Content-Type to application/json if we're NOT sending FormData
    if (!(options.body instanceof FormData)) {
        headers['Content-Type'] = 'application/json';
    }

    if (token) {
        headers['Authorization'] = `Bearer ${token}`;
    }

    const config = {
        ...options,
        headers,
    };

    // Ensure endpoint starts with / for consistency
    const path = endpoint.startsWith('/') ? endpoint : `/${endpoint}`;
    const url = `${API_BASE_URL}${path}`;

    try {
        const response = await fetch(url, config);

        // Handle 204 No Content
        if (response.status === 204) return null;

        // Handle non-JSON responses (like binary image data)
        const contentType = response.headers.get('content-type') || '';
        if (contentType.startsWith('image/')) {
            if (!response.ok) {
                throw new Error(`Image request failed with status ${response.status}`);
            }
            return response; // Return raw response for blob handling
        }

        const data = await response.json().catch(() => ({}));

        if (!response.ok) {
            console.error('API Error Response:', { status: response.status, data });

            // Global Error Handling — on 401 clear token and redirect to login
            if (response.status === 401) {
                console.warn('Session expired or unauthorized. Redirecting to login.');
                localStorage.removeItem('token');
                localStorage.removeItem('user');
                window.location.href = '/login';
                return;
            }

            // Surface the most useful error message from backend
            const message = data.error || data.detail || data.message || `Request failed with status ${response.status}`;
            const err = new Error(message);
            err.status = response.status;
            err.data = data;
            throw err;
        }

        return data;
    } catch (error) {
        // Re-throw errors that already have our shape
        if (error.status) throw error;
        console.error('API Network/Code Error:', error);
        throw error;
    }
};

/**
 * Fetch a binary resource (e.g. image) and return a blob URL.
 * Authorization header is attached automatically.
 */
export const fetchBlobUrl = async (endpoint, options = {}) => {
    const token = localStorage.getItem('token');
    const headers = { ...options.headers };
    if (token) {
        headers['Authorization'] = `Bearer ${token}`;
    }

    const path = endpoint.startsWith('/') ? endpoint : `/${endpoint}`;
    const url = `${API_BASE_URL}${path}`;

    const response = await fetch(url, { ...options, headers });
    if (!response.ok) {
        throw new Error(`Failed to fetch binary resource: ${response.status}`);
    }
    const blob = await response.blob();
    return URL.createObjectURL(blob);
};

export default api;
