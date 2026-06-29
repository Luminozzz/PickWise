from database.models import (
    Gaming_Mouse,
    Mouse,
    Price_History,
    Mouse_Skins,
    Mouse_Connectivity,
    SessionLocal,
    engine,
)

session = SessionLocal()

# Update rows
mouse = session.query(Gaming_Mouse).filter_by(mouse_id=53).first()
if mouse:
    mouse.rgb = True
    session.commit()
    print("Updated!")
else:
    print("Mouse not found.")


# Drop Tables
# Price_History.__table__.drop(engine)
# Price_History.__table__.create(engine)

# Remove rows
# mouse = session.query(Mouse).filter_by(id=46).first()
# if mouse:
#     session.delete(mouse)
#     session.commit()
#     print("Deleted!")
# else:
#     print("Mouse not found.")
