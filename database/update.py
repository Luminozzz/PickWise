from database.models import db, Mouse,Price_History, Mouse_Skins, create_app

app = create_app()

# Update rows
# with app.app_context():
#     mouse = Mouse.query.filter_by(product_name="Razer Viper V3 HyperSpeed").first()
#     if mouse:
#         mouse.img_link = 'https://assets3.razerzone.com/y265A8on-spu30uzfYMFCzGGBpU=/300x300/https%3A%2F%2Fmedias-p1.phoenix.razer.com%2Fsys-master-phoenix-images-container%2Fhb2%2Fhb9%2F9529652379678%2Fnaga-v2-pro-2-500x500.png'
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
#     mouse = Price_History.query.filter_by(product_name="Logitech M720 Triathlon").first()
#     if mouse:
#         db.session.delete(mouse)
#         db.session.commit()
#         print("Deleted!")
#     else:
#         print("Mouse not found.")
