import csv, io
from datetime import date
from fastapi import FastAPI, Depends, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import desc
from .config import settings
from .database import Base, engine, get_db
from .models import Sale
from .schemas import SaleCreate, SaleOut, ChatRequest
from .analytics import analytics_summary, monthly_revenue, breakdown
from .bedrock import ask_bedrock

Base.metadata.create_all(bind=engine)
app = FastAPI(title=settings.app_name, version="1.0.0", description="Sales analytics and Amazon Bedrock copilot")
app.add_middleware(CORSMiddleware, allow_origins=[x.strip() for x in settings.cors_origins.split(",")],
                   allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

@app.get("/api/health")
def health():
    return {"status": "ok", "service": "sales-ninja"}

@app.get("/api/sales", response_model=list[SaleOut])
def list_sales(limit: int = 100, offset: int = 0, db: Session = Depends(get_db)):
    if limit < 1 or limit > 500: raise HTTPException(400, "limit must be between 1 and 500")
    return db.query(Sale).order_by(desc(Sale.order_date), desc(Sale.id)).offset(offset).limit(limit).all()

@app.post("/api/sales", response_model=SaleOut, status_code=201)
def create_sale(payload: SaleCreate, db: Session = Depends(get_db)):
    if db.query(Sale).filter_by(order_id=payload.order_id).first():
        raise HTTPException(409, "order_id already exists")
    sale = Sale(**payload.model_dump())
    db.add(sale); db.commit(); db.refresh(sale)
    return sale

@app.delete("/api/sales/{sale_id}", status_code=204)
def delete_sale(sale_id: int, db: Session = Depends(get_db)):
    sale = db.get(Sale, sale_id)
    if not sale: raise HTTPException(404, "Sale not found")
    db.delete(sale); db.commit()

@app.get("/api/analytics/summary")
def summary(db: Session = Depends(get_db)):
    return analytics_summary(db)

@app.get("/api/analytics/monthly")
def monthly(db: Session = Depends(get_db)):
    return monthly_revenue(db)

@app.get("/api/analytics/products")
def products(db: Session = Depends(get_db)):
    return breakdown(db, Sale.product)

@app.get("/api/analytics/regions")
def regions(db: Session = Depends(get_db)):
    return breakdown(db, Sale.region)

@app.post("/api/sales/upload")
async def upload_sales(file: UploadFile = File(...), db: Session = Depends(get_db)):
    if not file.filename.lower().endswith(".csv"):
        raise HTTPException(400, "Upload a CSV file")
    raw = await file.read()
    if len(raw) > settings.max_upload_mb * 1024 * 1024:
        raise HTTPException(413, f"File exceeds {settings.max_upload_mb} MB limit")
    try:
        reader = csv.DictReader(io.StringIO(raw.decode("utf-8-sig")))
        required = {"order_id","order_date","customer","product","category","region","quantity","unit_price","unit_cost"}
        if not reader.fieldnames or not required.issubset(set(reader.fieldnames)):
            raise ValueError("CSV must contain: " + ", ".join(sorted(required)))
        added, skipped = 0, 0
        for row in reader:
            try:
                order_id = row["order_id"].strip()
                if not order_id or db.query(Sale).filter_by(order_id=order_id).first():
                    skipped += 1; continue
                sale = Sale(order_id=order_id, order_date=date.fromisoformat(row["order_date"]),
                    customer=row["customer"].strip() or "Unknown", product=row["product"].strip(),
                    category=row["category"].strip() or "Uncategorized", region=row["region"].strip() or "Unknown",
                    quantity=int(row["quantity"]), unit_price=float(row["unit_price"]), unit_cost=float(row["unit_cost"]))
                if sale.quantity < 1 or sale.unit_price < 0 or sale.unit_cost < 0: raise ValueError("invalid numeric value")
                db.add(sale); added += 1
            except (ValueError, TypeError, KeyError):
                skipped += 1
        db.commit()
        return {"inserted": added, "skipped": skipped}
    except UnicodeDecodeError:
        raise HTTPException(400, "CSV must be UTF-8 encoded")

@app.post("/api/chat")
def chat(payload: ChatRequest, db: Session = Depends(get_db)):
    snapshot = {
        "summary": analytics_summary(db),
        "monthly_revenue": monthly_revenue(db),
        "top_products": breakdown(db, Sale.product, 10),
        "top_regions": breakdown(db, Sale.region, 10),
        "data_rows": db.query(Sale).count(),
    }
    if not snapshot["data_rows"]:
        return {"answer": "There is no sales data yet. Upload the sample CSV or add sales before asking questions.", "source": "local"}
    try:
        answer = ask_bedrock(payload.question, snapshot)
        return {"answer": answer, "source": "amazon-bedrock", "data": snapshot}
    except RuntimeError as exc:
        raise HTTPException(503, str(exc))
