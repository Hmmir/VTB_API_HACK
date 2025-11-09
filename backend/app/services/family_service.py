"""Family Banking Hub core service."""
from datetime import datetime
from typing import List, Optional
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_
import logging

from app.models.family import (
    FamilyGroup,
    FamilyMember,
    FamilyMemberSettings,
    FamilyActivityLog,
    FamilyRole,
    FamilyMemberStatus,
)
from app.models.user import User
from app.schemas.family import (
    FamilyGroupCreate,
    FamilyGroupUpdate,
    FamilyMemberUpdate,
)
from fastapi import HTTPException, status

logger = logging.getLogger(__name__)


class FamilyService:
    """Service for managing family groups and members."""
    
    @staticmethod
    def create_family(
        db: Session,
        user_id: int,
        data: FamilyGroupCreate
    ) -> FamilyGroup:
        """Create a new family group."""
        # Create family group
        family = FamilyGroup(
            name=data.name,
            created_by=user_id
        )
        db.add(family)
        db.flush()
        
        # Add creator as admin member
        creator_member = FamilyMember(
            family_id=family.id,
            user_id=user_id,
            role=FamilyRole.ADMIN,
            status=FamilyMemberStatus.ACTIVE
        )
        db.add(creator_member)
        db.flush()
        
        # Create default settings for creator
        settings = FamilyMemberSettings(
            member_id=creator_member.id,
            show_accounts=True,
            default_visibility="full"
        )
        db.add(settings)
        
        # Log activity
        log = FamilyActivityLog(
            family_id=family.id,
            actor_id=user_id,
            action="created_family",
            target="family_group",
            action_metadata={"family_name": data.name}
        )
        db.add(log)
        
        db.commit()
        db.refresh(family)
        return family
    
    @staticmethod
    def get_family(db: Session, family_id: int) -> Optional[FamilyGroup]:
        """Get family by ID."""
        return db.query(FamilyGroup).filter(FamilyGroup.id == family_id).first()
    
    @staticmethod
    def get_user_families(db: Session, user_id: int) -> List[FamilyGroup]:
        """Get all families where user is a member."""
        return db.query(FamilyGroup).join(
            FamilyMember, FamilyGroup.id == FamilyMember.family_id
        ).filter(
            FamilyMember.user_id == user_id,
            FamilyMember.status == FamilyMemberStatus.ACTIVE
        ).all()
    
    @staticmethod
    def update_family(
        db: Session,
        family_id: int,
        data: FamilyGroupUpdate,
        user_id: int
    ) -> FamilyGroup:
        """Update family group."""
        family = FamilyService.get_family(db, family_id)
        if not family:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Family not found"
            )
        
        # Check if user is admin
        if not FamilyService.is_admin(db, family_id, user_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only admins can update family"
            )
        
        if data.name:
            family.name = data.name
            family.updated_at = datetime.utcnow()
        
        # Log activity
        log = FamilyActivityLog(
            family_id=family_id,
            actor_id=user_id,
            action="updated_family",
            target="family_group",
            action_metadata={"changes": data.dict(exclude_unset=True)}
        )
        db.add(log)
        
        db.commit()
        db.refresh(family)
        return family
    
    @staticmethod
    def delete_family(db: Session, family_id: int, user_id: int) -> None:
        """Delete family group."""
        family = FamilyService.get_family(db, family_id)
        if not family:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Family not found"
            )
        
        # Only creator can delete
        if family.created_by != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only creator can delete family"
            )
        
        db.delete(family)
        db.commit()
    
    @staticmethod
    def regenerate_invite_code(
        db: Session,
        family_id: int,
        user_id: int
    ) -> FamilyGroup:
        """Regenerate invite code for family."""
        import secrets
        import base64
        
        family = FamilyService.get_family(db, family_id)
        if not family:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Family not found"
            )
        
        # Check if user is admin
        if not FamilyService.is_admin(db, family_id, user_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only admins can regenerate invite code"
            )
        
        # Generate new invite code
        family.invite_code = base64.urlsafe_b64encode(secrets.token_bytes(16)).decode('utf-8').rstrip('=')
        family.updated_at = datetime.utcnow()
        
        # Log activity
        log = FamilyActivityLog(
            family_id=family_id,
            actor_id=user_id,
            action="regenerated_invite_code",
            target="family_group",
            action_metadata={}
        )
        db.add(log)
        
        db.commit()
        db.refresh(family)
        return family
    
    @staticmethod
    def join_family(
        db: Session,
        invite_code: str,
        user_id: int
    ) -> FamilyMember:
        """Join family using invite code."""
        # Find family by invite code
        family = db.query(FamilyGroup).filter(
            FamilyGroup.invite_code == invite_code
        ).first()
        
        if not family:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Invalid invite code"
            )
        
        # Check if user is already a member
        existing = db.query(FamilyMember).filter(
            and_(
                FamilyMember.family_id == family.id,
                FamilyMember.user_id == user_id
            )
        ).first()
        
        if existing:
            if existing.status == FamilyMemberStatus.BLOCKED:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You are blocked from this family"
                )
            # Если уже член - просто возвращаем существующего члена
            logger.info(f"User {user_id} already member of family {family.id}, returning existing member")
            return existing
        
        # Create pending member - требует одобрения администратора
        member = FamilyMember(
            family_id=family.id,
            user_id=user_id,
            role=FamilyRole.MEMBER,
            status=FamilyMemberStatus.PENDING  # Ожидает одобрения администратора
        )
        db.add(member)
        db.flush()
        
        # Create default settings
        settings = FamilyMemberSettings(
            member_id=member.id,
            show_accounts=True,
            default_visibility="full"
        )
        db.add(settings)
        
        # Log activity
        log = FamilyActivityLog(
            family_id=family.id,
            actor_id=user_id,
            action="requested_join",
            target="family_member",
            action_metadata={"member_id": member.id}
        )
        db.add(log)
        
        db.commit()
        db.refresh(member)
        return member
    
    @staticmethod
    def approve_member(
        db: Session,
        family_id: int,
        member_id: int,
        admin_user_id: int
    ) -> FamilyMember:
        """Approve pending member."""
        # Check if user is admin
        if not FamilyService.is_admin(db, family_id, admin_user_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only admins can approve members"
            )
        
        member = db.query(FamilyMember).filter(
            and_(
                FamilyMember.id == member_id,
                FamilyMember.family_id == family_id
            )
        ).first()
        
        if not member:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Member not found"
            )
        
        member.status = FamilyMemberStatus.ACTIVE
        
        # Log activity
        log = FamilyActivityLog(
            family_id=family_id,
            actor_id=admin_user_id,
            action="approved_member",
            target="family_member",
            action_metadata={"member_id": member_id, "user_id": member.user_id}
        )
        db.add(log)
        
        db.commit()
        db.refresh(member)
        return member
    
    @staticmethod
    def reject_member(
        db: Session,
        family_id: int,
        member_id: int,
        admin_user_id: int
    ) -> None:
        """Reject and remove pending member."""
        # Check if user is admin
        if not FamilyService.is_admin(db, family_id, admin_user_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only admins can reject members"
            )
        
        member = db.query(FamilyMember).filter(
            and_(
                FamilyMember.id == member_id,
                FamilyMember.family_id == family_id,
                FamilyMember.status == FamilyMemberStatus.PENDING
            )
        ).first()
        
        if not member:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Pending member not found"
            )
        
        # Log activity before deletion
        log = FamilyActivityLog(
            family_id=family_id,
            actor_id=admin_user_id,
            action="rejected_member",
            target="family_member",
            action_metadata={"member_id": member_id, "user_id": member.user_id}
        )
        db.add(log)
        
        # Delete member
        db.delete(member)
        db.commit()
    
    @staticmethod
    def add_shared_accounts(
        db: Session,
        family_id: int,
        member_id: int,
        account_ids: List[int],
        user_id: int
    ) -> None:
        """Add accounts to member's shared accounts (append, not replace)."""
        import logging
        from app.models.family import FamilySharedAccount
        
        logger = logging.getLogger(__name__)
        logger.info(f"🔍 add_shared_accounts called: family_id={family_id}, member_id={member_id}, account_ids={account_ids}")
        
        # Verify member belongs to family and user owns the member record
        member = db.query(FamilyMember).filter(
            and_(
                FamilyMember.id == member_id,
                FamilyMember.family_id == family_id,
                FamilyMember.user_id == user_id
            )
        ).first()
        
        if not member:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Member not found or unauthorized"
            )
        
        # Get existing shared accounts to avoid duplicates
        existing = db.query(FamilySharedAccount).filter(
            and_(
                FamilySharedAccount.family_id == family_id,
                FamilySharedAccount.member_id == member_id
            )
        ).all()
        existing_account_ids = {sa.account_id for sa in existing}
        logger.info(f"📋 Existing shared accounts: {existing_account_ids}")
        
        # Add new shared accounts (skip duplicates)
        added_count = 0
        for account_id in account_ids:
            if account_id not in existing_account_ids:
                shared_account = FamilySharedAccount(
                    family_id=family_id,
                    member_id=member_id,
                    account_id=account_id
                )
                db.add(shared_account)
                added_count += 1
                logger.info(f"➕ Adding shared account: account_id={account_id}")
            else:
                logger.info(f"⏭️  Skipping duplicate account: account_id={account_id}")
        
        # Log activity
        log = FamilyActivityLog(
            family_id=family_id,
            actor_id=user_id,
            action="added_shared_accounts",
            target="family_member",
            action_metadata={"member_id": member_id, "added_count": added_count}
        )
        db.add(log)
        
        db.commit()
        logger.info(f"✅ Successfully added {added_count} new shared accounts for member {member_id}")
    
    @staticmethod
    def set_shared_accounts(
        db: Session,
        family_id: int,
        member_id: int,
        account_ids: List[int],
        user_id: int
    ) -> None:
        """Set which accounts member shares with family (replace all)."""
        import logging
        from app.models.family import FamilySharedAccount
        
        logger = logging.getLogger(__name__)
        logger.info(f"🔍 set_shared_accounts called: family_id={family_id}, member_id={member_id}, account_ids={account_ids}")
        
        # Verify member belongs to family and user owns the member record
        member = db.query(FamilyMember).filter(
            and_(
                FamilyMember.id == member_id,
                FamilyMember.family_id == family_id,
                FamilyMember.user_id == user_id
            )
        ).first()
        
        if not member:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Member not found or unauthorized"
            )
        
        # Delete existing shared accounts for this member
        deleted_count = db.query(FamilySharedAccount).filter(
            and_(
                FamilySharedAccount.family_id == family_id,
                FamilySharedAccount.member_id == member_id
            )
        ).delete()
        logger.info(f"🗑️  Deleted {deleted_count} existing shared accounts for member {member_id}")
        
        # Add new shared accounts
        for account_id in account_ids:
            shared_account = FamilySharedAccount(
                family_id=family_id,
                member_id=member_id,
                account_id=account_id
            )
            db.add(shared_account)
            logger.info(f"➕ Adding shared account: account_id={account_id}")
        
        # Log activity
        log = FamilyActivityLog(
            family_id=family_id,
            actor_id=user_id,
            action="updated_shared_accounts",
            target="family_member",
            action_metadata={"member_id": member_id, "account_count": len(account_ids)}
        )
        db.add(log)
        
        db.commit()
        logger.info(f"✅ Successfully set {len(account_ids)} shared accounts for member {member_id}")
    
    @staticmethod
    def update_member(
        db: Session,
        family_id: int,
        member_id: int,
        data: FamilyMemberUpdate,
        admin_user_id: int
    ) -> FamilyMember:
        """Update family member."""
        # Check if user is admin
        if not FamilyService.is_admin(db, family_id, admin_user_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only admins can update members"
            )
        
        member = db.query(FamilyMember).filter(
            and_(
                FamilyMember.id == member_id,
                FamilyMember.family_id == family_id
            )
        ).first()
        
        if not member:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Member not found"
            )
        
        if data.role:
            member.role = data.role
        if data.status:
            member.status = data.status
        
        # Log activity
        log = FamilyActivityLog(
            family_id=family_id,
            actor_id=admin_user_id,
            action="updated_member",
            target="family_member",
            action_metadata={"member_id": member_id, "changes": data.dict(exclude_unset=True)}
        )
        db.add(log)
        
        db.commit()
        db.refresh(member)
        return member
    
    @staticmethod
    def remove_member(
        db: Session,
        family_id: int,
        member_id: int,
        admin_user_id: int
    ) -> None:
        """Remove member from family."""
        # Check if user is admin
        if not FamilyService.is_admin(db, family_id, admin_user_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only admins can remove members"
            )
        
        member = db.query(FamilyMember).filter(
            and_(
                FamilyMember.id == member_id,
                FamilyMember.family_id == family_id
            )
        ).first()
        
        if not member:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Member not found"
            )
        
        # Cannot remove creator
        family = FamilyService.get_family(db, family_id)
        if member.user_id == family.created_by:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot remove family creator"
            )
        
        # Log activity before deletion
        log = FamilyActivityLog(
            family_id=family_id,
            actor_id=admin_user_id,
            action="removed_member",
            target="family_member",
            action_metadata={"member_id": member_id, "user_id": member.user_id}
        )
        db.add(log)
        
        db.delete(member)
        db.commit()
    
    @staticmethod
    def get_family_members(
        db: Session,
        family_id: int,
        include_pending: bool = False
    ) -> List[FamilyMember]:
        """Get all family members."""
        query = db.query(FamilyMember).filter(FamilyMember.family_id == family_id)
        
        if not include_pending:
            query = query.filter(FamilyMember.status == FamilyMemberStatus.ACTIVE)
        
        return query.options(joinedload(FamilyMember.user)).all()
    
    @staticmethod
    def is_member(db: Session, family_id: int, user_id: int) -> bool:
        """Check if user is a member of the family."""
        member = db.query(FamilyMember).filter(
            and_(
                FamilyMember.family_id == family_id,
                FamilyMember.user_id == user_id,
                FamilyMember.status == FamilyMemberStatus.ACTIVE
            )
        ).first()
        return member is not None
    
    @staticmethod
    def is_admin(db: Session, family_id: int, user_id: int) -> bool:
        """Check if user is an admin of the family."""
        member = db.query(FamilyMember).filter(
            and_(
                FamilyMember.family_id == family_id,
                FamilyMember.user_id == user_id,
                FamilyMember.role == FamilyRole.ADMIN,
                FamilyMember.status == FamilyMemberStatus.ACTIVE
            )
        ).first()
        return member is not None
    
    @staticmethod
    def get_member_by_user(
        db: Session,
        family_id: int,
        user_id: int
    ) -> Optional[FamilyMember]:
        """Get family member by user ID."""
        return db.query(FamilyMember).filter(
            and_(
                FamilyMember.family_id == family_id,
                FamilyMember.user_id == user_id
            )
        ).first()

