from typing import List, Optional
from beanie import WriteRules
from app.domain.models.user import User
from app.domain.repositories.user_repository import UserRepository
from app.infrastructure.models.documents import UserDocument
import logging

logger = logging.getLogger(__name__)


class MongoUserRepository(UserRepository):
    """MongoDB implementation of UserRepository"""
    
    async def create_user(self, user: User) -> User:
        """Create a new user"""
        logger.info(f"Creating user: {user.fullname}")
        
        # Convert domain model to document
        user_doc = UserDocument.from_domain(user)
        
        # Save to database
        await user_doc.create()
        
        # Convert back to domain model
        result = user_doc.to_domain()
        logger.info(f"User created successfully: {result.id}")
        return result
    
    async def get_user_by_id(self, user_id: str) -> Optional[User]:
        """Get user by ID"""
        logger.debug(f"Getting user by ID: {user_id}")
        
        user_doc = await UserDocument.find_one(UserDocument.user_id == user_id)
        if not user_doc:
            logger.debug(f"User not found: {user_id}")
            return None
        
        return user_doc.to_domain()
    
    async def get_user_by_fullname(self, fullname: str) -> Optional[User]:
        """Get user by fullname"""
        logger.debug(f"Getting user by fullname: {fullname}")
        
        user_doc = await UserDocument.find_one(UserDocument.fullname == fullname)
        if not user_doc:
            logger.debug(f"User not found: {fullname}")
            return None
        
        return user_doc.to_domain()
    
    async def get_user_by_email(self, email: str) -> Optional[User]:
        """Get user by email"""
        logger.debug(f"Getting user by email: {email}")
        
        user_doc = await UserDocument.find_one(UserDocument.email == email.lower())
        if not user_doc:
            logger.debug(f"User not found: {email}")
            return None
        
        return user_doc.to_domain()
    
    async def update_user(self, user: User) -> User:
        """Update user information"""
        logger.info(f"Updating user: {user.id}")
        
        # Find existing document
        user_doc = await UserDocument.find_one(UserDocument.user_id == user.id)
        if not user_doc:
            raise ValueError(f"User not found: {user.id}")
        
        # Update document from domain model
        user_doc.update_from_domain(user)
        
        # Save to database
        await user_doc.save()
        
        # Convert back to domain model
        result = user_doc.to_domain()
        logger.info(f"User updated successfully: {result.id}")
        return result
    
    async def delete_user(self, user_id: str) -> bool:
        """Delete user by ID"""
        logger.info(f"Deleting user: {user_id}")
        
        user_doc = await UserDocument.find_one(UserDocument.user_id == user_id)
        if not user_doc:
            logger.warning(f"User not found for deletion: {user_id}")
            return False
        
        await user_doc.delete()
        logger.info(f"User deleted successfully: {user_id}")
        return True
    
    async def list_users(self, limit: int = 100, offset: int = 0) -> List[User]:
        """List users with pagination"""
        logger.debug(f"Listing users: limit={limit}, offset={offset}")
        
        user_docs = await UserDocument.find().skip(offset).limit(limit).to_list()
        
        users = [doc.to_domain() for doc in user_docs]
        logger.debug(f"Found {len(users)} users")
        return users
    
    async def fullname_exists(self, fullname: str) -> bool:
        """Check if fullname exists"""
        logger.debug(f"Checking if fullname exists: {fullname}")
        
        user_doc = await UserDocument.find_one(UserDocument.fullname == fullname)
        exists = user_doc is not None
        logger.debug(f"Fullname exists: {exists}")
        return exists
    
    async def email_exists(self, email: str) -> bool:
        """Check if email exists"""
        logger.debug(f"Checking if email exists: {email}")
        
        user_doc = await UserDocument.find_one(UserDocument.email == email.lower())
        exists = user_doc is not None
        logger.debug(f"Email exists: {exists}")
        return exists 