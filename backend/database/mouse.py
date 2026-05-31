from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    Enum as SAEnum,
    ForeignKey,
    create_engine,
)
from sqlalchemy.orm import relationship, sessionmaker, declarative_base
from enum import Enum
from app.core.config import DATABASE_URL

Base = declarative_base()

class Hand_Fit(Enum):
    LEFT_HANDED = "left-handed"
    RIGHT_HANDED = "right-handed"
    BOTH = "both"

class Ergonomy(Enum):
    ERGONOMIC = "ergonomic"
    SYMMETRICAL = "symmetrical"
    AMBIDEXTROUS = "ambidextrous"

class Connectivity(Enum):
    STRICTLY_WIRELESS = "strictly wireless"
    WIRED_AND_WIRELESS = "wired + wireless"
    STRICTLY_WIRED = "strictly wired"

class Mouse(Base):
    __tablename__ = "mouse_model"

    id = Column(Integer, primary_key = True)
    product_name = Column(String, nullable = False)
    brand_name = Column(String, nullable = False)
    link = Column(String)
    img_link = Column(String)
    hand_fit = Column(SAEnum(Hand_Fit))
    ergonomy = Column(SAEnum(Ergonomy))
    connectivity = Column(SAEnum(Connectivity))
    max_DPI = Column(Integer)
    length = Column(Float) # mm
    width = Column(Float) # mm
    height = Column(Float) # mm
    weight = Column(Float) # g
    number_of_buttons = Column(Integer)
    min_battery_life = Column(Integer)
    max_battery_life = Column(Integer)
    min_polling_rate = Column(Integer)
    max_polling_rate = Column(Integer)
    other_features = Column(String)

    gaming_specs = relationship('Gaming_Mouse', backref='mouse', uselist=False)

    @property
    def rechargeable(self):
        if self.connectivity != Connectivity.STRICTLY_WIRED and self.min_battery_life != self.max_battery_life: # 1 month battery life
            return True
        return False

class Gaming_Mouse(Base):
    __tablename__ = "gaming_mouse_specs"

    mouse_id = Column(Integer, ForeignKey('mouse_model.id'), primary_key = True)
    acceleration = Column(Integer) # Maximum linear acceleration in G’s before mouse stops working properly.
    tracking_speed = Column(Integer) # Tracking speed measured in inches per second (IPS)

def create_session():
    # Async driver -> sync driver for the seeding/admin path.
    sync_url = DATABASE_URL.replace("+aiosqlite", "").replace("+asyncpg", "+psycopg2")
    engine = create_engine(sync_url)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    return Session()


# class PriceHistory(Base):
#     __tablename__ = "price_history"

#     mouse_id = Column(Integer, ForeignKey('mouse_model.id'), nullable=False)
#     date = Column(Date, nullable=False)
#     price = Column(Float, nullable=False)