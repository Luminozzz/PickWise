import hashlib
import io
import requests
from PIL import Image
from rembg import remove, new_session
from sqlalchemy import Column, Integer, String, LargeBinary, DateTime, func
from sqlalchemy.orm import declarative_base, Session

Base = declarative_base()

class ProductImage(Base):
    __tablename__ = "product_images"
    id = Column(Integer, primary_key=True)
    source_url = Column(String, nullable=False)
    sha256 = Column(String(64), unique=True, nullable=False)  # dedupe
    mime = Column(String, default="image/png")
    width = Column(Integer)
    height = Column(Integer)
    data = Column(LargeBinary, nullable=False)  # BYTEA
    created_at = Column(DateTime(timezone=True), server_default=func.now())


# Load the model once — creating a session per image is very slow.
_session = new_session("isnet-general-use")

def fetch_image(url: str, timeout: int = 20) -> bytes:
    r = requests.get(url, timeout=timeout, headers={"User-Agent": "Mozilla/5.0"})
    r.raise_for_status()
    if not r.headers.get("Content-Type", "").startswith("image/"):
        raise ValueError(f"Not an image: {r.headers.get('Content-Type')}")
    return r.content

def strip_background(raw: bytes) -> tuple[bytes, int, int]:
    img = Image.open(io.BytesIO(raw)).convert("RGBA")
    out = remove(img, session=_session, post_process_mask=True)
    buf = io.BytesIO()
    out.save(buf, format="PNG", optimize=True)   # PNG — JPEG has no alpha
    return buf.getvalue(), out.width, out.height

def store(db: Session, url: str) -> ProductImage:
    png, w, h = strip_background(fetch_image(url))
    digest = hashlib.sha256(png).hexdigest()

    existing = db.query(ProductImage).filter_by(sha256=digest).one_or_none()
    if existing:
        return existing

    row = ProductImage(source_url=url, sha256=digest, width=w, height=h, data=png)
    db.add(row)
    db.commit()
    db.refresh(row)
    return row