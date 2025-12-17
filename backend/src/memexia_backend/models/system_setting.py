from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column

from typing import Optional

from ..database import Base

class SystemSetting(Base):
    """
    Model for storing dynamic system configurations.
    Key-value pairs where value is stored as JSON string.
    """
    __tablename__ = "system_settings"

    key: Mapped[str] = mapped_column(String, primary_key=True, index=True)
    value: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String, nullable=True)
