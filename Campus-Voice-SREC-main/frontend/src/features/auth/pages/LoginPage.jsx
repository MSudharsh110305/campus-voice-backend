import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Eye, EyeOff } from 'lucide-react';
import { useAuth } from '../../../context/AuthContext';
import { Button } from '../../../components/UI';

export default function LoginPage() {
  const { loginStudent, user, loading } = useAuth();
  const navigate = useNavigate();
  const [identifier, setIdentifier] = useState(''); // Email or Roll No
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  // Redirect if already logged in (guard against unnecessary login page access)
  React.useEffect(() => {
    if (!loading && user) {
      if (user.role === 'Admin') navigate('/admin', { replace: true });
      else if (user.role === 'Authority') navigate('/authority-dashboard', { replace: true });
      else navigate('/home', { replace: true });
    }
  }, [user, loading, navigate]);

  const onSubmit = async (e) => {
    e.preventDefault();
    setError('');
    if (!identifier || !password) {
      setError('Please fill in both email/roll number and password.');
      return;
    }

    try {
      setIsLoading(true);
      const response = await loginStudent(identifier, password);
      console.log('Login successful:', response);
      navigate('/dashboard', { replace: true });
    } catch (err) {
      console.error('Login error:', err);
      // Show backend error message directly
      setError(err.message || 'Login failed');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-srec-background flex items-center justify-center px-4">
      <div className="w-full max-w-[400px]">
        <div className="bg-white rounded-2xl shadow-md border border-srec-border p-8">
          <div className="text-center mb-8">
            <h1 className="text-2xl font-bold text-srec-textPrimary tracking-tight">CampusVoice</h1>
            <p className="text-srec-textSecondary text-sm mt-2">SREC Grievance Redressal Portal</p>
          </div>

          <form onSubmit={onSubmit} className="space-y-5" aria-label="Login form">
            <div>
              <label className="block text-xs font-semibold text-srec-textSecondary mb-1.5 ml-1">EMAIL OR ROLL NUMBER</label>
              <input
                type="text"
                value={identifier}
                onChange={(e) => setIdentifier(e.target.value)}
                aria-label="Email or Roll Number"
                className="w-full rounded-lg border border-srec-border bg-gray-50/50 px-4 py-3 text-sm text-srec-textPrimary shadow-sm placeholder:text-gray-400 focus:bg-white focus:outline-none focus:ring-2 focus:ring-srec-primary/50 transition-all font-medium"
                placeholder="22CS123 or student@srec.ac.in"
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

            <Button type="submit" variant="primary" className="w-full py-2.5 text-base" isLoading={isLoading}>
              {isLoading ? 'Signing In...' : 'Sign In'}
            </Button>
          </form>
        </div>

        <div className="mt-8 text-center bg-white/50 backdrop-blur-sm rounded-xl border border-white/60 shadow-sm p-4">
          <span className="text-gray-600 text-sm">Don't have an account? </span>
          <Link to="/signup" className="text-srec-primary font-semibold hover:text-srec-primaryHover transition-colors">Create Account</Link>
        </div>
      </div>
    </div>
  );
}
