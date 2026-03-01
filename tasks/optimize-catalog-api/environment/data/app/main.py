from fastapi import FastAPI, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from models import Product, Category, Review, User, Order, OrderItem

app = FastAPI(title="Product Catalog API")


@app.get("/api/products")
def list_products(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    category_id: int = None,
    sort: str = Query("id"),
    db: Session = Depends(get_db),
):
    """List products with optional filtering, sorting, and pagination."""
    query = db.query(Product)
    if category_id:
        query = query.filter(Product.category_id == category_id)
    products = query.all()

    # N+1: fetch category name one by one
    results = []
    for p in products:
        category = db.query(Category).filter(Category.id == p.category_id).first()
        results.append(
            {
                "id": p.id,
                "name": p.name,
                "price": p.price,
                "category": category.name if category else None,
                "created_at": p.created_at.isoformat(),
            }
        )

    # Sort in Python instead of SQL
    sort_keys = {
        "price": lambda x: (x["price"], x["id"]),
        "name": lambda x: (x["name"], x["id"]),
    }
    results.sort(key=sort_keys.get(sort, lambda x: x["id"]))

    # Paginate in Python instead of SQL
    total = len(results)
    start = (page - 1) * per_page
    end = start + per_page

    return {
        "items": results[start:end],
        "total": total,
        "page": page,
        "per_page": per_page,
    }


@app.get("/api/products/search")
def search_products(
    q: str = Query(..., min_length=1),
    min_rating: float = Query(0, ge=0, le=5),
    db: Session = Depends(get_db),
):
    """Search products by name/description with minimum rating filter."""
    # Full table scan with LIKE
    products = (
        db.query(Product)
        .filter(Product.name.ilike(f"%{q}%") | Product.description.ilike(f"%{q}%"))
        .all()
    )

    # N+1: compute avg rating per product
    results = []
    for p in products:
        reviews = db.query(Review).filter(Review.product_id == p.id).all()
        avg_rating = sum(r.rating for r in reviews) / len(reviews) if reviews else 0

        if avg_rating >= min_rating:
            results.append(
                {
                    "id": p.id,
                    "name": p.name,
                    "price": p.price,
                    "avg_rating": round(avg_rating, 2),
                    "review_count": len(reviews),
                }
            )

    return {"query": q, "results": results[:50]}


@app.get("/api/products/{product_id}/related")
def get_related_products(product_id: int, db: Session = Depends(get_db)):
    """Find products in the same category within +/- 20% price range."""
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    # Load ALL products in category (no price filter in SQL)
    category_products = (
        db.query(Product).filter(Product.category_id == product.category_id).all()
    )

    # Filter by price range in Python
    min_price = product.price * 0.8
    max_price = product.price * 1.2
    related = [
        p
        for p in category_products
        if p.id != product_id and min_price <= p.price <= max_price
    ]

    # N+1: get review count for each related product
    results = []
    for p in related[:10]:
        review_count = db.query(Review).filter(Review.product_id == p.id).count()
        results.append(
            {
                "id": p.id,
                "name": p.name,
                "price": p.price,
                "review_count": review_count,
            }
        )

    return {"product_id": product_id, "related": results}


@app.get("/api/analytics/category-performance")
def get_category_performance(db: Session = Depends(get_db)):
    """Revenue and average rating per category."""
    categories = db.query(Category).all()

    results = []
    for cat in categories:
        # Get product IDs for this category
        cat_products = (
            db.query(Product.id).filter(Product.category_id == cat.id).all()
        )
        product_ids = [p.id for p in cat_products]

        # Load all order items for these products and sum in Python
        revenue = 0.0
        if product_ids:
            order_items = (
                db.query(OrderItem)
                .filter(OrderItem.product_id.in_(product_ids))
                .all()
            )
            revenue = sum(item.quantity * item.unit_price for item in order_items)

        # Load all reviews for these products and average in Python
        avg_rating = 0.0
        if product_ids:
            reviews = (
                db.query(Review).filter(Review.product_id.in_(product_ids)).all()
            )
            if reviews:
                avg_rating = sum(r.rating for r in reviews) / len(reviews)

        results.append(
            {
                "category_id": cat.id,
                "category_name": cat.name,
                "total_revenue": round(revenue, 2),
                "avg_rating": round(avg_rating, 2),
                "product_count": len(product_ids),
            }
        )

    return {"categories": results}


@app.get("/api/orders/{user_id}/history")
def get_order_history(
    user_id: int,
    year: int = None,
    db: Session = Depends(get_db),
):
    """Order history for a user with line-item details."""
    # Load ALL orders, filter in Python
    all_orders = db.query(Order).all()
    user_orders = [o for o in all_orders if o.user_id == user_id]

    # Filter by year in Python
    if year:
        user_orders = [o for o in user_orders if o.created_at.year == year]

    # N+1: load order items per order
    results = []
    for order in user_orders:
        items = db.query(OrderItem).filter(OrderItem.order_id == order.id).all()

        # N+1 within N+1: load product per item
        order_items = []
        for item in items:
            product = db.query(Product).filter(Product.id == item.product_id).first()
            order_items.append(
                {
                    "product_name": product.name if product else "Unknown",
                    "quantity": item.quantity,
                    "unit_price": item.unit_price,
                }
            )

        results.append(
            {
                "order_id": order.id,
                "total": order.total,
                "created_at": order.created_at.isoformat(),
                "items": order_items,
            }
        )

    return {"user_id": user_id, "orders": results}
