import os
from enum import Enum

from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    Boolean,
    Date,
    DateTime,
    JSON,
    Enum as SAEnum,
    ForeignKey,
    UniqueConstraint,
    create_engine,
    func,
)
from sqlalchemy.orm import relationship, declarative_base, sessionmaker

# Load backend/.env so DATABASE_URL / DB_SCHEMA are available when these
# tools run standalone (no-op if python-dotenv is missing or the file absent).
try:
    from dotenv import load_dotenv

    load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env"))
except Exception:
    pass

Base = declarative_base()


class Ergonomy(Enum):
    ERGONOMIC = "ergonomic"
    SYMMETRICAL = "symmetrical"
    AMBIDEXTROUS = "ambidextrous"
    NOT_MENTIONED = "none"


class Sort_By(Enum):
    REVIEW = "reviews"
    PRICE = "price"
    OFFICIAL = "official"


class Mouse(Base):
    __tablename__ = "mouse_model"

    id = Column(Integer, primary_key=True)
    product_name = Column(String, nullable=False, unique=True)
    brand_name = Column(String, nullable=False)
    link = Column(String)
    img_link = Column(String)  # main image (transparent product render preferred)
    alt_img_link = Column(String)  # secondary / marketing image (e.g. lifestyle shot)
    left_fit = Column(Boolean, default=False)
    ergonomy = Column(SAEnum(Ergonomy))
    max_DPI = Column(Integer)
    length = Column(Float)  # mm
    width = Column(Float)  # mm
    height = Column(Float)  # mm
    weight = Column(Float)  # g
    number_of_buttons = Column(Integer)
    min_battery_life = Column(Integer)
    max_battery_life = Column(Integer)
    other_features = Column(String)

    gaming_specs = relationship("Gaming_Mouse", backref="mouse", uselist=False)
    skins = relationship("Mouse_Skins", backref="mouse", lazy=True)
    connectivity = relationship("Mouse_Connectivity", backref="mouse", uselist=False)

    @property
    def max_polling_rate(self):
        # Polling rate lives on gaming_mouse_specs now, not mouse_model. Exposed
        # here so existing callers can keep reading mouse.max_polling_rate; it is
        # None for a mouse with no gaming specs. gaming_specs is eager-loaded on
        # the endpoints that use it, so reading this never triggers a lazy load.
        return self.gaming_specs.max_polling_rate if self.gaming_specs else None


class Gaming_Mouse(Base):
    __tablename__ = "gaming_mouse_specs"

    mouse_id = Column(Integer, ForeignKey("mouse_model.id"), primary_key=True)
    rgb = Column(Boolean, default=False)
    acceleration = Column(Integer)  # Max linear acceleration in G before tracking fails
    tracking_speed = Column(Integer)  # Tracking speed in inches per second (IPS)
    max_polling_rate = Column(Integer)  # Hz


class Mouse_Connectivity(Base):
    __tablename__ = "mouse_connectivity"

    mouse_id = Column(Integer, ForeignKey("mouse_model.id"), primary_key=True)
    bluetooth = Column(Boolean, default=False)
    dongle = Column(Boolean, default=False)
    wired = Column(Boolean, default=False)


class Mouse_Skins(Base):
    __tablename__ = "mouse_skins"

    id = Column(Integer, primary_key=True, autoincrement=True)
    mouse_id = Column(Integer, ForeignKey("mouse_model.id"), nullable=False)
    product_name = Column(String, nullable=False)
    colour = Column(String, nullable=False)
    img_link = Column(String, nullable=False)


class Price_History(Base):
    __tablename__ = "price_history"
    # One price per (mouse, store, colour, day). NULLS NOT DISTINCT so rows with
    # a NULL colour still can't duplicate (Postgres 15+).
    __table_args__ = (
        UniqueConstraint(
            "mouse_id",
            "store_name",
            "colour",
            "date",
            name="uq_price_history_mouse_store_colour_date",
            postgresql_nulls_not_distinct=True,
        ),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    mouse_id = Column(Integer, ForeignKey("mouse_model.id"), nullable=False)
    product_name = Column(String, nullable=False)
    date = Column(Date, nullable=False)
    currency = Column(String, nullable=False)
    price = Column(Float, nullable=False)
    num_of_stars = Column(Float, nullable=True)
    num_of_reviews = Column(Integer, nullable=True)
    colour = Column(String, nullable=True)
    store_link = Column(String, nullable=False)
    store_name = Column(String, nullable=False)
    sort_by = Column(SAEnum(Sort_By))


class Preference_Profile(Base):
    __tablename__ = "preference_profile"

    id = Column(String, primary_key=True)            # UUID4 string, generated server-side
    answers = Column(JSON, nullable=False)            # questionnaire answers dict
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


# --------------------------------------------------------------------------- #
# Engine / session — plain SQLAlchemy against Postgres (sync, via psycopg2).
# Reads the same DATABASE_URL / DB_SCHEMA env vars as the FastAPI app.
# --------------------------------------------------------------------------- #

DB_SCHEMA = os.environ.get("DB_SCHEMA", "lumino").strip()


def _sync_database_url():
    url = os.environ.get("DATABASE_URL", "").strip()
    if not url:
        # Offline fallback: local SQLite snapshot next to this module.
        return "sqlite:///" + os.path.join(os.path.dirname(__file__), "mouse.db")
    # The app uses async drivers; the seeding tools are synchronous.
    return url.replace("+asyncpg", "+psycopg2").replace("+aiosqlite", "")


def _make_engine():
    url = _sync_database_url()
    connect_args = {}
    if url.startswith("postgresql"):
        # Managed Postgres (DigitalOcean) requires SSL; pin the schema so
        # unqualified table names resolve, matching the async engine.
        connect_args = {
            "sslmode": "require",
            "options": f"-c search_path={DB_SCHEMA}",
        }
    return create_engine(url, connect_args=connect_args, future=True)


engine = _make_engine()
SessionLocal = sessionmaker(bind=engine, autoflush=False, future=True)


def init_db():
    """Create any tables that don't exist yet (existing ones are left as-is)."""
    Base.metadata.create_all(engine)


def get_session():
    return SessionLocal()
