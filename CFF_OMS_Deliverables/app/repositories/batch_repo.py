from abc import ABC, abstractmethod
from typing import Generic, TypeVar, List, Optional
from sqlalchemy.orm import Session
from app.domain.models import Batch, AuditLog

T = TypeVar("T")

class AbstractRepository(ABC, Generic[T]):
    """Design Pattern 1: Generic Repository Interface decoupling ORM from Business Services."""
    @abstractmethod
    def get_by_id(self, entity_id: int) -> Optional[T]:
        pass

    @abstractmethod
    def add(self, entity: T) -> T:
        pass

class BatchRepository(AbstractRepository[Batch]):
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, entity_id: int) -> Optional[Batch]:
        return self.db.query(Batch).filter(Batch.id == entity_id).first()

    def get_by_canonical_key(self, key: str) -> Optional[Batch]:
        return self.db.query(Batch).filter(Batch.canonical_batch_key == key).first()

    def find_by_legacy_no(self, legacy_no: str) -> List[Batch]:
        return self.db.query(Batch).filter(Batch.legacy_batch_no == legacy_no).all()

    def add(self, batch: Batch) -> Batch:
        self.db.add(batch)
        self.db.flush()
        return batch

    def list_approved_batches(self) -> List[Batch]:
        return self.db.query(Batch).filter(Batch.status == "APPROVED").all()

class AuditRepository:
    def __init__(self, db: Session):
        self.db = db

    def log(self, user_id: int, entity_name: str, entity_id: str, action: str, old_data: dict, new_data: dict):
        entry = AuditLog(
            user_id=user_id,
            entity_name=entity_name,
            entity_id=str(entity_id),
            action=action,
            old_data=old_data,
            new_data=new_data,
        )
        self.db.add(entry)
        self.db.flush()