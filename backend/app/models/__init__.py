# Alembic autogenerate가 모든 테이블을 인식하도록 여기서 전부 import
from app.db.base import Base
from app.models.clothing import ClothingItem
from app.models.recommendation import Outfit, OutfitFeedback, OutfitItem, Recommendation
from app.models.schedule import Schedule
from app.models.user import User

__all__ = ["Base", "User", "ClothingItem", "Schedule", "Recommendation", "Outfit", "OutfitItem", "OutfitFeedback"]
