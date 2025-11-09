"""
MyBank - Lightweight Banking API Sandbox
Provides cards, accounts, transfers, goals for FinanceHub integration
"""
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine, Column, Integer, String, Numeric, DateTime, ForeignKey, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session, sessionmaker, relationship
from pydantic import BaseModel
from datetime import datetime, timedelta
from typing import List, Optional
from decimal import Decimal
import jwt
import uuid

# Database setup
DATABASE_URL = "postgresql://mybank_user:mybank_password@mybank-db:5432/mybank"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# JWT Config
SECRET_KEY = "mybank-secret-key-change-in-production"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")

# Models
class Customer(Base):
    __tablename__ = "customers"
    
    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(String, unique=True, index=True)
    full_name = Column(String)
    email = Column(String, unique=True, index=True)
    phone = Column(String)
    password_hash = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    cards = relationship("Card", back_populates="customer")
    accounts = relationship("Account", back_populates="customer")


class Card(Base):
    __tablename__ = "cards"
    
    id = Column(Integer, primary_key=True, index=True)
    card_id = Column(String, unique=True, index=True)
    customer_id = Column(Integer, ForeignKey("customers.id"))
    card_number = Column(String)  # Masked: **** **** **** 1234
    card_type = Column(String)  # debit, credit
    balance = Column(Numeric(15, 2), default=0)
    credit_limit = Column(Numeric(15, 2), default=0)
    currency = Column(String, default="RUB")
    status = Column(String, default="active")  # active, blocked, closed
    created_at = Column(DateTime, default=datetime.utcnow)
    
    customer = relationship("Customer", back_populates="cards")


class Account(Base):
    __tablename__ = "accounts"
    
    id = Column(Integer, primary_key=True, index=True)
    account_id = Column(String, unique=True, index=True)
    customer_id = Column(Integer, ForeignKey("customers.id"))
    account_number = Column(String, unique=True)
    account_type = Column(String)  # checking, savings, goal
    balance = Column(Numeric(15, 2), default=0)
    currency = Column(String, default="RUB")
    status = Column(String, default="active")
    linked_goal_id = Column(String, nullable=True)  # For goal accounts
    created_at = Column(DateTime, default=datetime.utcnow)
    
    customer = relationship("Customer", back_populates="accounts")
    transactions = relationship("Transaction", back_populates="account")


class Transaction(Base):
    __tablename__ = "transactions"
    
    id = Column(Integer, primary_key=True, index=True)
    transaction_id = Column(String, unique=True, index=True)
    account_id = Column(Integer, ForeignKey("accounts.id"))
    amount = Column(Numeric(15, 2))
    transaction_type = Column(String)  # deposit, withdrawal, transfer
    description = Column(String)
    counterparty = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    account = relationship("Account", back_populates="transactions")


class Goal(Base):
    __tablename__ = "goals"
    
    id = Column(Integer, primary_key=True, index=True)
    goal_id = Column(String, unique=True, index=True)
    customer_id = Column(Integer, ForeignKey("customers.id"))
    account_id = Column(Integer, ForeignKey("accounts.id"))  # Dedicated account for goal
    name = Column(String)
    target_amount = Column(Numeric(15, 2))
    current_amount = Column(Numeric(15, 2), default=0)
    deadline = Column(DateTime, nullable=True)
    status = Column(String, default="active")  # active, completed, cancelled
    created_at = Column(DateTime, default=datetime.utcnow)


# Pydantic Schemas
class CustomerCreate(BaseModel):
    full_name: str
    email: str
    phone: str
    password: str


class CustomerResponse(BaseModel):
    customer_id: str
    full_name: str
    email: str
    phone: str
    
    class Config:
        from_attributes = True


class CardCreate(BaseModel):
    card_type: str = "debit"  # debit or credit
    credit_limit: Optional[Decimal] = 0


class CardResponse(BaseModel):
    card_id: str
    card_number: str
    card_type: str
    balance: Decimal
    credit_limit: Decimal
    currency: str
    status: str
    
    class Config:
        from_attributes = True


class AccountCreate(BaseModel):
    account_type: str = "checking"  # checking, savings, goal
    linked_goal_id: Optional[str] = None


class AccountResponse(BaseModel):
    account_id: str
    account_number: str
    account_type: str
    balance: Decimal
    currency: str
    status: str
    linked_goal_id: Optional[str]
    
    class Config:
        from_attributes = True


class TransferRequest(BaseModel):
    from_account_id: str
    to_account_id: str
    amount: Decimal
    description: Optional[str] = "Transfer"


class GoalCreate(BaseModel):
    name: str
    target_amount: Decimal
    deadline: Optional[datetime] = None


class GoalResponse(BaseModel):
    goal_id: str
    name: str
    target_amount: Decimal
    current_amount: Decimal
    deadline: Optional[datetime]
    status: str
    account_id: str
    
    class Config:
        from_attributes = True


class GoalContribution(BaseModel):
    amount: Decimal
    from_card_id: Optional[str] = None


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


# Create tables
Base.metadata.create_all(bind=engine)

# FastAPI App
app = FastAPI(title="MyBank API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Dependencies
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def get_current_customer(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        customer_id: str = payload.get("sub")
        if customer_id is None:
            raise HTTPException(status_code=401, detail="Invalid token")
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    customer = db.query(Customer).filter(Customer.customer_id == customer_id).first()
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    return customer


# Endpoints
@app.get("/")
def root():
    return {
        "service": "MyBank API",
        "version": "1.0.0",
        "status": "operational"
    }


@app.post("/auth/register", response_model=CustomerResponse)
def register_customer(data: CustomerCreate, db: Session = Depends(get_db)):
    """Register new customer"""
    # Check if exists
    existing = db.query(Customer).filter(Customer.email == data.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    customer = Customer(
        customer_id=f"CUST-{uuid.uuid4().hex[:12].upper()}",
        full_name=data.full_name,
        email=data.email,
        phone=data.phone,
        password_hash=data.password  # In production, hash this!
    )
    db.add(customer)
    db.commit()
    db.refresh(customer)
    
    # Create default checking account
    account = Account(
        account_id=f"ACC-{uuid.uuid4().hex[:12].upper()}",
        customer_id=customer.id,
        account_number=f"40817810{uuid.uuid4().hex[:12]}",
        account_type="checking",
        balance=Decimal("10000.00")  # Starting balance
    )
    db.add(account)
    
    # Create default debit card
    card = Card(
        card_id=f"CARD-{uuid.uuid4().hex[:12].upper()}",
        customer_id=customer.id,
        card_number=f"**** **** **** {uuid.uuid4().hex[:4]}",
        card_type="debit",
        balance=Decimal("10000.00")
    )
    db.add(card)
    db.commit()
    
    return customer


@app.post("/auth/token", response_model=TokenResponse)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """OAuth2 token endpoint"""
    customer = db.query(Customer).filter(Customer.email == form_data.username).first()
    if not customer or customer.password_hash != form_data.password:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    access_token = create_access_token(data={"sub": customer.customer_id})
    return {"access_token": access_token, "token_type": "bearer"}


@app.get("/customers/me", response_model=CustomerResponse)
def get_current_customer_info(current_customer: Customer = Depends(get_current_customer)):
    """Get current customer info"""
    return current_customer


@app.post("/customers/me/cards", response_model=CardResponse)
def create_card(
    data: CardCreate,
    current_customer: Customer = Depends(get_current_customer),
    db: Session = Depends(get_db)
):
    """Issue new card for customer"""
    card = Card(
        card_id=f"CARD-{uuid.uuid4().hex[:12].upper()}",
        customer_id=current_customer.id,
        card_number=f"**** **** **** {uuid.uuid4().hex[:4]}",
        card_type=data.card_type,
        balance=Decimal("0.00"),
        credit_limit=data.credit_limit if data.card_type == "credit" else Decimal("0")
    )
    db.add(card)
    db.commit()
    db.refresh(card)
    return card


@app.get("/customers/me/cards", response_model=List[CardResponse])
def get_cards(current_customer: Customer = Depends(get_current_customer)):
    """Get customer's cards"""
    return current_customer.cards


@app.post("/customers/me/accounts", response_model=AccountResponse)
def create_account(
    data: AccountCreate,
    current_customer: Customer = Depends(get_current_customer),
    db: Session = Depends(get_db)
):
    """Create new account"""
    account = Account(
        account_id=f"ACC-{uuid.uuid4().hex[:12].upper()}",
        customer_id=current_customer.id,
        account_number=f"40817810{uuid.uuid4().hex[:12]}",
        account_type=data.account_type,
        balance=Decimal("0.00"),
        linked_goal_id=data.linked_goal_id
    )
    db.add(account)
    db.commit()
    db.refresh(account)
    return account


@app.get("/customers/me/accounts", response_model=List[AccountResponse])
def get_accounts(current_customer: Customer = Depends(get_current_customer)):
    """Get customer's accounts"""
    return current_customer.accounts


@app.post("/transfers")
def transfer_money(
    data: TransferRequest,
    current_customer: Customer = Depends(get_current_customer),
    db: Session = Depends(get_db)
):
    """Transfer money between accounts"""
    from_account = db.query(Account).filter(
        Account.account_id == data.from_account_id,
        Account.customer_id == current_customer.id
    ).first()
    
    if not from_account:
        raise HTTPException(status_code=404, detail="Source account not found")
    
    if from_account.balance < data.amount:
        raise HTTPException(status_code=400, detail="Insufficient funds")
    
    to_account = db.query(Account).filter(Account.account_id == data.to_account_id).first()
    if not to_account:
        raise HTTPException(status_code=404, detail="Destination account not found")
    
    # Debit from source
    from_account.balance -= data.amount
    tx_debit = Transaction(
        transaction_id=f"TX-{uuid.uuid4().hex[:12].upper()}",
        account_id=from_account.id,
        amount=-data.amount,
        transaction_type="transfer_out",
        description=data.description,
        counterparty=to_account.account_id
    )
    db.add(tx_debit)
    
    # Credit to destination
    to_account.balance += data.amount
    tx_credit = Transaction(
        transaction_id=f"TX-{uuid.uuid4().hex[:12].upper()}",
        account_id=to_account.id,
        amount=data.amount,
        transaction_type="transfer_in",
        description=data.description,
        counterparty=from_account.account_id
    )
    db.add(tx_credit)
    
    db.commit()
    
    return {
        "success": True,
        "from_account": from_account.account_id,
        "to_account": to_account.account_id,
        "amount": float(data.amount),
        "new_balance": float(from_account.balance)
    }


@app.post("/customers/me/goals", response_model=GoalResponse)
def create_goal(
    data: GoalCreate,
    current_customer: Customer = Depends(get_current_customer),
    db: Session = Depends(get_db)
):
    """Create savings goal with dedicated account"""
    # Create dedicated goal account
    account = Account(
        account_id=f"ACC-{uuid.uuid4().hex[:12].upper()}",
        customer_id=current_customer.id,
        account_number=f"40817810{uuid.uuid4().hex[:12]}",
        account_type="goal",
        balance=Decimal("0.00")
    )
    db.add(account)
    db.flush()
    
    goal = Goal(
        goal_id=f"GOAL-{uuid.uuid4().hex[:12].upper()}",
        customer_id=current_customer.id,
        account_id=account.id,
        name=data.name,
        target_amount=data.target_amount,
        current_amount=Decimal("0.00"),
        deadline=data.deadline
    )
    account.linked_goal_id = goal.goal_id
    
    db.add(goal)
    db.commit()
    db.refresh(goal)
    
    return {
        **goal.__dict__,
        "account_id": account.account_id
    }


@app.get("/customers/me/goals", response_model=List[GoalResponse])
def get_goals(
    current_customer: Customer = Depends(get_current_customer),
    db: Session = Depends(get_db)
):
    """Get customer's goals"""
    goals = db.query(Goal).filter(Goal.customer_id == current_customer.id).all()
    result = []
    for goal in goals:
        account = db.query(Account).filter(Account.id == goal.account_id).first()
        result.append({
            **goal.__dict__,
            "account_id": account.account_id if account else None
        })
    return result


@app.post("/customers/me/goals/{goal_id}/contribute")
def contribute_to_goal(
    goal_id: str,
    data: GoalContribution,
    current_customer: Customer = Depends(get_current_customer),
    db: Session = Depends(get_db)
):
    """Contribute to goal"""
    print(f"🔵 MyBank contribute_to_goal: goal_id={goal_id}, amount={data.amount}, from_card_id={data.from_card_id}")
    
    goal = db.query(Goal).filter(
        Goal.goal_id == goal_id,
        Goal.customer_id == current_customer.id
    ).first()
    
    if not goal:
        print(f"❌ Goal not found: goal_id={goal_id}, customer_id={current_customer.id}")
        raise HTTPException(status_code=404, detail="Goal not found")
    
    # Get goal account
    goal_account = db.query(Account).filter(Account.id == goal.account_id).first()
    
    # Get source (card or default account)
    if data.from_card_id:
        print(f"🔍 Looking for card: from_card_id={data.from_card_id}, customer_id={current_customer.id}")
        # Try to find card by card_id
        card = db.query(Card).filter(
            Card.card_id == data.from_card_id,
            Card.customer_id == current_customer.id
        ).first()
        
        # If not found by card_id, try by id (for compatibility)
        if not card:
            try:
                card_int_id = int(data.from_card_id)
                print(f"🔍 Trying by integer ID: {card_int_id}")
                card = db.query(Card).filter(
                    Card.id == card_int_id,
                    Card.customer_id == current_customer.id
                ).first()
            except (ValueError, TypeError):
                print(f"❌ Cannot convert to int: {data.from_card_id}")
                pass
        
        if not card:
            # List all cards for this customer
            all_cards = db.query(Card).filter(Card.customer_id == current_customer.id).all()
            print(f"❌ Card not found! Available cards: {[(c.id, c.card_id) for c in all_cards]}")
            raise HTTPException(status_code=400, detail=f"Card not found: {data.from_card_id}")
        if card.balance < data.amount:
            raise HTTPException(status_code=400, detail=f"Insufficient funds on card. Balance: {card.balance}, Required: {data.amount}")
        card.balance -= data.amount
    else:
        # Use default checking account
        source_account = db.query(Account).filter(
            Account.customer_id == current_customer.id,
            Account.account_type == "checking"
        ).first()
        if not source_account:
            raise HTTPException(status_code=400, detail="No default account found")
        if source_account.balance < data.amount:
            raise HTTPException(status_code=400, detail=f"Insufficient funds. Balance: {source_account.balance}, Required: {data.amount}")
        source_account.balance -= data.amount
    
    # Credit goal account
    goal_account.balance += data.amount
    goal.current_amount += data.amount
    
    # Check if goal completed
    if goal.current_amount >= goal.target_amount:
        goal.status = "completed"
    
    # Create transaction
    tx = Transaction(
        transaction_id=f"TX-{uuid.uuid4().hex[:12].upper()}",
        account_id=goal_account.id,
        amount=data.amount,
        transaction_type="goal_contribution",
        description=f"Contribution to {goal.name}"
    )
    db.add(tx)
    
    db.commit()
    
    return {
        "success": True,
        "goal_id": goal.goal_id,
        "contributed": float(data.amount),
        "current_amount": float(goal.current_amount),
        "target_amount": float(goal.target_amount),
        "progress": float((goal.current_amount / goal.target_amount) * 100) if goal.target_amount > 0 else 0
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)

