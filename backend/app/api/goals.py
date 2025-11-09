"""Goals endpoints."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime
from decimal import Decimal
from app.database import get_db
from app.schemas.goal import GoalCreate, GoalUpdate, GoalResponse
from app.api.dependencies import get_current_user
from app.models.user import User
from app.models.goal import Goal
from app.models.account import Account, AccountType
from app.models.bank_connection import BankProvider
from app.integrations.mybank_client import get_mybank_client, DEFAULT_MYBANK_PASSWORD
import logging
import httpx

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/", response_model=GoalResponse, status_code=status.HTTP_201_CREATED)
async def create_goal(
    goal_data: GoalCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create a new financial goal.
    Автоматически создает выделенный счет в MyBank для хранения денег.
    """
    # Создаем цель в MyBank с выделенным счетом
    mybank = get_mybank_client()
    mybank_goal = None
    
    try:
        # Пытаемся залогиниться в MyBank с дефолтным паролем
        # Если пользователь создал аккаунт в MyBank при регистрации, используем тот же пароль
        # Для упрощения используем email как часть пароля (в production - хранить encrypted)
        try:
            await mybank.login(current_user.email, DEFAULT_MYBANK_PASSWORD)
        except httpx.HTTPStatusError:
            # Если не получилось, возможно пользователь еще не зарегистрирован в MyBank
            # Регистрируем на лету
            try:
                await mybank.register_customer(
                    full_name=current_user.full_name or current_user.email.split('@')[0],
                    email=current_user.email,
                    phone=current_user.phone or "+70000000000",
                    password=DEFAULT_MYBANK_PASSWORD
                )
            except httpx.HTTPStatusError as reg_err:
                if reg_err.response.status_code != 400:
                    raise
            await mybank.login(current_user.email, DEFAULT_MYBANK_PASSWORD)
        
        # Создаем цель с выделенным счетом
        mybank_goal = await mybank.create_goal(
            name=goal_data.name,
            target_amount=goal_data.target_amount,
            deadline=goal_data.target_date  # Используем target_date из схемы
        )
        
        logger.info(f"✅ MyBank goal created: {mybank_goal['goal_id']}, account: {mybank_goal['account_id']}")
        
    except Exception as e:
        logger.error(f"❌ Failed to create MyBank goal: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Не удалось создать счет для цели в MyBank: {str(e)}"
        )
    
    # Создаем Account в нашей БД для отображения MyBank счета цели
    mybank_account = Account(
        bank_connection_id=None,  # Нет подключения, это внутренний счет MyBank
        account_name=f"MyBank Goal: {goal_data.name}",
        account_number=mybank_goal.get('account_number', mybank_goal['account_id']),
        account_type=AccountType.SAVINGS,  # Используем enum напрямую
        balance=Decimal("0"),
        currency="RUB",
        is_active=1,  # INTEGER в БД, не BOOLEAN
        external_account_id=mybank_goal['account_id']
    )
    db.add(mybank_account)
    db.flush()  # Получаем ID счета
    
    # Создаем цель в нашей БД
    goal_dict = goal_data.model_dump(exclude={'current_amount'})
    goal = Goal(
        user_id=current_user.id,
        **goal_dict,
        current_amount=Decimal("0")
    )
    
    db.add(goal)
    db.commit()
    db.refresh(goal)
    db.refresh(mybank_account)
    
    logger.info(f"✅ Goal created: {goal.id} linked to MyBank goal {mybank_goal['goal_id']}, account: {mybank_account.id}")
    
    return goal


@router.get("/", response_model=List[GoalResponse])
def get_goals(
    active_only: bool = False,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all goals for current user."""
    query = db.query(Goal).filter(Goal.user_id == current_user.id)
    
    if active_only:
        query = query.filter(Goal.status == 'IN_PROGRESS')
    
    return query.order_by(Goal.created_at.desc()).all()


@router.get("/{goal_id}", response_model=GoalResponse)
def get_goal(
    goal_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get specific goal."""
    goal = db.query(Goal).filter(
        Goal.id == goal_id,
        Goal.user_id == current_user.id
    ).first()
    
    if not goal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Goal not found"
        )
    
    return goal


@router.put("/{goal_id}", response_model=GoalResponse)
def update_goal(
    goal_id: int,
    goal_data: GoalUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update goal."""
    goal = db.query(Goal).filter(
        Goal.id == goal_id,
        Goal.user_id == current_user.id
    ).first()
    
    if not goal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Goal not found"
        )
    
    for key, value in goal_data.model_dump(exclude_unset=True).items():
        setattr(goal, key, value)
    
    # Auto-complete if target reached
    if goal.current_amount >= goal.target_amount and goal.status != 'COMPLETED':
        goal.status = 'COMPLETED'
    
    db.commit()
    db.refresh(goal)
    
    return goal


@router.delete("/{goal_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_goal(
    goal_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete goal."""
    goal = db.query(Goal).filter(
        Goal.id == goal_id,
        Goal.user_id == current_user.id
    ).first()
    
    if not goal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Goal not found"
        )
    
    db.delete(goal)
    db.commit()


@router.post("/{goal_id}/contribute")
async def contribute_to_goal(
    goal_id: int,
    contribution: dict,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Add contribution to goal.
    Реальный перевод денег на счет цели в MyBank.
    """
    amount = contribution.get("amount")
    from_card_id = contribution.get("from_card_id")
    
    if not amount:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Amount is required"
        )
    
    goal = db.query(Goal).filter(
        Goal.id == goal_id,
        Goal.user_id == current_user.id
    ).first()
    
    if not goal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Goal not found"
        )
    
    # Проверяем что на счету достаточно денег (если указан источник)
    source_account = None
    if from_card_id:
        source_account = db.query(Account).filter(
            Account.id == from_card_id,
            Account.bank_connection.has(user_id=current_user.id)
        ).first()
        
        if not source_account:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Source account not found"
            )
        
        if source_account.balance < Decimal(str(amount)):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Insufficient funds. Balance: {source_account.balance} ₽, Required: {amount} ₽"
            )
        
        # Списываем деньги со счета-источника (симуляция)
        source_account.balance -= Decimal(str(amount))
        db.add(source_account)
    
    # Перевод через MyBank (только если это MyBank счет или без указания источника)
    mybank = get_mybank_client()
    
    try:
        # Логинимся в MyBank
        try:
            await mybank.login(current_user.email, DEFAULT_MYBANK_PASSWORD)
        except httpx.HTTPStatusError:
            # Если пользователь не зарегистрирован, регистрируем
            try:
                await mybank.register_customer(
                    full_name=current_user.full_name or current_user.email.split('@')[0],
                    email=current_user.email,
                    phone=current_user.phone or "+70000000000",
                    password=DEFAULT_MYBANK_PASSWORD
                )
            except httpx.HTTPStatusError as reg_err:
                if reg_err.response.status_code != 400:
                    raise
            await mybank.login(current_user.email, DEFAULT_MYBANK_PASSWORD)
        
        # Получаем список целей чтобы найти нужную
        mybank_goals = await mybank.get_goals()
        mybank_goal = next((g for g in mybank_goals if g['name'] == goal.name), None)
        
        if not mybank_goal:
            raise HTTPException(
                status_code=404,
                detail="MyBank goal not found. Create goal first."
            )
        
        # Вносим деньги в MyBank цель
        # Если источник - MyBank счет, передаем external_account_id, иначе используем дефолтный счет
        mybank_card_id = None
        if source_account and source_account.bank_connection.bank_provider == BankProvider.MYBANK:
            mybank_card_id = source_account.external_account_id
        
        result = await mybank.contribute_to_goal(
            goal_id=mybank_goal['goal_id'],
            amount=Decimal(str(amount)),
            from_card_id=mybank_card_id
        )
        
        logger.info(f"✅ Contributed {amount} to goal {goal.id} from {'account ' + str(from_card_id) if from_card_id else 'default'}: {result}")
        
    except Exception as e:
        logger.error(f"❌ Failed to contribute via MyBank: {e}")
        # Откатываем списание если было
        if source_account:
            source_account.balance += Decimal(str(amount))
            db.add(source_account)
            db.commit()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Не удалось внести деньги: {str(e)}"
        )
    
    # Обновляем в нашей БД
    goal.current_amount += Decimal(str(amount))
    
    # Обновляем баланс MyBank счета цели
    mybank_goal_account = db.query(Account).filter(
        Account.bank_connection_id == None,
        Account.external_account_id == mybank_goal['account_id']
    ).first()
    if mybank_goal_account:
        mybank_goal_account.balance += Decimal(str(amount))
        db.add(mybank_goal_account)
        logger.info(f"✅ Updated MyBank goal account balance: {mybank_goal_account.id}, new balance: {mybank_goal_account.balance}")
    
    # Auto-complete if target reached
    if goal.current_amount >= goal.target_amount:
        goal.status = 'COMPLETED'
    
    # Создаем транзакцию в FinanceHub для отображения в истории (если был указан источник)
    if source_account:
        from app.models.transaction import Transaction, TransactionType
        from app.models.category import Category
        import uuid
        
        # Находим категорию "Сбережения" или создаем
        savings_category = db.query(Category).filter(Category.name == "Сбережения").first()
        if not savings_category:
            savings_category = db.query(Category).first()  # Fallback to any category
        
        transaction = Transaction(
            account_id=source_account.id,
            external_transaction_id=f"GOAL_CONTRIB_{uuid.uuid4().hex[:16].upper()}",
            amount=-Decimal(str(amount)),  # Отрицательная сумма = расход
            description=f"Взнос на цель: {goal.name}",
            transaction_date=datetime.now(),
            category_id=savings_category.id if savings_category else None,
            transaction_type=TransactionType.EXPENSE
        )
        db.add(transaction)
    
    db.commit()
    db.refresh(goal)
    
    return {
        "message": "Деньги успешно внесены на счет цели",
        "goal": goal,
        "progress": float((goal.current_amount / goal.target_amount) * 100) if goal.target_amount > 0 else 0,
        "mybank_transaction": result,
        "transaction_id": transaction.id
    }

