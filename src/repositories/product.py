from src.repositories.abstract import IRepository
from src.tables import Product


class ProductRepository(IRepository):
    _table_obj = Product
