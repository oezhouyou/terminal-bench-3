import random
from datetime import datetime, timedelta
from sqlalchemy import create_engine, func
from sqlalchemy.orm import sessionmaker
from models import Base, Category, Product, User, Review, Order, OrderItem

random.seed(42)

DATABASE_URL = "postgresql:///catalog"
engine = create_engine(DATABASE_URL)
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)


def seed():
    session = Session()

    # --- Categories ---
    category_names = [
        "Electronics", "Books", "Clothing", "Home & Garden", "Sports",
        "Toys", "Automotive", "Health", "Food", "Music",
        "Movies", "Software", "Office", "Pet Supplies", "Beauty",
        "Tools", "Jewelry", "Baby", "Industrial", "Arts",
        "Outdoors", "Computers", "Shoes", "Furniture", "Appliances",
        "Games", "Travel", "Kitchen", "Garden", "Photography",
        "Audio", "Video", "Networking", "Storage", "Lighting",
        "Plumbing", "Electrical", "Painting", "Flooring", "Roofing",
        "Cleaning", "Safety", "Crafts", "Sewing", "Knitting",
        "Woodworking", "Metalworking", "Welding", "Printing", "Education",
    ]
    categories = []
    for i, name in enumerate(category_names):
        cat = Category(
            id=i + 1, name=name, description=f"Products in the {name} category"
        )
        categories.append(cat)
    session.add_all(categories)
    session.flush()

    # --- Users ---
    users = []
    for i in range(1000):
        user = User(
            id=i + 1,
            username=f"user_{i + 1}",
            email=f"user_{i + 1}@example.com",
        )
        users.append(user)
    session.add_all(users)
    session.flush()

    # --- Products ---
    adjectives = [
        "Premium", "Basic", "Pro", "Ultra", "Mini",
        "Mega", "Smart", "Classic", "Modern", "Vintage",
    ]
    nouns = [
        "Widget", "Gadget", "Device", "Tool", "Kit",
        "Set", "Pack", "Bundle", "System", "Module",
    ]
    products = []
    for i in range(10000):
        cat_id = (i % 50) + 1
        adj = adjectives[i % len(adjectives)]
        noun = nouns[(i // len(adjectives)) % len(nouns)]
        product = Product(
            id=i + 1,
            name=f"{adj} {noun} {i + 1}",
            description=(
                f"A high-quality {adj.lower()} {noun.lower()} for the "
                f"{category_names[cat_id - 1].lower()} enthusiast. "
                f"Features advanced technology and premium materials. "
                f"Model number: {i + 1}."
            ),
            price=round(random.uniform(5.0, 500.0), 2),
            category_id=cat_id,
            created_at=datetime(2024, 1, 1)
            + timedelta(hours=random.randint(0, 8760)),
        )
        products.append(product)
    session.add_all(products)
    session.flush()

    # --- Reviews ---
    reviews = []
    for i in range(50000):
        review = Review(
            id=i + 1,
            product_id=random.randint(1, 10000),
            user_id=random.randint(1, 1000),
            rating=random.randint(1, 5),
            comment=f"Review comment {i + 1}. "
            + ("Great product!" if random.random() > 0.3 else "Could be better."),
            created_at=datetime(2024, 1, 1)
            + timedelta(hours=random.randint(0, 8760)),
        )
        reviews.append(review)
    session.add_all(reviews)
    session.flush()

    # --- Orders ---
    orders = []
    for i in range(5000):
        order = Order(
            id=i + 1,
            user_id=random.randint(1, 1000),
            total=0,
            created_at=datetime(2024, 1, 1)
            + timedelta(hours=random.randint(0, 8760)),
        )
        orders.append(order)
    session.add_all(orders)
    session.flush()

    # --- Order Items ---
    order_items = []
    for i in range(15000):
        product = products[random.randint(0, 9999)]
        qty = random.randint(1, 5)
        item = OrderItem(
            id=i + 1,
            order_id=random.randint(1, 5000),
            product_id=product.id,
            quantity=qty,
            unit_price=product.price,
        )
        order_items.append(item)
    session.add_all(order_items)
    session.flush()

    # Update order totals from their items
    totals = (
        session.query(
            OrderItem.order_id,
            func.sum(OrderItem.quantity * OrderItem.unit_price).label("total"),
        )
        .group_by(OrderItem.order_id)
        .all()
    )
    total_map = {t.order_id: round(float(t.total), 2) for t in totals}
    for order in orders:
        order.total = total_map.get(order.id, 0)

    session.commit()
    session.close()
    print("Database seeded: 50 categories, 10000 products, 1000 users, "
          "50000 reviews, 5000 orders, 15000 order items")


if __name__ == "__main__":
    seed()
