from abc import ABC
from typing import Any

from sqlalchemy import Engine, update
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError, DataError

from src.exceptions import InfrastructureException, InvalidDataError, RelationError
from src.tables import Base


class IRepository(ABC):
    _table_obj: Base

    def __init__(self, engine: Engine):
        self._engine = engine

    def add(self, data: dict[str, Any]) -> None:
        with Session(self._engine) as session:
            product_obj = self._table_obj(**data)

            try:
                session.add(product_obj)
                session.commit()
            except IntegrityError:
                raise RelationError(f"Impossible to add this {self._table_obj.__name__}")
            except DataError:
                raise InvalidDataError("Invalid input")
            except Exception as err:
                raise InfrastructureException(f"Something went wrong with {err.__class__.__name__}: {str(err)}")

    def delete(self, _id: int) -> None:
        with Session(self._engine) as session:
            product_to_delete = session.query(self._table_obj).get(_id)

            try:
                session.delete(product_to_delete)
                session.commit()
            except Exception as err:
                raise InfrastructureException(f"Something went wrong with {err.__class__.__name__}: {str(err)}")

    def update(self, _id: int, data: dict[str, Any]):
        with Session(self._engine) as session:
            try:
                session.execute(
                    update(self._table_obj).where(self._table_obj.id == _id).values(**data)
                )
                session.commit()
            except IntegrityError:
                raise RelationError(f"Impossible to add this {self._table_obj.__name__}")
            except DataError:
                raise InvalidDataError("Invalid input")
            except Exception as err:
                raise InfrastructureException(f"Something went wrong with {err.__class__.__name__}: {str(err)}")

    def get_all(self) -> list[dict[str, Any]]:
        with Session(self._engine) as session:
            try:
                return [row.__dict__ for row in session.query(self._table_obj).all()]
            except Exception as err:
                raise InfrastructureException(f"Something went wrong with {err.__class__.__name__}: {str(err)}")

    def get_one(self, _id: int) -> dict[str, Any]:
        with Session(self._engine) as session:
            try:
                return session.query(self._table_obj).get(_id)
            except Exception as err:
                raise InfrastructureException(f"Something went wrong with {err.__class__.__name__}: {str(err)}")
