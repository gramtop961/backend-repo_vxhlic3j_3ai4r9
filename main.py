import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from bson import ObjectId

from database import db, create_document, get_documents

app = FastAPI(title="Watch Store API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class WatchIn(BaseModel):
    title: str
    description: Optional[str] = None
    price: float
    brand: str
    collection: str
    image: Optional[str] = None
    images: Optional[List[str]] = None
    in_stock: bool = True


@app.get("/")
def read_root():
    return {"message": "Watch Store API is running"}


@app.get("/test")
def test_database():
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": None,
        "database_name": None,
        "connection_status": "Not Connected",
        "collections": []
    }
    try:
        if db is not None:
            response["database"] = "✅ Connected & Working"
            response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
            response["database_name"] = "✅ Set" if os.getenv("DATABASE_NAME") else "❌ Not Set"
            try:
                collections = db.list_collection_names()
                response["collections"] = collections[:10]
            except Exception as e:
                response["database"] = f"⚠️  Connected but Error: {str(e)[:50]}"
        else:
            response["database"] = "❌ Database not initialized"
    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:50]}"
    return response


# Seed sample watches if collection empty
@app.post("/seed")
def seed_watches():
    if db is None:
        raise HTTPException(status_code=500, detail="Database not available")
    count = db["watch"].count_documents({})
    if count > 0:
        return {"inserted": 0, "message": "Already seeded"}

    sample = [
        {
            "title": "ChronoMaster Pro",
            "description": "Stainless steel chronograph with sapphire crystal.",
            "price": 599.0,
            "brand": "Aeternum",
            "collection": "chronograph",
            "image": "https://images.unsplash.com/photo-1518081461904-9acda21b54fd?q=80&w=1200&auto=format&fit=crop",
            "images": [
                "https://images.unsplash.com/photo-1518081461904-9acda21b54fd?q=80&w=1200&auto=format&fit=crop",
                "https://images.unsplash.com/photo-1490367532201-b9bc1dc483f6?q=80&w=1200&auto=format&fit=crop"
            ],
            "in_stock": True,
        },
        {
            "title": "Elegance Dress 40",
            "description": "Ultra-thin automatic dress watch in rose gold tone.",
            "price": 749.0,
            "brand": "Novelle",
            "collection": "dress",
            "image": "https://images.unsplash.com/photo-1516570161787-2fd917215a3d?q=80&w=1200&auto=format&fit=crop",
            "images": [
                "https://images.unsplash.com/photo-1516570161787-2fd917215a3d?q=80&w=1200&auto=format&fit=crop",
                "https://images.unsplash.com/photo-1524805444758-089113d48a6d?q=80&w=1200&auto=format&fit=crop"
            ],
            "in_stock": True,
        },
        {
            "title": "AquaSport 300",
            "description": "Professional diver with ceramic bezel and 300m WR.",
            "price": 899.0,
            "brand": "Pelagos",
            "collection": "sport",
            "image": "https://images.unsplash.com/photo-1518546305927-5a555bb7020d?q=80&w=1200&auto=format&fit=crop",
            "images": [
                "https://images.unsplash.com/photo-1518546305927-5a555bb7020d?q=80&w=1200&auto=format&fit=crop",
                "https://images.unsplash.com/photo-1483721310020-03333e577078?q=80&w=1200&auto=format&fit=crop"
            ],
            "in_stock": True,
        }
    ]
    for doc in sample:
        create_document("watch", doc)
    return {"inserted": len(sample)}


@app.get("/watches")
def list_watches(collection: Optional[str] = None, brand: Optional[str] = None, q: Optional[str] = None):
    if db is None:
        raise HTTPException(status_code=500, detail="Database not available")
    filter_obj = {}
    if collection:
        filter_obj["collection"] = collection
    if brand:
        filter_obj["brand"] = brand
    if q:
        filter_obj["title"] = {"$regex": q, "$options": "i"}
    docs = get_documents("watch", filter_obj)
    # Convert ObjectId
    for d in docs:
        d["id"] = str(d.pop("_id"))
    return {"items": docs}


@app.get("/watches/{watch_id}")
def get_watch(watch_id: str):
    if db is None:
        raise HTTPException(status_code=500, detail="Database not available")
    try:
        doc = db["watch"].find_one({"_id": ObjectId(watch_id)})
        if not doc:
            raise HTTPException(status_code=404, detail="Watch not found")
        doc["id"] = str(doc.pop("_id"))
        return doc
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid ID")


class AddToCartIn(BaseModel):
    cart_id: str
    product_id: str
    quantity: int = 1


@app.post("/cart/add")
def add_to_cart(payload: AddToCartIn):
    if db is None:
        raise HTTPException(status_code=500, detail="Database not available")
    product = db["watch"].find_one({"_id": ObjectId(payload.product_id)})
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    doc = {
        "cart_id": payload.cart_id,
        "product_id": payload.product_id,
        "quantity": payload.quantity,
        "price_snapshot": float(product.get("price", 0)),
        "title_snapshot": product.get("title"),
        "image_snapshot": product.get("image"),
    }
    create_document("cartitem", doc)
    return {"status": "ok"}


@app.get("/cart/{cart_id}")
def get_cart(cart_id: str):
    if db is None:
        raise HTTPException(status_code=500, detail="Database not available")
    items = get_documents("cartitem", {"cart_id": cart_id})
    for i in items:
        i["id"] = str(i.pop("_id"))
    total = sum((i.get("price_snapshot", 0) * i.get("quantity", 1)) for i in items)
    return {"items": items, "total": round(total, 2)}


class CheckoutIn(BaseModel):
    cart_id: str
    email: Optional[str] = None


@app.post("/checkout")
def checkout(payload: CheckoutIn):
    if db is None:
        raise HTTPException(status_code=500, detail="Database not available")
    cart_items = list(db['cartitem'].find({"cart_id": payload.cart_id}))
    if not cart_items:
        raise HTTPException(status_code=400, detail="Cart is empty")
    for i in cart_items:
        i['id'] = str(i.pop('_id'))
    subtotal = sum((i.get('price_snapshot',0) * i.get('quantity',1)) for i in cart_items)
    order_doc = {
        'cart_id': payload.cart_id,
        'items': cart_items,
        'subtotal': round(float(subtotal), 2),
        'status': 'paid',
        'email': payload.email
    }
    order_id = create_document('order', order_doc)
    return {"status": "paid", "order_id": order_id}


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
