from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password, verify_password
from app.models.user import User
from app.schemas.auth import UserRegister


class AuthService:


    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_user_by_id(self, user_id: int) -> User | None:
        """Find a user by their ID."""
        query = select(User).where(User.id == user_id)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_user_by_email(self, email: str) -> User | None:
        """Find a user by their email address."""
        query = select(User).where(User.email == email)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_user_by_username(self, username: str) -> User | None:
        """Find a user by their username."""
        query = select(User).where(User.username == username)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def create_user(self, user_data: UserRegister) -> User:

        # Check if email already taken
        existing_email = await self.get_user_by_email(user_data.email)
        if existing_email:
            raise ValueError("Email already registered")

        # Check if username already taken
        existing_username = await self.get_user_by_username(user_data.username)
        if existing_username:
            raise ValueError("Username already taken")

        # Create the user with hashed password
        user = User(
            email=user_data.email,
            username=user_data.username,
            hashed_password=hash_password(user_data.password),
        )

        self.db.add(user)
        await self.db.flush()  # Assigns the ID without committing
        await self.db.refresh(user)  # Reload to get generated fields

        return user

    async def authenticate_user(self, email: str, password: str) -> User | None:

        user = await self.get_user_by_email(email)

        if not user:
            return None

        if not verify_password(password, user.hashed_password):
            return None

        if not user.is_active:
            return None

        return user
