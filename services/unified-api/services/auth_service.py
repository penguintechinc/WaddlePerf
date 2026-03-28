"""Authentication service layer for WaddlePerf Unified API"""
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Optional
import bcrypt
import jwt
import pyotp
import qrcode
from io import BytesIO
import base64
from penguin_dal import AsyncDB


@dataclass
class AuthResponse:
    """Response object for authentication operations"""
    access_token: Optional[str] = None
    refresh_token: Optional[str] = None
    user_id: Optional[int] = None
    mfa_required: bool = False
    mfa_secret: Optional[str] = None
    mfa_qr_code: Optional[str] = None
    error: Optional[str] = None
    success: bool = True


@dataclass
class UserInfo:
    """User information object"""
    id: int
    username: str
    email: str
    role: str


class AuthService:
    """Service class for authentication operations"""

    def __init__(self, db: AsyncDB, config) -> None:
        """Initialize AuthService with database and config

        Args:
            db: penguin-dal AsyncDB instance
            config: Configuration object with JWT_SECRET and JWT_EXPIRATION_HOURS
        """
        self.db = db
        self.config = config
        self.jwt_secret = config.JWT_SECRET
        self.jwt_expiration = config.JWT_EXPIRATION_HOURS

    def _hash_password(self, password: str) -> str:
        """Hash password using bcrypt

        Args:
            password: Plain text password

        Returns:
            Bcrypt hashed password string
        """
        salt = bcrypt.gensalt()
        return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

    def _verify_password(self, password: str, password_hash: str) -> bool:
        """Verify password against hash

        Args:
            password: Plain text password
            password_hash: Bcrypt hash to verify against

        Returns:
            True if password matches, False otherwise
        """
        try:
            return bcrypt.checkpw(
                password.encode('utf-8'),
                password_hash.encode('utf-8')
            )
        except (ValueError, TypeError):
            return False

    def _generate_jwt(self, user_id: int, token_type: str = 'access') -> str:
        """Generate JWT token

        Args:
            user_id: User ID to encode in token
            token_type: Type of token ('access' or 'refresh')

        Returns:
            JWT token string
        """
        now = datetime.now(timezone.utc)
        if token_type == 'access':
            expiration = now + timedelta(hours=self.jwt_expiration)
        else:  # refresh token lasts longer
            expiration = now + timedelta(days=30)

        payload = {
            'user_id': user_id,
            'token_type': token_type,
            'iat': now,
            'exp': expiration,
        }
        return jwt.encode(payload, self.jwt_secret, algorithm='HS256')

    def _verify_jwt(self, token: str) -> Optional[dict]:
        """Verify and decode JWT token

        Args:
            token: JWT token string to verify

        Returns:
            Decoded payload if valid, None otherwise
        """
        try:
            return jwt.decode(token, self.jwt_secret, algorithms=['HS256'])
        except (jwt.InvalidTokenError, jwt.DecodeError, jwt.ExpiredSignatureError):
            return None

    async def authenticate(
        self,
        email_or_username: str,
        password: str,
        mfa_token: Optional[str] = None
    ) -> AuthResponse:
        """Authenticate user with email/username and password

        Args:
            email_or_username: User email address or username
            password: Plain text password
            mfa_token: Optional MFA token if MFA is enabled

        Returns:
            AuthResponse with tokens or error
        """
        try:
            # Find user by email or username
            rows = await self.db(
                (self.db.users.email == email_or_username) |
                (self.db.users.username == email_or_username)
            ).select()
            user = rows.first()
            if not user:
                return AuthResponse(
                    success=False,
                    error="Invalid email or password"
                )

            # Verify password
            if not self._verify_password(password, user.password_hash):
                return AuthResponse(
                    success=False,
                    error="Invalid email or password"
                )

            # Check if user is active
            if not user.is_active:
                return AuthResponse(
                    success=False,
                    error="User account is inactive"
                )

            # Check MFA if enabled
            if user.mfa_enabled:
                if not mfa_token:
                    return AuthResponse(
                        success=False,
                        mfa_required=True,
                        error="MFA token required"
                    )

                # Verify MFA token
                totp = pyotp.TOTP(user.mfa_secret)
                if not totp.verify(mfa_token, valid_window=1):
                    return AuthResponse(
                        success=False,
                        error="Invalid MFA token"
                    )

            # Generate tokens
            access_token = self._generate_jwt(user.id, 'access')
            refresh_token = self._generate_jwt(user.id, 'refresh')

            # Store refresh token in database
            await self.db.refresh_tokens.async_insert(
                user_id=user.id,
                token=refresh_token,
                expires_at=datetime.now(timezone.utc) + timedelta(days=30),
                is_revoked=False
            )

            return AuthResponse(
                access_token=access_token,
                refresh_token=refresh_token,
                user_id=user.id,
                success=True
            )
        except Exception as e:
            return AuthResponse(
                success=False,
                error=f"Authentication error: {str(e)}"
            )

    async def refresh_access_token(self, refresh_token: str) -> AuthResponse:
        """Refresh access token using refresh token

        Args:
            refresh_token: Refresh token string

        Returns:
            AuthResponse with new access token or error
        """
        try:
            # Verify refresh token
            payload = self._verify_jwt(refresh_token)
            if not payload or payload.get('token_type') != 'refresh':
                return AuthResponse(
                    success=False,
                    error="Invalid refresh token"
                )

            # Check if token is revoked
            rows = await self.db(
                (self.db.refresh_tokens.token == refresh_token) &
                (self.db.refresh_tokens.is_revoked == False)  # noqa: E712
            ).select()
            token_record = rows.first()

            if not token_record:
                return AuthResponse(
                    success=False,
                    error="Refresh token is revoked or invalid"
                )

            # Check expiration
            if token_record.expires_at < datetime.now(timezone.utc):
                return AuthResponse(
                    success=False,
                    error="Refresh token has expired"
                )

            user_id = payload.get('user_id')
            access_token = self._generate_jwt(user_id, 'access')

            return AuthResponse(
                access_token=access_token,
                user_id=user_id,
                success=True
            )
        except Exception as e:
            return AuthResponse(
                success=False,
                error=f"Token refresh error: {str(e)}"
            )

    async def revoke_tokens(self, user_id: int) -> AuthResponse:
        """Revoke all refresh tokens for a user

        Args:
            user_id: User ID whose tokens should be revoked

        Returns:
            AuthResponse indicating success or error
        """
        try:
            # Mark all refresh tokens as revoked
            await self.db(self.db.refresh_tokens.user_id == user_id).update(
                is_revoked=True
            )
            return AuthResponse(success=True)
        except Exception as e:
            return AuthResponse(
                success=False,
                error=f"Token revocation error: {str(e)}"
            )

    async def send_password_reset_email(self, email: str) -> AuthResponse:
        """Send password reset email to user

        Args:
            email: User email address

        Returns:
            AuthResponse indicating success or error
        """
        try:
            rows = await self.db(self.db.users.email == email).select()
            user = rows.first()
            if not user:
                # Don't reveal if email exists
                return AuthResponse(success=True)

            # Generate reset token
            reset_token = self._generate_jwt(user.id, 'reset')

            # Store reset token
            await self.db.password_reset_tokens.async_insert(
                user_id=user.id,
                token=reset_token,
                expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
                is_used=False
            )

            # TODO: Send email with reset link
            # email_service.send_reset_email(email, reset_token)

            return AuthResponse(success=True)
        except Exception as e:
            return AuthResponse(
                success=False,
                error=f"Password reset email error: {str(e)}"
            )

    async def reset_password(self, token: str, new_password: str) -> AuthResponse:
        """Reset password using reset token

        Args:
            token: Password reset token
            new_password: New password

        Returns:
            AuthResponse indicating success or error
        """
        try:
            # Verify reset token
            payload = self._verify_jwt(token)
            if not payload or payload.get('token_type') != 'reset':
                return AuthResponse(
                    success=False,
                    error="Invalid reset token"
                )

            # Check if token exists and hasn't been used
            rows = await self.db(
                (self.db.password_reset_tokens.token == token) &
                (self.db.password_reset_tokens.is_used == False)  # noqa: E712
            ).select()
            token_record = rows.first()

            if not token_record:
                return AuthResponse(
                    success=False,
                    error="Reset token is invalid or already used"
                )

            # Check expiration
            if token_record.expires_at < datetime.now(timezone.utc):
                return AuthResponse(
                    success=False,
                    error="Reset token has expired"
                )

            # Update password
            user_id = payload.get('user_id')
            password_hash = self._hash_password(new_password)
            await self.db(self.db.users.id == user_id).update(
                password_hash=password_hash
            )

            # Mark token as used
            await self.db(self.db.password_reset_tokens.id == token_record.id).update(
                is_used=True
            )

            # Revoke all refresh tokens
            await self.revoke_tokens(user_id)

            return AuthResponse(success=True)
        except Exception as e:
            return AuthResponse(
                success=False,
                error=f"Password reset error: {str(e)}"
            )

    async def change_password(
        self,
        user_id: int,
        current_password: str,
        new_password: str
    ) -> AuthResponse:
        """Change password for authenticated user

        Args:
            user_id: User ID
            current_password: Current password for verification
            new_password: New password

        Returns:
            AuthResponse indicating success or error
        """
        try:
            rows = await self.db(self.db.users.id == user_id).select()
            user = rows.first()
            if not user:
                return AuthResponse(
                    success=False,
                    error="User not found"
                )

            # Verify current password
            if not self._verify_password(current_password, user.password_hash):
                return AuthResponse(
                    success=False,
                    error="Current password is incorrect"
                )

            # Hash new password
            password_hash = self._hash_password(new_password)
            await self.db(self.db.users.id == user_id).update(
                password_hash=password_hash
            )

            # Revoke all refresh tokens
            await self.revoke_tokens(user_id)

            return AuthResponse(success=True)
        except Exception as e:
            return AuthResponse(
                success=False,
                error=f"Password change error: {str(e)}"
            )

    async def setup_mfa(self, user_id: int) -> AuthResponse:
        """Generate MFA secret and QR code for user

        Args:
            user_id: User ID

        Returns:
            AuthResponse with MFA secret and QR code
        """
        try:
            rows = await self.db(self.db.users.id == user_id).select()
            user = rows.first()
            if not user:
                return AuthResponse(
                    success=False,
                    error="User not found"
                )

            # Generate secret
            secret = pyotp.random_base32()

            # Generate QR code
            totp = pyotp.TOTP(secret)
            qr = qrcode.QRCode(version=1, box_size=10, border=4)
            qr.add_data(totp.provisioning_uri(
                name=user.email,
                issuer_name='WaddlePerf'
            ))
            qr.make(fit=True)

            # Convert QR to base64
            img = qr.make_image()
            buffer = BytesIO()
            img.save(buffer, format='PNG')
            qr_code_base64 = base64.b64encode(buffer.getvalue()).decode()

            return AuthResponse(
                user_id=user_id,
                mfa_secret=secret,
                mfa_qr_code=qr_code_base64,
                success=True
            )
        except Exception as e:
            return AuthResponse(
                success=False,
                error=f"MFA setup error: {str(e)}"
            )

    async def verify_and_enable_mfa(
        self,
        user_id: int,
        mfa_secret: str,
        mfa_token: str
    ) -> AuthResponse:
        """Verify MFA token and enable MFA for user

        Args:
            user_id: User ID
            mfa_secret: MFA secret to store
            mfa_token: MFA token to verify

        Returns:
            AuthResponse indicating success or error
        """
        try:
            rows = await self.db(self.db.users.id == user_id).select()
            user = rows.first()
            if not user:
                return AuthResponse(
                    success=False,
                    error="User not found"
                )

            # Verify token
            totp = pyotp.TOTP(mfa_secret)
            if not totp.verify(mfa_token, valid_window=1):
                return AuthResponse(
                    success=False,
                    error="Invalid MFA token"
                )

            # Enable MFA
            await self.db(self.db.users.id == user_id).update(
                mfa_enabled=True,
                mfa_secret=mfa_secret
            )

            return AuthResponse(success=True)
        except Exception as e:
            return AuthResponse(
                success=False,
                error=f"MFA verification error: {str(e)}"
            )

    async def disable_mfa(
        self,
        user_id: int,
        password: str
    ) -> AuthResponse:
        """Disable MFA for user after password verification

        Args:
            user_id: User ID
            password: User password for verification

        Returns:
            AuthResponse indicating success or error
        """
        try:
            rows = await self.db(self.db.users.id == user_id).select()
            user = rows.first()
            if not user:
                return AuthResponse(
                    success=False,
                    error="User not found"
                )

            # Verify password
            if not self._verify_password(password, user.password_hash):
                return AuthResponse(
                    success=False,
                    error="Invalid password"
                )

            # Disable MFA
            await self.db(self.db.users.id == user_id).update(
                mfa_enabled=False,
                mfa_secret=None
            )

            return AuthResponse(success=True)
        except Exception as e:
            return AuthResponse(
                success=False,
                error=f"MFA disable error: {str(e)}"
            )

    async def get_user_by_id(self, user_id: int) -> Optional[UserInfo]:
        """Get user information by ID

        Args:
            user_id: User ID

        Returns:
            UserInfo object or None if not found
        """
        try:
            rows = await self.db(self.db.users.id == user_id).select()
            user = rows.first()
            if not user:
                return None

            return UserInfo(
                id=user.id,
                username=user.username,
                email=user.email,
                role=user.role or 'user'
            )
        except Exception:
            return None
