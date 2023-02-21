from sqlalchemy import Engine, Table

from src.repositories.abstract import IRepository
from src.tables import Base
from src.repositories import ProductRepository, CustomerRepository, OrderRepository


_PROJECT_REPOSITORIES = [ProductRepository, CustomerRepository, OrderRepository]


def recreate_tables(engine: Engine) -> None:
    with engine.connect() as conn:
        tbl: Table
        for tbl in Base.metadata.sorted_tables:
            try:
                conn.execute(tbl.delete())
                conn.commit()
            except Exception:  # we use Exception class here, because error may differ from one driver to another
                pass

    Base.metadata.create_all(engine)


def export_data(from_engine: Engine, to_engine: Engine) -> None:
    recreate_tables(to_engine)

    for repository in _PROJECT_REPOSITORIES:
        _export_repository(repository(from_engine), repository(to_engine))


def _export_repository(from_repo: IRepository, to_repo: IRepository) -> None:
    records = from_repo.get_all()

    for record in records:
        record.pop("_sa_instance_state")

        to_repo.add(record)
