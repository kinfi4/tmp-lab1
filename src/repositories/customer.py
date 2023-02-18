from repositories.abstract import IRepository
from src.tables import Customer


class CustomerRepository(IRepository):
    _table_obj = Customer
