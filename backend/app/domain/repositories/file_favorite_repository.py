from typing import Protocol, Set


class FileFavoriteRepository(Protocol):
    """Per-user library file favorites (by file_id)."""

    async def set_favorite(self, user_id: str, file_id: str, is_favorite: bool) -> None:
        """Add or remove a file from the user's favorites."""
        ...

    async def list_favorite_file_ids(self, user_id: str) -> Set[str]:
        """Return all favorited file IDs for the user."""
        ...
