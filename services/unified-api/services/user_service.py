"""User management service with penguin-dal AsyncDB operations"""

import uuid
from datetime import datetime
from typing import Dict, Any, Optional, List
from bcrypt import hashpw, gensalt
from penguin_dal import AsyncDB


class UserService:
    """Service for user management operations using penguin-dal AsyncDB.

    Handles:
        - User CRUD operations
        - Password hashing and verification
        - User-role associations
        - Pagination and search
    """

    def __init__(self, db: Optional[AsyncDB] = None) -> None:
        """Initialize UserService.

        Args:
            db: penguin-dal AsyncDB instance (injected for testing/flexibility)
        """
        self.db = db

    async def list_users(
        self,
        page: int = 1,
        limit: int = 20,
        search: str = ''
    ) -> Dict[str, Any]:
        """List users with pagination and optional search.

        Args:
            page: Page number (1-indexed)
            limit: Items per page (max 100)
            search: Search term (searches email, username, first_name, last_name)

        Returns:
            Dict with users list, total count, page info
        """
        try:
            limit = min(limit, 100)  # Cap at 100
            offset = (page - 1) * limit

            # Build query
            query = self.db.auth_user.active == True  # noqa: E712

            # Add search filter if provided
            if search:
                search_term = f'%{search}%'
                query = query & (
                    (self.db.auth_user.email.like(search_term)) |
                    (self.db.auth_user.username.like(search_term)) |
                    (self.db.auth_user.first_name.like(search_term)) |
                    (self.db.auth_user.last_name.like(search_term))
                )

            # Get total count
            total = await self.db(query).count()

            # Fetch paginated results
            rows = await self.db(query).select(
                orderby=self.db.auth_user.created_at,
                limitby=(offset, offset + limit)
            )

            # Serialize users with roles
            users = [await self._serialize_user(row) for row in rows]

            return {
                'users': users,
                'total': total,
                'page': page,
                'limit': limit,
                'pages': (total + limit - 1) // limit  # Ceiling division
            }
        except Exception as e:
            raise Exception(f'Error listing users: {str(e)}')

    async def get_user(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Get user by ID with roles.

        Args:
            user_id: User ID

        Returns:
            User dict with roles or None if not found
        """
        try:
            rows = await self.db(self.db.auth_user.id == user_id).select()
            row = rows.first()
            if not row:
                return None
            return await self._serialize_user(row)
        except Exception as e:
            raise Exception(f'Error fetching user: {str(e)}')

    async def create_user(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create new user with hashed password.

        Args:
            data: User data dict with keys:
                - email (required)
                - username (required)
                - password (required) - will be hashed
                - first_name (optional)
                - last_name (optional)
                - active (optional, default True)
                - role_ids (optional, list of role IDs)

        Returns:
            Created user dict with roles

        Raises:
            ValueError: If email or username already exists
        """
        try:
            email = data.get('email', '').strip()
            username = data.get('username', '').strip()
            password = data.get('password', '').strip()

            # Validate input
            if not email or not username or not password:
                raise ValueError('Email, username, and password are required')

            # Check uniqueness
            if await self.db(self.db.auth_user.email == email).count() > 0:
                raise ValueError(f'Email {email} already exists')

            if await self.db(self.db.auth_user.username == username).count() > 0:
                raise ValueError(f'Username {username} already exists')

            # Hash password
            hashed_password = self._hash_password(password)

            # Create fs_uniquifier for Flask-Security compatibility
            fs_uniquifier = str(uuid.uuid4())

            # Insert user
            user_id = await self.db.auth_user.async_insert(
                email=email,
                username=username,
                password=hashed_password,
                first_name=data.get('first_name', ''),
                last_name=data.get('last_name', ''),
                active=data.get('active', True),
                fs_uniquifier=fs_uniquifier,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )

            # Assign roles if provided
            role_ids = data.get('role_ids', [])
            if role_ids:
                for role_id in role_ids:
                    await self.db.auth_user_role.async_insert(
                        user_id=user_id,
                        role_id=role_id,
                        created_at=datetime.utcnow()
                    )

            # Fetch and return created user
            rows = await self.db(self.db.auth_user.id == user_id).select()
            user_row = rows.first()
            return await self._serialize_user(user_row)

        except ValueError:
            raise
        except Exception as e:
            raise Exception(f'Error creating user: {str(e)}')

    async def update_user(
        self,
        user_id: int,
        data: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Update user profile and/or roles.

        Args:
            user_id: User ID
            data: Update data dict with optional keys:
                - first_name
                - last_name
                - active
                - password (will be hashed)
                - role_ids (list of role IDs to replace existing)

        Returns:
            Updated user dict with roles or None if not found
        """
        try:
            # Check user exists
            rows = await self.db(self.db.auth_user.id == user_id).select()
            if not rows.first():
                return None

            update_data: Dict[str, Any] = {}

            # Update basic fields
            if 'first_name' in data:
                update_data['first_name'] = data['first_name']
            if 'last_name' in data:
                update_data['last_name'] = data['last_name']
            if 'active' in data:
                update_data['active'] = data['active']

            # Update password if provided
            if 'password' in data and data['password'].strip():
                update_data['password'] = self._hash_password(data['password'].strip())

            # Always update timestamp
            update_data['updated_at'] = datetime.utcnow()

            # Update user record
            if update_data:
                await self.db(self.db.auth_user.id == user_id).update(**update_data)

            # Update roles if provided
            if 'role_ids' in data:
                role_ids = data['role_ids']
                # Delete existing roles
                await self.db(self.db.auth_user_role.user_id == user_id).delete()
                # Insert new roles
                for role_id in role_ids:
                    await self.db.auth_user_role.async_insert(
                        user_id=user_id,
                        role_id=role_id,
                        created_at=datetime.utcnow()
                    )

            # Fetch and return updated user
            updated_rows = await self.db(self.db.auth_user.id == user_id).select()
            user_row = updated_rows.first()
            return await self._serialize_user(user_row)

        except Exception as e:
            raise Exception(f'Error updating user: {str(e)}')

    async def delete_user(self, user_id: int) -> bool:
        """Delete user and associated roles.

        Args:
            user_id: User ID to delete

        Returns:
            True if deleted, False if not found
        """
        try:
            # Check user exists
            rows = await self.db(self.db.auth_user.id == user_id).select()
            if not rows.first():
                return False

            # Delete user (cascade will remove roles)
            await self.db(self.db.auth_user.id == user_id).delete()

            return True
        except Exception as e:
            raise Exception(f'Error deleting user: {str(e)}')

    async def _serialize_user(self, user_row: Any) -> Dict[str, Any]:
        """Convert penguin-dal Row to user dict with roles.

        Args:
            user_row: Row object from auth_user table

        Returns:
            User dict with id, email, username, profile fields, active status, and roles list
        """
        if not user_row:
            return {}

        # Fetch user roles with left join via separate query
        role_rows = await self.db(
            self.db.auth_user_role.user_id == user_row.id
        ).select()

        roles: List[Dict[str, Any]] = []
        for role_row in role_rows:
            # Fetch role details
            auth_role_rows = await self.db(
                self.db.auth_role.id == role_row.role_id
            ).select()
            auth_role = auth_role_rows.first()
            if auth_role:
                roles.append({
                    'id': auth_role.id,
                    'name': auth_role.name,
                    'description': auth_role.description,
                    'scopes': auth_role.scopes.split(',') if auth_role.scopes else []
                })

        return {
            'id': user_row.id,
            'email': user_row.email,
            'username': user_row.username,
            'first_name': user_row.first_name,
            'last_name': user_row.last_name,
            'active': user_row.active,
            'confirmed_at': user_row.confirmed_at.isoformat() if user_row.confirmed_at else None,
            'last_login_at': user_row.last_login_at.isoformat() if user_row.last_login_at else None,
            'login_count': user_row.login_count,
            'roles': roles,
            'created_at': user_row.created_at.isoformat() if user_row.created_at else None,
            'updated_at': user_row.updated_at.isoformat() if user_row.updated_at else None
        }

    @staticmethod
    def _hash_password(password: str) -> str:
        """Hash password using bcrypt.

        Args:
            password: Plain text password

        Returns:
            Hashed password string
        """
        salt = gensalt(rounds=12)
        hashed = hashpw(password.encode('utf-8'), salt)
        return hashed.decode('utf-8')
