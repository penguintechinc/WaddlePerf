import React from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { LoginPageBuilder } from '@penguintechinc/react-libs';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:5000';

const Login: React.FC = () => {
  const { login } = useAuth();
  const navigate = useNavigate();

  return (
    <LoginPageBuilder
      api={{ loginUrl: `${API_BASE_URL}/api/v1/auth/login` }}
      branding={{
        appName: 'WaddlePerf Manager',
        logo: '/waddleperf-logo.png',
        tagline: 'Network Performance Management',
        githubRepo: 'penguintechinc/WaddlePerf',
      }}
      mfa={{ enabled: true, codeLength: 6 }}
      showForgotPassword={true}
      forgotPasswordUrl="/forgot-password"
      showSignUp={false}
      onSuccess={(response) => {
        localStorage.setItem('auth_token', response.token || '');
        localStorage.setItem('user', JSON.stringify(response.user || {}));
        navigate('/dashboard');
      }}
      onError={(error) => console.error('Login failed:', error)}
    />
  );
};

export default Login;
