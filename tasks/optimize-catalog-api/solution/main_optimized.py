from datetime import datetime

from fastapi import FastAPI, Depends, Query, HTTPException
from sqlalchemy import func, text
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
    query = db.query(
        Product.id,
        Product.name,
        Product.price,
        Category.name.label("category_name"),
        Product.created_at,
    ).join(Category, Product.category_id == Category.id)

    if category_id:
        query = query.filter(Product.category_id == category_id)

    total = query.count()

    sort_columns = {
        "price": [Product.price, Product.id],
        "name": [Product.name, Product.id],
    }
    for col in sort_columns.get(sort, [Product.id]):
        query = query.order_by(col)

    offset = (page - 1) * per_page
    rows = query.offset(offset).limit(per_page).all()

    items = [
        {
            "id": r.id,
            "name": r.name,
            "price": r.price,
            "category": r.category_name,
            "created_at": r.created_at.isoformat(),
        }
        for r in rows
    ]

    return {"items": items, "total": total, "page": page, "per_page": per_page}


@app.get("/api/products/search")
def search_products(
    q: str = Query(..., min_length=1),
    min_rating: float = Query(0, ge=0, le=5),
    db: Session = Depends(get_db),
):
    rows = (
        db.query(
            Product.id,
            Product.name,
            Product.price,
            func.coalesce(func.avg(Review.rating), 0).label("avg_rating"),
            func.count(Review.id).label("review_count"),
        )
        .outerjoin(Review, Review.product_id == Product.id)
        .filter(
            text("search_vector @@ plainto_tsquery('english', :q)").bindparams(q=q)
        )
        .group_by(Product.id, Product.name, Product.price)
        .having(func.coalesce(func.avg(Review.rating), 0) >= min_rating)
        .limit(50)
        .all()
    )

    return {
        "query": q,
        "results": [
            {
                "id": r.id,
                "name": r.name,
                "price": r.price,
                "avg_rating": round(float(r.avg_rating), 2),
                "review_count": r.review_count,
            }
            for r in rows
        ],
    }


@app.get("/api/products/{product_id}/related")
def get_related_products(product_id: int, db: Session = Depends(get_db)):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    min_price = product.price * 0.8
    max_price = product.price * 1.2

    rows = (
        db.query(
            Product.id,
            Product.name,
            Product.price,
            func.count(Review.id).label("review_count"),
        )
        .outerjoin(Review, Review.product_id == Product.id)
        .filter(
            Product.category_id == product.category_id,
            Product.id != product_id,
            Product.price >= min_price,
            Product.price <= max_price,
        )
        .group_by(Product.id, Product.name, Product.price)
        .limit(10)
        .all()
    )

    return {
        "product_id": product_id,
        "related": [
            {
                "id": r.id,
                "name": r.name,
                "price": r.price,
                "review_count": r.review_count,
            }
            for r in rows
        ],
    }


@app.get("/api/analytics/category-performance")
def get_category_performance(db: Session = Depends(get_db)):
    revenue_rows = (
        db.query(
            Category.id.label("category_id"),
            Category.name.label("category_name"),
            func.count(func.distinct(Product.id)).label("product_count"),
            func.coalesce(
                func.sum(OrderItem.quantity * OrderItem.unit_price), 0
            ).label("total_revenue"),
        )
        .outerjoin(Product, Product.category_id == Category.id)
        .outerjoin(OrderItem, OrderItem.product_id == Product.id)
        .group_by(Category.id, Category.name)
        .all()
    )

    rating_rows = (
        db.query(
            Category.id.label("category_id"),
            func.coalesce(func.avg(Review.rating), 0).label("avg_rating"),
        )
        .outerjoin(Product, Product.category_id == Category.id)
        .outerjoin(Review, Review.product_id == Product.id)
        .group_by(Category.id)
        .all()
    )

    rating_map = {r.category_id: float(r.avg_rating) for r in rating_rows}

    return {
        "categories": [
            {
                "category_id": r.category_id,
                "category_name": r.category_name,
                "total_revenue": round(float(r.total_revenue), 2),
                "avg_rating": round(rating_map.get(r.category_id, 0), 2),
                "product_count": r.product_count,
            }
            for r in revenue_rows
        ]
    }


@app.get("/api/orders/{user_id}/history")
def get_order_history(
    user_id: int,
    year: int = None,
    db: Session = Depends(get_db),
):
    query = db.query(Order).filter(Order.user_id == user_id)

    if year:
        start = datetime(year, 1, 1)
        end = datetime(year + 1, 1, 1)
        query = query.filter(Order.created_at >= start, Order.created_at < end)

    orders = query.all()

    if not orders:
        return {"user_id": user_id, "orders": []}

    order_ids = [o.id for o in orders]

    items_with_products = (
        db.query(
            OrderItem.order_id,
            Product.name.label("product_name"),
            OrderItem.quantity,
            OrderItem.unit_price,
        )
        .join(Product, OrderItem.product_id == Product.id)
        .filter(OrderItem.order_id.in_(order_ids))
        .all()
    )

    items_by_order = {}
    for item in items_with_products:
        items_by_order.setdefault(item.order_id, []).append(
            {
                "product_name": item.product_name,
                "quantity": item.quantity,
                "unit_price": item.unit_price,
            }
        )

    return {
        "user_id": user_id,
        "orders": [
            {
                "order_id": order.id,
                "total": order.total,
                "created_at": order.created_at.isoformat(),
                "items": items_by_order.get(order.id, []),
            }
            for order in orders
        ],
    }
