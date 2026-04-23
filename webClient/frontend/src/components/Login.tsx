import { LoginPageBuilder, LoginResponse } from '@penguintechinc/react-libs';
import './Login.css'

interface LoginProps {
  onLogin: (user: { id: number; username: string; email: string; role: string }) => void
}

function Login({ onLogin }: LoginProps) {
  return (
    <LoginPageBuilder
      api={{ loginUrl: '/api/auth/login' }}
      branding={{
        appName: 'WaddlePerf',
        logo: '/waddleperf-logo.png',
        tagline: 'Network Performance Testing',
      }}
      showForgotPassword={false}
      showSignUp={false}
      onSuccess={(response: LoginResponse) => {
        if (response.user) {
          onLogin({
            id: parseInt(response.user.id, 10),
            username: response.user.name ?? response.user.email,
            email: response.user.email,
            role: response.user.roles?.[0] ?? 'viewer',
          });
        }
        if (response.token) {
          localStorage.setItem('access_token', response.token);
        }
        if (response.refreshToken) {
          localStorage.setItem('refresh_token', response.refreshToken);
        }
      }}
      onError={(error: unknown) => console.error('[Login] failed:', error)}
    />
  );
}

export default Login
