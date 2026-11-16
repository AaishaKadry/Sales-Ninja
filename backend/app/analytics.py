from sqlalchemy import func
from sqlalchemy.orm import Session
from .models import Sale

def analytics_summary(db: Session):
    revenue = db.query(func.coalesce(func.sum(Sale.quantity * Sale.unit_price), 0)).scalar()
    cost = db.query(func.coalesce(func.sum(Sale.quantity * Sale.unit_cost), 0)).scalar()
    orders = db.query(func.count(Sale.id)).scalar()
    units = db.query(func.coalesce(func.sum(Sale.quantity), 0)).scalar()
    customers = db.query(func.count(func.distinct(Sale.customer))).scalar()
    return {
        "revenue": round(float(revenue), 2),
        "profit": round(float(revenue - cost), 2),
        "orders": int(orders or 0),
        "units": int(units or 0),
        "customers": int(customers or 0),
        "average_order_value": round(float(revenue) / orders, 2) if orders else 0,
    }

def monthly_revenue(db: Session):
    rows = (db.query(func.strftime("%Y-%m", Sale.order_date).label("month"),
                     func.sum(Sale.quantity * Sale.unit_price).label("revenue"),
                     func.sum(Sale.quantity * (Sale.unit_price - Sale.unit_cost)).label("profit"))
            .group_by("month").order_by("month").all())
    # PostgreSQL uses to_char instead of SQLite strftime.
    if db.bind.dialect.name == "postgresql":
        rows = (db.query(func.to_char(Sale.order_date, "YYYY-MM").label("month"),
                         func.sum(Sale.quantity * Sale.unit_price).label("revenue"),
                         func.sum(Sale.quantity * (Sale.unit_price - Sale.unit_cost)).label("profit"))
                .group_by("month").order_by("month").all())
    return [{"month": r.month, "revenue": round(float(r.revenue or 0), 2),
             "profit": round(float(r.profit or 0), 2)} for r in rows]

def breakdown(db: Session, column, limit=7):
    rows = (db.query(column.label("name"),
                     func.sum(Sale.quantity * Sale.unit_price).label("revenue"))
            .group_by(column).order_by(func.sum(Sale.quantity * Sale.unit_price).desc())
            .limit(limit).all())
    return [{"name": r.name or "Unknown", "revenue": round(float(r.revenue or 0), 2)} for r in rows]
