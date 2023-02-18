from repositories.abstract import IRepository
from src.tables import Order


class OrderRepository(IRepository):
    _table_obj = Order
