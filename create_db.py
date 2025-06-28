from her.platform.db.models import Base
from her.platform.db import engine

Base.metadata.create_all(engine)
