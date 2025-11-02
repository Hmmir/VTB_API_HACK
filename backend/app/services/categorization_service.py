"""Service for automatic transaction categorization."""
from typing import Optional
from app.models.category import Category
from sqlalchemy.orm import Session


# Category keywords dictionary
CATEGORY_KEYWORDS = {
    "Продукты": [
        "metro", "перекресток", "пятерочка", "магнит", "дикси", "лента", "ашан",
        "вкусвилл", "азбука вкуса", "перекресток", "продукты", "супермаркет",
        "grocery", "food", "market"
    ],
    "Транспорт": [
        "яндекс.такси", "uber", "bolt", "taxi", "метро", "транспорт", "бензин",
        "азс", "заправка", "parking", "парковка", "каршеринг", "делимобиль"
    ],
    "Рестораны и кафе": [
        "ресторан", "кафе", "mcdonald", "kfc", "burger", "pizza", "суши",
        "доставка еды", "яндекс.еда", "delivery club", "coffee", "starbucks"
    ],
    "Развлечения": [
        "кино", "театр", "музей", "концерт", "steam", "playstation", "xbox",
        "entertainment", "игры", "netflix", "spotify", "youtube premium"
    ],
    "Здоровье": [
        "аптека", "pharmacy", "больница", "клиника", "медицина", "врач",
        "стоматолог", "анализы", "лекарства", "health"
    ],
    "Одежда и обувь": [
        "zara", "h&m", "uniqlo", "adidas", "nike", "ozon", "wildberries",
        "lamoda", "одежда", "обувь", "clothes", "fashion"
    ],
    "Коммунальные услуги": [
        "электроэнергия", "вода", "газ", "интернет", "телефон", "связь",
        "коммунальные", "жкх", "utilities", "мтс", "мегафон", "билайн", "теле2"
    ],
    "Образование": [
        "курсы", "обучение", "университет", "школа", "книги", "литература",
        "education", "coursera", "udemy", "skillbox", "нетология"
    ],
    "Красота": [
        "салон", "парикмахерская", "косметика", "маникюр", "beauty", "sephora",
        "л'этуаль", "рив гош", "makeup"
    ],
    "Путешествия": [
        "авиабилеты", "отель", "hotel", "booking", "airbnb", "туризм", "travel",
        "ржд", "поезд", "туристическая", "тур"
    ]
}


class CategorizationService:
    """Service for categorizing transactions."""
    
    @staticmethod
    def get_or_create_category(db: Session, name: str) -> Category:
        """Get existing category or create new one."""
        category = db.query(Category).filter(Category.name == name).first()
        
        if not category:
            category = Category(
                name=name,
                description=f"Автоматически созданная категория: {name}"
            )
            db.add(category)
            db.commit()
            db.refresh(category)
        
        return category
    
    @staticmethod
    def categorize_transaction(db: Session, description: str, merchant: Optional[str] = None) -> Optional[int]:
        """
        Categorize transaction based on description and merchant.
        Returns category_id or None if no match found.
        """
        # Combine description and merchant for search
        search_text = (description or "").lower()
        if merchant:
            search_text += " " + merchant.lower()
        
        # Check each category
        for category_name, keywords in CATEGORY_KEYWORDS.items():
            for keyword in keywords:
                if keyword.lower() in search_text:
                    category = CategorizationService.get_or_create_category(db, category_name)
                    return category.id
        
        # Default category "Прочее"
        category = CategorizationService.get_or_create_category(db, "Прочее")
        return category.id
    
    @staticmethod
    def recategorize_all_transactions(db: Session):
        """Recategorize all transactions without categories."""
        from app.models.transaction import Transaction
        
        transactions = db.query(Transaction).filter(
            Transaction.category_id == None
        ).all()
        
        for tx in transactions:
            tx.category_id = CategorizationService.categorize_transaction(
                db,
                tx.description,
                tx.merchant
            )
        
        db.commit()

