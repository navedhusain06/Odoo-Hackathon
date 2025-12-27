from sqlalchemy.orm import declarative_base

Base = declarative_base()

# IMPORTANT: import models so Alembic sees them
from app.db import models  # noqa: F401
