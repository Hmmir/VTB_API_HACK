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
    """Get bank products from connected banks (requires auth since API update)."""
    
    # Получаем активные подключения пользователя
    connections = db.query(BankConnection).filter(
        BankConnection.user_id == current_user.id,
        BankConnection.status == 'ACTIVE'
    ).all()
    
    if bank_code:
        connections = [c for c in connections if c.bank_provider.value.lower() == bank_code.lower()]
    
    all_products = []
    
    for connection in connections:
        bank = connection.bank_provider.value.lower()
        try:
            # Расшифровываем токен
            try:
                client_token = decrypt_token(connection.access_token_encrypted)
            except Exception as decrypt_error:
                # Если токен не расшифровывается, пробуем обновить его
                print(f"Token decrypt failed for {bank}, refreshing connection: {decrypt_error}")
                try:
                    # Пробуем обновить токен через refresh_token
                    from app.services.openbanking_service import OpenBankingService
                    new_token = await OpenBankingService.refresh_access_token(db, connection.id)
                    client_token = new_token
                except Exception as refresh_error:
                    print(f"Token refresh failed for {bank}, skipping: {refresh_error}")
                    continue
            
            # Получаем продукты с авторизацией (API изменился, теперь требует токен)
            async with OpenBankingClient(bank) as client:
                products_response = await client.get_products(access_token=client_token)
                
                # Handle different response formats
                if isinstance(products_response, list):
                    products_data = products_response
                elif isinstance(products_response, dict):
                    products_data = products_response.get("data", {})
                    if isinstance(products_data, dict):
                        products_data = products_data.get("product", [])
                    elif not isinstance(products_data, list):
                        products_data = []
                else:
                    products_data = []
                
                # Enrich with bank info
                for product in products_data:
                    if not isinstance(product, dict):
                        continue
                    
                    product["bank_code"] = bank
                    product["bank_name"] = {
                        "vbank": "Virtual Bank",
                        "abank": "Awesome Bank",
                        "sbank": "Smart Bank"
                    }.get(bank, bank)
                    
                    # Filter by product type if specified (case-insensitive)
                    product_type_from_api = product.get("productType", "").upper()
                    filter_type = product_type.upper() if product_type else None
                    
                    if not filter_type or product_type_from_api == filter_type:
                        all_products.append(product)
        
        except Exception as e:
            print(f"Error fetching products from {bank}: {e}")
            import traceback
            traceback.print_exc()
            continue
    
    # Fallback: если продукты не загрузились, показываем демо
    if len(all_products) == 0:
        print("⚠️ No products from banks, using demo products")
        all_products = [
            {"productId": "DEMO_DEPOSIT_12M", "productName": "Депозит 12 мес (8.5%)", "productType": "DEPOSIT", "interestRate": 8.5, "minAmount": 10000, "term": 12, "bank_code": "vbank", "bank_name": "Virtual Bank"},
            {"productId": "DEMO_DEPOSIT_6M", "productName": "Депозит 6 мес (7.5%)", "productType": "DEPOSIT", "interestRate": 7.5, "minAmount": 5000, "term": 6, "bank_code": "abank", "bank_name": "Awesome Bank"},
            {"productId": "DEMO_LOAN", "productName": "Потребительский кредит (12.9%)", "productType": "LOAN", "interestRate": 12.9, "minAmount": 50000, "maxAmount": 3000000, "term": 60, "bank_code": "sbank", "bank_name": "Smart Bank"},
            {"productId": "DEMO_CARD", "productName": "Кредитная карта Standard", "productType": "CREDIT_CARD", "interestRate": 19.9, "minAmount": 10000, "maxAmount": 500000, "bank_code": "vbank", "bank_name": "Virtual Bank"}
        ]
    
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

