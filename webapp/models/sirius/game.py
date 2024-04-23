from datetime import datetime

from sqlalchemy import TIMESTAMP, Boolean, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column

from webapp.models.meta import DEFAULT_SCHEMA, Base


class Game(Base):
    __tablename__ = 'game'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    user_id: Mapped[int] = mapped_column(Integer, ForeignKey(f'{DEFAULT_SCHEMA}.user.id'), index=True)

    won: Mapped[bool] = mapped_column(Boolean)

    ships_sank: Mapped[int] = mapped_column(Integer)

    ships_destroyed: Mapped[int] = mapped_column(Integer)

    timestamp: Mapped[datetime] = mapped_column(TIMESTAMP, default=datetime.utcnow)
