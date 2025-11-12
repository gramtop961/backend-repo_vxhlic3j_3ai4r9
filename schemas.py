"""
Database Schemas

Define your MongoDB collection schemas here using Pydantic models.
These schemas are used for data validation in your application.

Each Pydantic model represents a collection in your database.
Model name is converted to lowercase for the collection name:
- User -> "user" collection
- Product -> "product" collection
- BlogPost -> "blogs" collection
"""

from pydantic import BaseModel, Field
from typing import Optional, List

# Example schemas (replace with your own):

class User(BaseModel):
    """
    Users collection schema
    Collection name: "user" (lowercase of class name)
    """
    name: str = Field(..., description="Full name")
    email: str = Field(..., description="Email address")
    address: str = Field(..., description="Address")
    age: Optional[int] = Field(None, ge=0, le=120, description="Age in years")
    is_active: bool = Field(True, description="Whether user is active")

class Watch(BaseModel):
    """
    Watches collection schema
    Collection name: "watch"
    """
    title: str = Field(..., description="Watch title")
    description: Optional[str] = Field(None, description="Detailed description")
    price: float = Field(..., ge=0, description="Price in USD")
    brand: str = Field(..., description="Brand name")
    collection: str = Field(..., description="Collection/category, e.g., chronograph, dress, sport")
    image: Optional[str] = Field(None, description="Primary image URL")
    images: Optional[List[str]] = Field(default=None, description="Gallery image URLs")
    in_stock: bool = Field(True, description="Whether watch is in stock")

class CartItem(BaseModel):
    """
    Cart collection schema
    Collection name: "cartitem" (lowercase of class name)
    Items are grouped by cart_id (stored client-side in localStorage)
    """
    cart_id: str = Field(..., description="Client cart identifier")
    product_id: str = Field(..., description="Associated product/watch ObjectId as string")
    quantity: int = Field(1, ge=1, description="Quantity of the product")
    price_snapshot: float = Field(..., ge=0, description="Price at time of adding to cart")
    title_snapshot: Optional[str] = Field(None, description="Title at time of adding to cart")
    image_snapshot: Optional[str] = Field(None, description="Image at time of adding to cart")

class Order(BaseModel):
    """
    Orders collection schema
    Collection name: "order"
    """
    cart_id: str = Field(..., description="Cart identifier used for this order")
    items: List[dict] = Field(default_factory=list, description="Snapshot of items")
    subtotal: float = Field(..., ge=0)
    status: str = Field("paid", description="Order status in demo flow")
    email: Optional[str] = Field(None, description="Customer email (optional in demo)")

# Add your own schemas here:
# --------------------------------------------------

# Note: The Flames database viewer will automatically:
# 1. Read these schemas from GET /schema endpoint
# 2. Use them for document validation when creating/editing
# 3. Handle all database operations (CRUD) directly
# 4. You don't need to create any database endpoints!
