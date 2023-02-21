from abc import ABC
from typing import Any

from sqlalchemy import Engine, update
from sqlalchemy.orm import Session

from src.tables import Base


class IRepository(ABC):
    _table_obj: Base

    def __init__(self, engine: Engine):
        self._engine = engine

    def add(self, data: dict[str, Any]) -> None:
        with Session(self._engine) as session:
            product_obj = self._table_obj(**data)
            session.add(product_obj)
            session.commit()

    def delete(self, _id: int) -> None:
        with Session(self._engine) as session:
            product_to_delete = session.query(self._table_obj).get(_id)
            session.delete(product_to_delete)
            session.commit()

    def update(self, _id: int, data: dict[str, Any]):
        with Session(self._engine) as session:
            session.execute(
                update(self._table_obj)
                .where(self._table_obj.id == _id)
                .values(**data)
            )
            session.commit()

    def get_all(self) -> list[dict[str, Any]]:
        with Session(self._engine) as session:
            return [row.__dict__ for row in session.query(self._table_obj).all()]

    def get_one(self, _id: int) -> dict[str, Any]:
        with Session(self._engine) as session:
            return session.query(self._table_obj).get(_id)
