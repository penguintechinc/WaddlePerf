import { LoginPageBuilder } from '@penguintechinc/react-libs';
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
      onSuccess={(response: Record<string, unknown>) => {
        if (response.user) {
          onLogin(response.user as { id: number; username: string; email: string; role: string });
        }
        // Store session_id for WebSocket authentication
        if ((response as Record<string, unknown>).session_id) {
          sessionStorage.setItem('session_id', (response as Record<string, unknown>).session_id as string);
        }
      }}
      onError={(error: unknown) => console.error('Login failed:', error)}
    />
  );
}

export default Login
