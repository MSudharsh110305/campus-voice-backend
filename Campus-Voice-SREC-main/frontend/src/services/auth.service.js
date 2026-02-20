import { api, decodeToken } from '../utils/api';

const loginStudent = async (email_or_roll_no, password) => {
    const data = await api('/students/login', {
        method: 'POST',
        body: JSON.stringify({ email_or_roll_no, password }),
    });
    return handleLoginResponse(data);
};

const loginAuthority = async (email, password) => {
    const data = await api('/authorities/login', {
        method: 'POST',
        body: JSON.stringify({ email, password }),
    });
    return handleLoginResponse(data);
};

const handleLoginResponse = (data) => {
    if (data.token) {
        localStorage.setItem('token', data.token);

        // Decode token to get the authoritative role
        const decoded = decodeToken(data.token);

        // Merge returned user data with the token role
        // Backend returns user details (name, email, etc) separate from token
        // But token is the source of truth for 'role'
        const userWithRole = {
            ...data, // This likely contains name, email, roll_no etc directly at top level or in a 'user' object depending on backend
            // Per backend spec: Response fields include roll_no, name, etc, AND token.
            // We'll flatten it carefully.
            role: decoded?.role, // Default to Student if missing, but should be there
        };

        // If the backend returns 'user' object nested:
        if (data.user) {
            Object.assign(userWithRole, data.user);
        }

        // Clean up redundant fields if necessary, but key implies we store 'user' string
        localStorage.setItem('user', JSON.stringify(userWithRole));
        return userWithRole;
    }
    return data;
};

const signup = async (userData) => {
    const data = await api('/students/register', {
        method: 'POST',
        body: JSON.stringify(userData),
    });
    return data;
};

const logout = () => {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    window.location.href = '/login';
};

const getCurrentUser = () => {
    const userStr = localStorage.getItem('user');
    const token = localStorage.getItem('token');

    if (!userStr || !token) return null;

    try {
        const user = JSON.parse(userStr);
        if (!user || typeof user !== 'object') return null;

        const decoded = decodeToken(token);
        if (!decoded?.role) return null;
        if (decoded && decoded.exp * 1000 < Date.now()) {
            // Token expired - invalid session
            return null;
        }

        return user;
    } catch (e) {
        return null;
    }
};

const authService = {
    loginStudent,
    loginAuthority,
    signup,
    logout,
    getCurrentUser,
};

export default authService;
