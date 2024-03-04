from sqlalchemy import Integer, BigInteger
from sqlalchemy.orm import Mapped, mapped_column

from webapp.models.meta import Base



class User(Base):
    __tablename__ = 'user'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    username: Mapped[int] = mapped_column(BigInteger, unique=True)
