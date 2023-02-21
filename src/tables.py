import sqlalchemy as sq
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class Customer(Base):
    __tablename__ = "customer"

    id = sq.Column(sq.Integer, primary_key=True)
    full_name = sq.Column(sq.String(255), nullable=False)
    email = sq.Column(sq.String(255), nullable=False)


class Product(Base):
    __tablename__ = "product"
    __table_args__ = (
        sq.CheckConstraint("price > 0"),
    )

    id = sq.Column(sq.Integer, primary_key=True)
    name = sq.Column(sq.String(255), nullable=False)
    price = sq.Column(sq.Float, nullable=False)
    description = sq.Column(sq.Text, nullable=True)


class Order(Base):
    __tablename__ = "order"

    id = sq.Column(sq.Integer, primary_key=True)
    qty = sq.Column(sq.Integer, nullable=False)
    customer_id = sq.Column(sq.Integer, sq.ForeignKey("customer.id", ondelete="CASCADE"))
    product_id = sq.Column(sq.Integer, sq.ForeignKey("product.id", ondelete="CASCADE"))
