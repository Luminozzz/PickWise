from database.models import db, Mouse, create_app

app = create_app()

with app.app_context():
    mouse = Mouse.query.filter_by(product_name="Razer Basilisk V3 Pro 35k").first()
    if mouse:
        mouse.img_link = 'https://assets3.razerzone.com/IGLejpy9uJjP2M8FsPZTU6rZ-Jg=/300x300/https%3A%2F%2Fmedias-p1.phoenix.razer.com%2Fsys-master-phoenix-images-container%2Fh5a%2Fh1c%2F9821720576030%2Fbasilisk-v3-pro-35k-500x500.png'
        db.session.commit()
        print("Updated!")
    else:
        print("Mouse not found.")