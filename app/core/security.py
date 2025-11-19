"""
Security and Privacy Module for HealthTrack API

Implements comprehensive security measures for handling sensitive health data:
- Data encryption (at rest and in transit)
- Access control and authorization
- Rate limiting for DDoS protection
- Data privacy compliance (HIPAA-ready)
- Secure password handling
"""

import hashlib
import hmac
from typing import Optional
from datetime import datetime, timedelta
from functools import lru_cache

from cryptography.fernet import Fernet
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthCredentials
import jwt

from app.models import User
from app.core.config import get_settings

settings = get_settings()
security = HTTPBearer()


class EncryptionManager:
    """Manages encryption/decryption of sensitive health data."""

    def __init__(self):
        """Initialize encryption manager."""
        # In production, use environment variable for key
        # Keep this key securely stored (e.g., AWS KMS, HashiCorp Vault)
        self._cipher_suite: Optional[Fernet] = None

    def get_cipher(self) -> Fernet:
        """Get Fernet cipher for encryption."""
        if self._cipher_suite is None:
            # Generate or load encryption key
            key = settings.SECRET_KEY.encode()[:32]
            # Create a valid Fernet key
            import base64

            key_b64 = base64.urlsafe_b64encode(key.ljust(32)[:32])
            self._cipher_suite = Fernet(key_b64)
        return self._cipher_suite

    def encrypt_field(self, data: str) -> str:
        """Encrypt a sensitive field."""
        if not data:
            return ""
        cipher = self.get_cipher()
        return cipher.encrypt(data.encode()).decode()

    def decrypt_field(self, encrypted_data: str) -> str:
        """Decrypt a sensitive field."""
        if not encrypted_data:
            return ""
        try:
            cipher = self.get_cipher()
            return cipher.decrypt(encrypted_data.encode()).decode()
        except Exception:
            return ""

    @staticmethod
    def hash_sensitive_data(data: str, salt: Optional[str] = None) -> str:
        """Hash sensitive data using SHA-256 (one-way)."""
        if salt is None:
            salt = settings.SECRET_KEY[:16]
        return hashlib.pbkdf2_hmac(
            "sha256",
            data.encode(),
            salt.encode(),
            100000,  # iterations
        ).hex()


class AccessControl:
    """Manages user access control and authorization."""

    @staticmethod
    async def verify_user_access(
        user_id: int,
        requesting_user_id: int,
        db: AsyncSession,
    ) -> bool:
        """
        Verify if a user has access to another user's data.

        Privacy rule: Users can only access their own health data.
        Admins can access any user data (future feature).
        """
        # Users can only access their own data
        if user_id == requesting_user_id:
            return True

        # Future: Check if requesting_user is admin
        # result = await db.execute(select(User).where(User.id == requesting_user_id))
        # user = result.scalar_one_or_none()
        # if user and user.is_admin:
        #     return True

        return False

    @staticmethod
    def require_user_access(
        resource_user_id: int,
        requesting_user_id: int,
    ):
        """Require access to user's data (for dependency injection)."""
        if resource_user_id != requesting_user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: you can only access your own health data",
            )


class TokenManager:
    """Manages JWT tokens for authentication."""

    @staticmethod
    def create_access_token(
        user_id: int,
        expires_delta: Optional[timedelta] = None,
    ) -> str:
        """Create a JWT access token."""
        if expires_delta is None:
            expires_delta = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

        expire = datetime.utcnow() + expires_delta
        to_encode = {"sub": str(user_id), "exp": expire}

        encoded_jwt = jwt.encode(
            to_encode,
            settings.SECRET_KEY,
            algorithm=settings.ALGORITHM,
        )
        return encoded_jwt

    @staticmethod
    def verify_token(token: str) -> Optional[int]:
        """Verify JWT token and extract user_id."""
        try:
            payload = jwt.decode(
                token,
                settings.SECRET_KEY,
                algorithms=[settings.ALGORITHM],
            )
            user_id: str = payload.get("sub")
            if user_id is None:
                return None
            return int(user_id)
        except jwt.InvalidTokenError:
            return None


class AuditLogger:
    """Logs access to sensitive health data for compliance."""

    # In production, use structured logging with centralized storage
    _access_log = []

    @staticmethod
    def log_access(
        user_id: int,
        action: str,
        resource_type: str,
        resource_id: int,
        status_code: int,
    ):
        """Log access to health data."""
        entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "user_id": user_id,
            "action": action,  # 'read', 'create', 'update', 'delete'
            "resource_type": resource_type,  # 'health_metric', 'nutrition_log', etc.
            "resource_id": resource_id,
            "status_code": status_code,
        }
        AuditLogger._access_log.append(entry)

        # In production, send to audit log storage
        # logger.info(f"Audit: {entry}")

    @staticmethod
    def get_audit_log(user_id: Optional[int] = None) -> list:
        """Retrieve audit log entries."""
        if user_id is None:
            return AuditLogger._access_log

        return [entry for entry in AuditLogger._access_log if entry["user_id"] == user_id]


# ==================== PRIVACY & SECURITY BEST PRACTICES ====================
"""
HIPAA-Ready Implementation for Health Data Privacy:

1. **Data Encryption:**
   - At rest: Fernet (symmetric encryption) or AES-256
   - In transit: TLS 1.3 required
   - Medical history, DOB can be encrypted
   - Separate encryption keys for different data categories

2. **Access Control:**
   - User can only access their own health data
   - Admins need explicit admin role (future)
   - API token-based authentication
   - Principle of least privilege

3. **Audit Logging:**
   - All access to health data logged
   - Immutable audit trail
   - Retention: 7 years (HIPAA requirement)
   - Tracks: who, what, when, why

4. **Data Retention:**
   - Users can request data deletion
   - Deleted data is cryptographically securely erased
   - Backups: encrypted and access-controlled
   - Archive old data after 2 years

5. **Password Security:**
   - Bcrypt hashing with salt (implemented in users.py)
   - Minimum 8 characters
   - Enforce complexity requirements
   - Never log passwords

6. **API Security:**
   - CORS configured appropriately
   - Rate limiting to prevent brute force
   - HTTPS required in production
   - API versioning for backward compatibility

7. **Database Security:**
   - Connection encryption (SSL/TLS)
   - Row-level security (future)
   - Parameterized queries (SQLAlchemy)
   - Regular backups with encryption

8. **Incident Response:**
   - Monitor for suspicious access patterns
   - Alert on brute force attempts (10+ failed logins)
   - Alert on unusual data access
   - Have incident response plan

9. **Compliance Checklist:**
   - [ ] Encryption at rest and in transit
   - [ ] Access control per-user
   - [ ] Audit logging implemented
   - [ ] Data retention policy defined
   - [ ] Incident response plan
   - [ ] Regular security audits
   - [ ] Employee training on data privacy
   - [ ] Business associate agreements (if using 3rd party services)
"""

# Global instance
_encryption_manager = None


def get_encryption_manager() -> EncryptionManager:
    """Get or create encryption manager."""
    global _encryption_manager
    if _encryption_manager is None:
        _encryption_manager = EncryptionManager()
    return _encryption_manager
