"""Bank products endpoints."""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from app.database import get_db
from app.api.dependencies import get_current_user
from app.models.user import User
from app.models.bank_connection import BankConnection
from app.integrations.vtb_api import OpenBankingClient
from app.utils.security import decrypt_token

router = APIRouter()


@router.get("/")
async def get_products(
    bank_code: Optional[str] = None,
    product_type: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get bank products from all connected banks or specific bank."""
    
    # Get user's connections
    query = db.query(BankConnection).filter(
        BankConnection.user_id == current_user.id,
        BankConnection.status == 'ACTIVE'
    )
    
    if bank_code:
        query = query.filter(BankConnection.bank_provider == bank_code.upper())
    
    connections = query.all()
    
    if not connections:
        return {"products": []}
    
    all_products = []
    
    for connection in connections:
        try:
            # Decrypt token
            client_token = decrypt_token(connection.access_token_encrypted)
            
            # Get products from bank
            async with OpenBankingClient(connection.bank_provider.value.lower()) as client:
                products_response = await client.get_products(client_token)
                products_data = products_response.get("data", {}).get("product", [])
                
                # Enrich with bank info
                for product in products_data:
                    product["bank_code"] = connection.bank_provider.value.lower()
                    product["bank_name"] = {
                        "vbank": "Virtual Bank",
                        "abank": "Awesome Bank",
                        "sbank": "Smart Bank"
                    }.get(connection.bank_provider.value.lower(), connection.bank_provider.value)
                    
                    # Filter by product type if specified (case-insensitive)
                    product_type_from_api = product.get("productType", "").upper()
                    filter_type = product_type.upper() if product_type else None
                    
                    if not filter_type or product_type_from_api == filter_type:
                        all_products.append(product)
        
        except Exception as e:
            print(f"Error fetching products from {connection.bank_provider}: {e}")
            continue
    
    return {"products": all_products, "total": len(all_products)}


@router.get("/{product_id}")
async def get_product(
    product_id: str,
    bank_code: str = Query(..., description="Bank code (vbank, abank, sbank)"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get specific product details."""
    
    # Get connection for this bank
    connection = db.query(BankConnection).filter(
        BankConnection.user_id == current_user.id,
        BankConnection.bank_provider == bank_code.upper(),
        BankConnection.status == 'ACTIVE'
    ).first()
    
    if not connection:
        from fastapi import HTTPException, status
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No active connection to {bank_code}"
        )
    
    try:
        # Decrypt token
        client_token = decrypt_token(connection.access_token_encrypted)
        
        # Get product details
        async with OpenBankingClient(bank_code.lower()) as client:
            product = await client.get_product(client_token, product_id)
            
            # Enrich with bank info
            product["bank_code"] = bank_code.lower()
            product["bank_name"] = {
                "vbank": "Virtual Bank",
                "abank": "Awesome Bank",
                "sbank": "Smart Bank"
            }.get(bank_code.lower(), bank_code)
            
            return product
    
    except Exception as e:
        from fastapi import HTTPException, status
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch product: {str(e)}"
        )


@router.get("/compare/{product_type}")
async def compare_products(
    product_type: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Compare products of the same type across all banks."""
    
    # Get products of specific type
    result = await get_products(
        bank_code=None,
        product_type=product_type,
        current_user=current_user,
        db=db
    )
    
    products = result.get("products", [])
    
    if not products:
        return {
            "product_type": product_type,
            "comparison": [],
            "best_offer": None
        }
    
    # Sort by best offer (depends on product type)
    if product_type == "DEPOSIT":
        # For deposits, higher rate is better
        products.sort(key=lambda p: float(p.get("interestRate", 0)), reverse=True)
    elif product_type == "LOAN":
        # For loans, lower rate is better
        products.sort(key=lambda p: float(p.get("interestRate", 999)))
    
    return {
        "product_type": product_type,
        "comparison": products,
        "best_offer": products[0] if products else None,
        "total": len(products)
    }

