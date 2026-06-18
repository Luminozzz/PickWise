from database.models import db, Gaming_Mouse, Mouse,Price_History, Mouse_Skins, create_app, Mouse_Connectivity
from sqlalchemy import text

app = create_app()

# Update rows
with app.app_context():
    mouse = Gaming_Mouse.query.filter_by(mouse_id=53).first()
    if mouse:
        mouse.rgb = True
        db.session.commit()
        print("Updated!")
    else:
        print("Mouse not found.")


# Drop Tables
# with app.app_context():
#     Price_History.__table__.drop(db.engine)
#     Price_History.__table__.create(db.engine)

# Remove rows
# with app.app_context():
#     mouse = Mouse.query.filter_by(id=46).first()
#     if mouse:
#         db.session.delete(mouse)
#         db.session.commit()
#         print("Deleted!")
#     else:
#         print("Mouse not found.")

