import React, { useState, useEffect } from 'react';
import { QRCodeSVG } from 'qrcode.react';
import { useAuth } from '../contexts/AuthContext';
import { api } from '../services/api';
import type { User } from '../types';
import './Profile.css';

const Profile: React.FC = () => {
  const { user: authUser } = useAuth();
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [showMfaSetup, setShowMfaSetup] = useState(false);
  const [mfaSecret, setMfaSecret] = useState('');
  const [mfaQrUri, setMfaQrUri] = useState('');
  const [mfaVerifyCode, setMfaVerifyCode] = useState('');
  const [showPasswordChange, setShowPasswordChange] = useState(false);
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');

  useEffect(() => {
    loadUserProfile();
  }, []);

  const loadUserProfile = async () => {
    if (!authUser) return;
    setLoading(true);
    try {
      const userData = await api.getUser(authUser.id);
      setUser(userData);
    } catch (err: any) {
      setError(err.response?.data?.error || 'Failed to load profile');
    } finally {
      setLoading(false);
    }
  };

  const handleSetupMfa = async () => {
    setError('');
    setSuccess('');
    try {
      const response = await api.setupMfa();
      setMfaSecret(response.secret);
      setMfaQrUri(response.qr_uri);
      setShowMfaSetup(true);
    } catch (err: any) {
      setError(err.response?.data?.error || 'Failed to setup MFA');
    }
  };

  const handleVerifyMfa = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setSuccess('');
    try {
      await api.verifyMfa(mfaVerifyCode);
      setSuccess('MFA enabled successfully!');
      setShowMfaSetup(false);
      setMfaVerifyCode('');
      loadUserProfile();
    } catch (err: any) {
      setError(err.response?.data?.error || 'Failed to verify MFA code');
    }
  };

  const handleChangePassword = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setSuccess('');

    if (newPassword !== confirmPassword) {
      setError('Passwords do not match');
      return;
    }

    if (newPassword.length < 8) {
      setError('Password must be at least 8 characters');
      return;
    }

    if (!authUser) return;

    try {
      await api.changeUserPassword(authUser.id, { password: newPassword });
      setSuccess('Password changed successfully!');
      setShowPasswordChange(false);
      setNewPassword('');
      setConfirmPassword('');
    } catch (err: any) {
      setError(err.response?.data?.error || 'Failed to change password');
    }
  };

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
    setSuccess('Copied to clipboard!');
    /* v8 ignore next */
    setTimeout(() => setSuccess(''), 3000);
  };

  if (loading) {
    return (
      <div className="profile-container">
        <div className="loading-container">
          <div className="spinner"></div>
          <p>Loading profile...</p>
        </div>
      </div>
    );
  }

  if (!user) {
    return (
      <div className="profile-container">
        <div className="error-message">Failed to load user profile</div>
      </div>
    );
  }

  return (
    <div className="profile-container">
      <h1>User Profile</h1>

      {error && <div className="error-message">{error}</div>}
      {success && <div className="success-message">{success}</div>}

      <div className="profile-sections">
        <div className="profile-section">
          <h2>Account Information</h2>
          <div className="info-grid">
            <div className="info-item">
              <span className="info-label">Username:</span>
              <span className="info-value">{user.username}</span>
            </div>
            <div className="info-item">
              <span className="info-label">Email:</span>
              <span className="info-value">{user.email}</span>
            </div>
            <div className="info-item">
              <span className="info-label">Role:</span>
              <span className="info-value">
                <span className="role-badge">{user.role}</span>
              </span>
            </div>
            <div className="info-item">
              <span className="info-label">Status:</span>
              <span className="info-value">
                <span className={`status-badge ${user.is_active ? 'active' : 'inactive'}`}>
                  {user.is_active ? 'Active' : 'Inactive'}
                </span>
              </span>
            </div>
            <div className="info-item">
              <span className="info-label">MFA Status:</span>
              <span className="info-value">
                <span className={`status-badge ${user.mfa_enabled ? 'active' : 'inactive'}`}>
                  {user.mfa_enabled ? 'Enabled' : 'Disabled'}
                </span>
              </span>
            </div>
            <div className="info-item">
              <span className="info-label">Created:</span>
              <span className="info-value">{new Date(user.created_at).toLocaleString()}</span>
            </div>
          </div>
        </div>

        <div className="profile-section">
          <h2>API Key</h2>
          {user.api_key ? (
            <div className="api-key-section">
              <div className="api-key-display">
                <code>{user.api_key}</code>
                <button className="btn-sm btn-copy" onClick={() => copyToClipboard(user.api_key!)}>
                  Copy
                </button>
              </div>
              <p className="info-text">Use this API key to authenticate with the WaddlePerf API.</p>
            </div>
          ) : (
            <p className="info-text">API key not available for your account.</p>
          )}
        </div>

        <div className="profile-section">
          <h2>Security Settings</h2>
          <div className="security-actions">
            {!user.mfa_enabled && (
              <button className="btn-primary" onClick={handleSetupMfa}>
                Enable MFA
              </button>
            )}
            <button className="btn-secondary" onClick={() => setShowPasswordChange(!showPasswordChange)}>
              Change Password
            </button>
          </div>

          {showPasswordChange && (
            <form onSubmit={handleChangePassword} className="password-form">
              <div className="form-group">
                <label htmlFor="new-password">New Password</label>
                <input
                  id="new-password"
                  type="password"
                  value={newPassword}
                  onChange={(e) => setNewPassword(e.target.value)}
                  required
                  minLength={8}
                  autoComplete="new-password"
                />
              </div>
              <div className="form-group">
                <label htmlFor="confirm-password">Confirm Password</label>
                <input
                  id="confirm-password"
                  type="password"
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  required
                  minLength={8}
                  autoComplete="new-password"
                />
              </div>
              <div className="form-actions">
                <button type="button" className="btn-secondary" onClick={() => setShowPasswordChange(false)}>
                  Cancel
                </button>
                <button type="submit" className="btn-primary">
                  Update Password
                </button>
              </div>
            </form>
          )}

          {showMfaSetup && (
            <div className="mfa-setup">
              <h3>Setup Multi-Factor Authentication</h3>
              <p className="info-text">Scan this QR code with your authenticator app (Google Authenticator, Authy, etc.):</p>
              <div className="qr-code-container">
                <QRCodeSVG value={mfaQrUri} size={200} />
              </div>
              <p className="info-text">Or enter this secret manually:</p>
              <div className="secret-display">
                <code>{mfaSecret}</code>
                <button className="btn-sm btn-copy" onClick={() => copyToClipboard(mfaSecret)}>
                  Copy
                </button>
              </div>
              <form onSubmit={handleVerifyMfa} className="mfa-verify-form">
                <div className="form-group">
                  <label htmlFor="mfa-code">Enter verification code:</label>
                  <input
                    id="mfa-code"
                    type="text"
                    value={mfaVerifyCode}
                    onChange={(e) => setMfaVerifyCode(e.target.value)}
                    placeholder="6-digit code"
                    maxLength={6}
                    required
                    autoComplete="one-time-code"
                  />
                </div>
                <div className="form-actions">
                  <button type="button" className="btn-secondary" onClick={() => setShowMfaSetup(false)}>
                    Cancel
                  </button>
                  <button type="submit" className="btn-primary">
                    Verify and Enable
                  </button>
                </div>
              </form>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default Profile;
