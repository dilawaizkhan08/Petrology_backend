from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from . import db, login_manager
from itsdangerous import URLSafeTimedSerializer as Serializer, BadSignature, SignatureExpired
from flask import current_app
from datetime import datetime,timedelta
from sqlalchemy import Enum

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(128), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    full_name = db.Column(db.String(128), nullable=False)
    role = db.Column(db.String(128), nullable=False)
    email_verified = db.Column(db.Boolean, default=False)
    is_admin = db.Column(db.Boolean, default=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def generate_verification_token(self, expiration=3600):
        s = Serializer(current_app.config['SECRET_KEY'])
        return s.dumps({'user_id': self.id})

    @staticmethod
    def verify_verification_token(token):
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token, max_age=3600)
        except SignatureExpired:
            return None
        except BadSignature:
            return None
        return User.query.get(data['user_id'])

    @property
    def is_active(self):
        return self.email_verified

    def get_id(self):
        return str(self.id)
    
    # New method to generate auth token (JWT)
    def generate_auth_token(self, expiration=3600):
        s = Serializer(current_app.config['SECRET_KEY'], salt='auth')
        exp = datetime.utcnow() + timedelta(seconds=expiration)
        return s.dumps({'user_id': self.id, 'exp': exp.isoformat()})

    

class Item(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    type = db.Column(db.String(50))
    item_name = db.Column(db.String(100), nullable=False)
    item_code = db.Column(db.String(50), unique=True, nullable=False)
    minimum_level = db.Column(db.Integer)
    qty_per_packet = db.Column(db.Integer)
    purchase_rate = db.Column(db.Float)
    sale_rate = db.Column(db.Float)
    wholesale_rate = db.Column(db.Float)
    sale_discount_percent = db.Column(db.Float)
    opening_stock = db.Column(db.Float)
    unit = db.Column(db.String(20))

    purchases = db.relationship('Purchase', backref='item', passive_deletes=True)

    def to_dict(self):
        return {col.name: getattr(self, col.name) for col in self.__table__.columns}


class Supplier(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    address = db.Column(db.String(200))
    tel = db.Column(db.String(20))
    mobile = db.Column(db.String(20))
    email = db.Column(db.String(100))
    cash_balance = db.Column(db.Float)
    cash_balance_type = db.Column(db.String(10), nullable=False)

    purchases = db.relationship('Purchase', backref='supplier', passive_deletes=True)

    def to_dict(self):
        return {col.name: getattr(self, col.name) for col in self.__table__.columns}


class Customer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    address = db.Column(db.String(200))
    tel = db.Column(db.String(20))
    mobile = db.Column(db.String(20))
    email = db.Column(db.String(100))
    cash_balance = db.Column(db.Float)  # +ve for receivable, -ve for payable
    cash_balance_type = db.Column(db.String(10), nullable=False)  # 'Receivable' or 'Payable'

    def to_dict(self):
        return {col.name: getattr(self, col.name) for col in self.__table__.columns}
    
class Purchase(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    purchase_no = db.Column(db.String(50), nullable=False)
    bill_no = db.Column(db.String(100), unique=True)
    date = db.Column(db.DateTime, default=datetime.utcnow)

    supplier_id = db.Column(db.Integer, db.ForeignKey('supplier.id', ondelete='SET NULL'), nullable=True)
    item_id = db.Column(db.Integer, db.ForeignKey('item.id', ondelete='SET NULL'), nullable=True)

    qty = db.Column(db.Float, nullable=False)
    purchase_rate = db.Column(db.Float)
    sale_rate = db.Column(db.Float)
    net_amount = db.Column(db.Float)
    description = db.Column(db.Text)
    discount_percent = db.Column(db.Float, default=0.0)
    discount = db.Column(db.Float)
    payment = db.Column(db.Float, default=0.0)
    balance = db.Column(db.Float)

    def to_dict(self):
        return {col.name: getattr(self, col.name) for col in self.__table__.columns}



class Sale(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    slip_no = db.Column(db.String(20), nullable=False)
    date = db.Column(db.DateTime, default=datetime.utcnow)

    salesperson = db.Column(db.String(100), nullable=False)
    cashier = db.Column(db.String(100), nullable=False)

    customer_id = db.Column(db.Integer, db.ForeignKey('customer.id'), nullable=False)

    item_id = db.Column(db.Integer, db.ForeignKey('item.id'), nullable=False)
    previous_reading = db.Column(db.Float, nullable=False)
    current_reading = db.Column(db.Float, nullable=False)

    qty = db.Column(db.Float, nullable=False)
    unit_rate = db.Column(db.Float, nullable=False)
    net_amount = db.Column(db.Float, nullable=False)

    cash = db.Column(db.Float, nullable=False)
    balance = db.Column(db.Float, nullable=False)

    def to_dict(self):
        return {
            "id": self.id,
            "slip_no": self.slip_no,
            "salesperson": self.salesperson,
            "cashier": self.cashier,
            "customer_id": self.customer_id,
            "item_id": self.item_id,
            "previous_reading": self.previous_reading,
            "current_reading": self.current_reading,
            "qty": self.qty,
            "unit_rate": self.unit_rate,
            "net_amount": self.net_amount,
            "cash": self.cash,
            "balance": self.balance
        }


class Amount(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sale_id = db.Column(db.Integer, db.ForeignKey('sale.id'), nullable=False)
    is_online = db.Column(db.Boolean, default=False)
    cash_in_hand = db.Column(db.Float)
    bank_name = db.Column(db.String(100))
    account_number = db.Column(db.String(100))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

class CreditSale(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sale_id = db.Column(db.Integer, db.ForeignKey('sale.id'), nullable=False)
    customer_id = db.Column(db.Integer, db.ForeignKey('customer.id'), nullable=False)

    debit = db.Column(db.Float, nullable=False)
    description = db.Column(db.String(255))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    customer = db.relationship("Customer", backref="credit_sales")
    sale = db.relationship("Sale", backref="credit_sales")

class CreditVoucher(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    voucher_no = db.Column(db.String(50), nullable=False)
    date = db.Column(db.DateTime, default=datetime.utcnow)
    cr_account = db.Column(db.String(50), nullable=False)  # "online" or "in hand"
    account_code = db.Column(db.String(50), nullable=False)
    account_name = db.Column(db.String(100), nullable=False)
    debit = db.Column(db.Float, nullable=False)
    description = db.Column(db.String(255), nullable=True)

    def to_dict(self):
        return {
            "id": self.id,
            "voucher_no": self.voucher_no,
            "date": self.date.isoformat(),
            "cr_account": self.cr_account,
            "account_code": self.account_code,
            "account_name": self.account_name,
            "debit": self.debit,
            "description": self.description,
        }
    

class DebitVoucher(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    voucher_no = db.Column(db.String(50), nullable=False)
    date = db.Column(db.DateTime, default=datetime.utcnow)
    db_account = db.Column(db.String(50), nullable=False)  # "online" or "in hand"
    account_code = db.Column(db.String(50), nullable=False)
    account_name = db.Column(db.String(100), nullable=False)
    credit = db.Column(db.Float, nullable=False)
    description = db.Column(db.String(255), nullable=True)

    def to_dict(self):
        return {
            "id": self.id,
            "voucher_no": self.voucher_no,
            "date": self.date.isoformat(),
            "db_account": self.db_account,
            "account_code": self.account_code,
            "account_name": self.account_name,
            "credit": self.credit,
            "description": self.description,
        }
    

