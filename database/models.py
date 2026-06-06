from flask_sqlalchemy import SQLAlchemy
from enum import Enum
from flask import Flask
import os
from flask_migrate import Migrate
from sqlalchemy import MetaData

naming_convention = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}

migrate = Migrate()
db = SQLAlchemy(metadata=MetaData(naming_convention=naming_convention))

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

class Sort_By(Enum):
    REVIEW = 'reviews'
    PRICE = 'price'
    OFFICIAL = 'official'

class Mouse(db.Model):
    __tablename__ = "mouse_model"

    id = db.Column(db.Integer, primary_key = True)
    product_name = db.Column(db.String, nullable = False, unique = True)
    brand_name = db.Column(db.String, nullable = False)
    link = db.Column(db.String)
    img_link = db.Column(db.String)
    hand_fit = db.Column(db.Enum(Hand_Fit))
    ergonomy = db.Column(db.Enum(Ergonomy))
    connectivity = db.Column(db.Enum(Connectivity))
    max_DPI = db.Column(db.Integer)
    length = db.Column(db.Float) # mm
    width = db.Column(db.Float) # mm
    height = db.Column(db.Float) # mm
    weight = db.Column(db.Float) # g
    number_of_buttons = db.Column(db.Integer)
    min_battery_life = db.Column(db.Integer)
    max_battery_life = db.Column(db.Integer)
    min_polling_rate = db.Column(db.Integer)
    max_polling_rate = db.Column(db.Integer)
    other_features = db.Column(db.String)

    gaming_specs = db.relationship('Gaming_Mouse', backref='mouse', uselist=False)
    skins = db.relationship('Mouse_Skins', backref='mouse', lazy=True)
    @property
    def rechargeable(self):
        if self.connectivity != Connectivity.STRICTLY_WIRED and self.min_battery_life != self.max_battery_life: # 1 month battery life
            return True
        return False
    
class Gaming_Mouse(db.Model):
    __tablename__ = "gaming_mouse_specs"

    mouse_id = db.Column(db.Integer, db.ForeignKey('mouse_model.id'), primary_key = True)
    acceleration = db.Column(db.Integer) # Maximum linear acceleration in G’s before mouse stops working properly.
    tracking_speed = db.Column(db.Integer) # Tracking speed measured in inches per second (IPS)

class Mouse_Skins(db.Model):
    __tablename__ = "mouse_skins"

    id = db.Column(db.Integer, primary_key = True, autoincrement=True)
    mouse_id = db.Column(db.Integer, db.ForeignKey('mouse_model.id'), nullable=False)
    product_name = db.Column(db.String, nullable=False)
    colour = db.Column(db.String, nullable=False)
    img_link = db.Column(db.String, nullable=False)

class Price_History(db.Model):
    __tablename__ = "price_history"

    id = db.Column(db.Integer, primary_key = True, autoincrement=True)
    mouse_id = db.Column(db.Integer, db.ForeignKey('mouse_model.id'), nullable=False)
    product_name = db.Column(db.String, nullable=False)
    date = db.Column(db.Date, nullable=False)
    currency = db.Column(db.String, nullable=False)
    price = db.Column(db.Float, nullable=False)
    num_of_stars = db.Column(db.Float, nullable=True)
    num_of_reviews = db.Column(db.Integer, nullable=True)
    colour = db.Column(db.String, nullable=True)
    store_link = db.Column(db.String, nullable=False)
    store_name = db.Column(db.String, nullable=False)
    sort_by = db.Column(db.Enum(Sort_By))


def create_app():
    app = Flask(__name__)
    db_path = os.path.join(os.path.dirname(__file__), 'mice3.db')
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    db.init_app(app)
    migrate.init_app(app, db, render_as_batch=True)
    return app






