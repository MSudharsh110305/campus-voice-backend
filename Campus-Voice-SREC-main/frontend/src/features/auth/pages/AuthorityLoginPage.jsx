import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Eye, EyeOff, ShieldCheck } from 'lucide-react';
import { useAuth } from '../../../context/AuthContext';
import { Button } from '../../../components/UI';

export default function AuthorityLoginPage() {
    const { loginAuthority } = useAuth();
    const navigate = useNavigate();
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [showPassword, setShowPassword] = useState(false);
    const [error, setError] = useState('');
    const [isLoading, setIsLoading] = useState(false);

    const onSubmit = async (e) => {
        e.preventDefault();
        setError('');
        if (!email || !password) {
            setError('Please fill in both email and password.');
            return;
        }

        try {
            setIsLoading(true);
            const response = await loginAuthority(email, password);
            console.log('Authority Login successful:', response);

            const role = response.role;
            if (role === 'Admin') {
                navigate('/admin', { replace: true });
            } else {
                navigate('/authority-dashboard', { replace: true });
            }
        } catch (err) {
            console.error('Login error:', err);
            setError(err.message || 'Login failed');
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <div className="min-h-screen bg-srec-background flex items-center justify-center px-4">
            <div className="w-full max-w-[400px]">
                <div className="bg-white rounded-2xl shadow-xl border border-srec-border p-8">
                    <div className="text-center mb-8">
                        <div className="flex justify-center mb-4">
                            <div className="p-3 bg-srec-primary/10 rounded-full text-srec-primary">
                                <ShieldCheck size={32} />
                            </div>
                        </div>
                        <h1 className="text-2xl font-bold text-srec-textPrimary tracking-tight">Authority Portal</h1>
                        <p className="text-srec-textSecondary text-sm mt-2">Administrative & Faculty Login</p>
                    </div>

                    <form onSubmit={onSubmit} className="space-y-5" aria-label="Authority Login form">
                        <div>
                            <label className="block text-xs font-semibold text-srec-textSecondary mb-1.5 ml-1">OFFICIAL EMAIL</label>
                            <input
                                type="email"
                                value={email}
                                onChange={(e) => setEmail(e.target.value)}
                                aria-label="Email address"
                                className="w-full rounded-lg border border-srec-border bg-gray-50/50 px-4 py-3 text-sm text-srec-textPrimary shadow-sm placeholder:text-gray-400 focus:bg-white focus:outline-none focus:ring-2 focus:ring-srec-primary/50 transition-all font-medium"
                                placeholder="authority@srec.ac.in"
                            />
                        </div>

                        <div>
                            <label className="block text-xs font-semibold text-srec-textSecondary mb-1.5 ml-1">PASSWORD</label>
                            <div className="relative">
                                <input
                                    type={showPassword ? 'text' : 'password'}
                                    value={password}
                                    onChange={(e) => setPassword(e.target.value)}
                                    aria-label="Password"
                                    className="w-full rounded-lg border border-srec-border bg-gray-50/50 px-4 py-3 pr-10 text-sm text-srec-textPrimary shadow-sm placeholder:text-gray-400 focus:bg-white focus:outline-none focus:ring-2 focus:ring-srec-primary/50 transition-all font-medium"
                                    placeholder="Enter your password"
                                />
                                <button
                                    type="button"
                                    onClick={() => setShowPassword(!showPassword)}
                                    className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600 transition-colors"
                                    aria-label={showPassword ? 'Hide password' : 'Show password'}
                                >
                                    {showPassword ? <EyeOff size={18} /> : <Eye size={18} />}
                                </button>
                            </div>
                        </div>

                        {error && (
                            <div className="p-3 rounded-lg bg-red-50 border border-red-100 text-xs text-red-600 font-medium animate-fadeInDelay" role="alert">
                                {error}
                            </div>
                        )}

                        <Button type="submit" variant="primary" className="w-full py-2.5 text-base" disabled={isLoading}>
                            {isLoading ? 'Access Dashboard' : 'Login to Dashboard'}
                        </Button>
                    </form>
                </div>

                <div className="mt-8 text-center">
                    <Link to="/login" className="text-sm text-gray-500 hover:text-srec-primary transition-colors">
                        Are you a student? Login here
                    </Link>
                </div>
            </div>
        </div>
    );
}
