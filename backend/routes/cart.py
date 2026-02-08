from fastapi import APIRouter, Depends, HTTPException
from typing import List
from datetime import datetime
import uuid

from models.cart import (
    CartItemAdd, CartItemUpdate, FavoriteAdd,
    PurchaseRequest, PurchaseRequestItem
)
from models.user import User
from routes.auth import get_current_user

router = APIRouter(tags=["cart"])

# Will be set from server.py
db = None

def set_db(database):
    global db
    db = database


# ==================== CART ROUTES ====================

@router.get("/cart")
async def get_cart(current_user: User = Depends(get_current_user)):
    """Get user's cart with product details"""
    cart = await db.carts.find_one({"user_id": current_user.id})
    
    if not cart or not cart.get("items"):
        return {"items": [], "total": 0}
    
    # Get product details for each item
    items_with_details = []
    total = 0
    
    for item in cart["items"]:
        product = await db.products.find_one({"id": item["product_id"]})
        if product:
            item_total = (product.get("price") or 0) * item["quantity"]
            total += item_total
            items_with_details.append({
                "product_id": item["product_id"],
                "quantity": item["quantity"],
                "product": {
                    "id": product["id"],
                    "name": product["name"],
                    "price": product.get("price"),
                    "image_url": product.get("image_url"),
                    "technology": product.get("technology"),
                    "category": product.get("category")
                },
                "subtotal": item_total
            })
    
    return {"items": items_with_details, "total": total}


@router.post("/cart")
async def add_to_cart(item: CartItemAdd, current_user: User = Depends(get_current_user)):
    """Add item to cart"""
    # Verify product exists
    product = await db.products.find_one({"id": item.product_id})
    if not product:
        raise HTTPException(status_code=404, detail="Produit non trouvé")
    
    cart = await db.carts.find_one({"user_id": current_user.id})
    
    if cart:
        # Check if product already in cart
        existing_item = next(
            (i for i in cart["items"] if i["product_id"] == item.product_id),
            None
        )
        
        if existing_item:
            # Update quantity
            await db.carts.update_one(
                {"user_id": current_user.id, "items.product_id": item.product_id},
                {
                    "$inc": {"items.$.quantity": item.quantity},
                    "$set": {"updated_at": datetime.utcnow()}
                }
            )
        else:
            # Add new item
            await db.carts.update_one(
                {"user_id": current_user.id},
                {
                    "$push": {"items": {"product_id": item.product_id, "quantity": item.quantity}},
                    "$set": {"updated_at": datetime.utcnow()}
                }
            )
    else:
        # Create new cart
        await db.carts.insert_one({
            "user_id": current_user.id,
            "items": [{"product_id": item.product_id, "quantity": item.quantity}],
            "updated_at": datetime.utcnow()
        })
    
    return {"message": "Produit ajouté au panier"}


@router.put("/cart/{product_id}")
async def update_cart_item(
    product_id: str,
    update: CartItemUpdate,
    current_user: User = Depends(get_current_user)
):
    """Update cart item quantity"""
    result = await db.carts.update_one(
        {"user_id": current_user.id, "items.product_id": product_id},
        {
            "$set": {
                "items.$.quantity": update.quantity,
                "updated_at": datetime.utcnow()
            }
        }
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Produit non trouvé dans le panier")
    
    return {"message": "Quantité mise à jour"}


@router.delete("/cart/{product_id}")
async def remove_from_cart(product_id: str, current_user: User = Depends(get_current_user)):
    """Remove item from cart"""
    result = await db.carts.update_one(
        {"user_id": current_user.id},
        {
            "$pull": {"items": {"product_id": product_id}},
            "$set": {"updated_at": datetime.utcnow()}
        }
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Panier non trouvé")
    
    return {"message": "Produit retiré du panier"}


@router.delete("/cart")
async def clear_cart(current_user: User = Depends(get_current_user)):
    """Clear entire cart"""
    await db.carts.update_one(
        {"user_id": current_user.id},
        {"$set": {"items": [], "updated_at": datetime.utcnow()}}
    )
    return {"message": "Panier vidé"}


# ==================== LOYALTY POINTS ====================

POINTS_PER_DINAR = 1  # 1 point per dinar spent
POINTS_REDEMPTION_RATE = 5 / 100  # 100 points = 5 DT

@router.get("/loyalty-points")
async def get_loyalty_points(current_user: User = Depends(get_current_user)):
    """Get user's loyalty points"""
    user = await db.users.find_one({"id": current_user.id})
    points = user.get("loyalty_points", 0) if user else 0
    total_spent = user.get("total_spent", 0) if user else 0
    
    # Calculate redemption value (100 points = 5 DT)
    redemption_value = (points // 100) * 5
    
    return {
        "points": points,
        "total_spent": total_spent,
        "redemption_value": redemption_value,
        "points_per_dinar": POINTS_PER_DINAR,
        "redemption_rate": "100 points = 5 DT"
    }


@router.post("/cart/validate")
async def validate_cart(
    current_user: User = Depends(get_current_user),
    use_points: bool = False
):
    """Validate cart and create purchase request with optional points redemption"""
    cart = await db.carts.find_one({"user_id": current_user.id})
    
    if not cart or not cart.get("items"):
        raise HTTPException(status_code=400, detail="Le panier est vide")
    
    # Build purchase request items with product details
    items = []
    total = 0
    
    for cart_item in cart["items"]:
        product = await db.products.find_one({"id": cart_item["product_id"]})
        if product:
            item_total = (product.get("price") or 0) * cart_item["quantity"]
            total += item_total
            items.append(PurchaseRequestItem(
                product_id=cart_item["product_id"],
                product_name=product["name"],
                product_price=product.get("price"),
                quantity=cart_item["quantity"]
            ))
    
    if not items:
        raise HTTPException(status_code=400, detail="Aucun produit valide dans le panier")
    
    # Get user details
    user = await db.users.find_one({"id": current_user.id})
    
    # Calculate discount from points
    discount = 0
    points_used = 0
    if use_points:
        available_points = user.get("loyalty_points", 0)
        # 100 points = 5 DT discount
        max_discount = (available_points // 100) * 5
        # Don't allow discount more than total
        discount = min(max_discount, total)
        points_used = int(discount / 5 * 100)  # Points to deduct
    
    final_total = total - discount
    
    # Create purchase request
    purchase_request = {
        "id": str(uuid.uuid4()),
        "user_id": current_user.id,
        "user_name": user.get("full_name") or user.get("email"),
        "user_email": user.get("email"),
        "user_phone": user.get("phone"),
        "items": [item.dict() for item in items],
        "total_estimated": total,
        "discount": discount,
        "points_used": points_used,
        "final_total": final_total,
        "status": "EN_ATTENTE",
        "admin_notes": None,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }
    
    await db.purchase_requests.insert_one(purchase_request)
    
    # Deduct points if used
    if points_used > 0:
        await db.users.update_one(
            {"id": current_user.id},
            {"$inc": {"loyalty_points": -points_used}}
        )
    
    # Clear cart
    await db.carts.update_one(
        {"user_id": current_user.id},
        {"$set": {"items": [], "updated_at": datetime.utcnow()}}
    )
    
    # Send email notification to admin
    try:
        from services.email_service import send_admin_purchase_notification
        await send_admin_purchase_notification(purchase_request, user)
    except Exception as e:
        print(f"Error sending admin notification: {e}")
    
    return {
        "message": "Demande d'achat envoyée avec succès",
        "request_id": purchase_request["id"],
        "points_used": points_used,
        "discount": discount,
        "final_total": final_total
    }


# ==================== FAVORITES ROUTES ====================

@router.get("/favorites")
async def get_favorites(current_user: User = Depends(get_current_user)):
    """Get user's favorites with product details"""
    favorites = await db.favorites.find_one({"user_id": current_user.id})
    
    if not favorites or not favorites.get("product_ids"):
        return {"products": []}
    
    # Get product details
    products = []
    for product_id in favorites["product_ids"]:
        product = await db.products.find_one({"id": product_id})
        if product:
            products.append({
                "id": product["id"],
                "name": product["name"],
                "description": product.get("description"),
                "price": product.get("price"),
                "image_url": product.get("image_url"),
                "technology": product.get("technology"),
                "category": product.get("category")
            })
    
    return {"products": products}


@router.post("/favorites")
async def add_to_favorites(item: FavoriteAdd, current_user: User = Depends(get_current_user)):
    """Add product to favorites"""
    # Verify product exists
    product = await db.products.find_one({"id": item.product_id})
    if not product:
        raise HTTPException(status_code=404, detail="Produit non trouvé")
    
    favorites = await db.favorites.find_one({"user_id": current_user.id})
    
    if favorites:
        if item.product_id in favorites.get("product_ids", []):
            return {"message": "Produit déjà dans les favoris"}
        
        await db.favorites.update_one(
            {"user_id": current_user.id},
            {
                "$push": {"product_ids": item.product_id},
                "$set": {"updated_at": datetime.utcnow()}
            }
        )
    else:
        await db.favorites.insert_one({
            "user_id": current_user.id,
            "product_ids": [item.product_id],
            "updated_at": datetime.utcnow()
        })
    
    return {"message": "Produit ajouté aux favoris"}


@router.delete("/favorites/{product_id}")
async def remove_from_favorites(product_id: str, current_user: User = Depends(get_current_user)):
    """Remove product from favorites"""
    result = await db.favorites.update_one(
        {"user_id": current_user.id},
        {
            "$pull": {"product_ids": product_id},
            "$set": {"updated_at": datetime.utcnow()}
        }
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Favoris non trouvés")
    
    return {"message": "Produit retiré des favoris"}


@router.get("/favorites/check/{product_id}")
async def check_favorite(product_id: str, current_user: User = Depends(get_current_user)):
    """Check if product is in favorites"""
    favorites = await db.favorites.find_one({"user_id": current_user.id})
    is_favorite = favorites and product_id in favorites.get("product_ids", [])
    return {"is_favorite": is_favorite}


# ==================== USER PURCHASE REQUESTS ====================

@router.get("/my-purchase-requests")
async def get_my_purchase_requests(current_user: User = Depends(get_current_user)):
    """Get user's purchase requests"""
    requests = await db.purchase_requests.find(
        {"user_id": current_user.id}
    ).sort("created_at", -1).to_list(100)
    
    for req in requests:
        req.pop("_id", None)
    
    return requests


@router.get("/my-purchase-requests/{request_id}/invoice")
async def download_my_invoice(request_id: str, current_user: User = Depends(get_current_user)):
    """Download invoice PDF for a validated purchase request (user)"""
    from services.invoice_service import base64_to_invoice
    from fastapi.responses import Response
    
    # Verify ownership
    request = await db.purchase_requests.find_one({"id": request_id, "user_id": current_user.id})
    if not request:
        raise HTTPException(status_code=404, detail="Demande non trouvée")
    
    # Check if validated
    if request.get("status") != "VALIDEE":
        raise HTTPException(status_code=400, detail="La facture n'est disponible que pour les commandes validées")
    
    # Get invoice
    invoice = await db.invoices.find_one({"purchase_request_id": request_id})
    if not invoice:
        raise HTTPException(status_code=404, detail="Facture non trouvée")
    
    pdf_bytes = base64_to_invoice(invoice["pdf_data"])
    
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="facture_{invoice["invoice_number"]}.pdf"'
        }
    )
