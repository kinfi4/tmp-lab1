from sqlalchemy import Engine, Table

from repositories.abstract import IRepository
from tables import Base
from repositories import ProductRepository, CustomerRepository, OrderRepository


_PROJECT_REPOSITORIES = [ProductRepository, CustomerRepository, OrderRepository]


def recreate_tables(engine: Engine) -> None:
    with engine.connect() as conn:
        tbl: Table
        for tbl in Base.metadata.sorted_tables:
            conn.execute(tbl.delete())
            conn.commit()

    Base.metadata.create_all(engine)


def export_data(from_engine: Engine, to_engine: Engine) -> None:
    recreate_tables(to_engine)

    for repository in _PROJECT_REPOSITORIES:
        _export_repository(repository(from_engine), repository(to_engine))


def _export_repository(from_repo: IRepository, to_repo: IRepository) -> None:
    records = from_repo.get_all()

    for record in records:
        to_repo.add(record)
