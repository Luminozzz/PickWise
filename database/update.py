from database.models import db, Mouse,Price_History, Mouse_Skins, create_app
from sqlalchemy import text

app = create_app()

# Update rows
# with app.app_context():
#     mouse = Price_History.query.filter_by(product_name="Logitech Logitech G303 Shroud Edition").first()
#     if mouse:
#         mouse.product_name = 'Logitech G303 Shroud Edition'
#         db.session.commit()
#         print("Updated!")
#     else:
#         print("Mouse not found.")


# Drop Tables
# with app.app_context():
#     Price_History.__table__.drop(db.engine)
#     Price_History.__table__.create(db.engine)

# Remove rows
# with app.app_context():
#     mouse = Price_History.query.filter_by(product_name="Razer Cobra Pro").first()
#     if mouse:
#         db.session.delete(mouse)
#         db.session.commit()
#         print("Deleted!")
#     else:
#         print("Mouse not found.")

