from flask import Blueprint, request, jsonify
from flask_login import login_user, login_required, logout_user, current_user
from flask_mail import Message
from .models import db, User, Item, Supplier, Customer, Purchase,Sale, Amount, CreditSale, CreditVoucher, DebitVoucher
from . import mail
from datetime import datetime
from flask_cors import CORS
from sqlalchemy.exc import IntegrityError
import time  # Add this import at the top of your file
import random
import string

main = Blueprint('main', __name__)

CORS(main, supports_credentials=True, origins=["http://localhost:3000"])  # Enable CORS for all domains


@main.route('/', methods=['GET'])
def index():
    return jsonify({'message': 'Welcome to the API!'})


@main.route('/login', methods=['POST'])
def login():
    if current_user.is_authenticated:
        return jsonify({'message': 'You are already logged in!'})

    data = request.get_json()
    email = data.get('email')
    password = data.get('password')

    if not email or not password:
        return jsonify({'error': 'Email or Password missing!'}), 400

    user = User.query.filter_by(email=email).first()

    if not user or not user.check_password(password):
        return jsonify({'error': 'Invalid credentials'}), 401

    if not user.email_verified:
        return jsonify({'error': 'Please verify your email address before logging in.'}), 401

    login_user(user)

    token = user.generate_auth_token()

    user_data = {
        'id': user.id,
        'email': user.email,
        'full_name': user.full_name,
        'role': user.role,
        'email_verified': user.email_verified,
        'is_admin': user.is_admin
    }

    return jsonify({
        'message': 'Login successful!',
        'accessToken': token,
        'userData': user_data
    })


# ---------------------- ITEM CRUD ----------------------

@main.route('/items', methods=['POST'])
# @login_required
def create_item():
    data = request.get_json()
    item = Item(**data)
    db.session.add(item)
    db.session.commit()
    return jsonify({'message': 'Item created', 'item': item.to_dict()}), 201


@main.route('/items', methods=['GET'])
# @login_required
def get_items():
    items = Item.query.all()
    return jsonify([item.to_dict() for item in items])


@main.route('/items/<int:item_id>', methods=['GET'])
# @login_required
def get_item(item_id):
    item = Item.query.get_or_404(item_id)
    return jsonify(item.to_dict())


@main.route('/items/<int:item_id>', methods=['PUT'])
# @login_required
def update_item(item_id):
    item = Item.query.get_or_404(item_id)
    for key, value in request.json.items():
        setattr(item, key, value)
    db.session.commit()
    return jsonify({'message': 'Item updated', 'item': item.to_dict()})


@main.route("/items/<int:item_id>", methods=["DELETE"])
def delete_item(item_id):
    item = Item.query.get(item_id)
    if not item:
        return jsonify({"error": "Item not found"}), 404

    # Check if the item is associated with any purchases
    if Purchase.query.filter_by(item_id=item.id).count() > 0:
        return jsonify({"error": "Cannot delete item, it is associated with purchases"}), 400
    
    # Check if the item is associated with any sales
    if Sale.query.filter_by(item_id=item.id).count() > 0:
        return jsonify({"error": "Cannot delete item, it is associated with sales"}), 400

    try:
        db.session.delete(item)
        db.session.commit()
        return jsonify({"message": "Item deleted successfully"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


# ---------------------- SUPPLIER CRUD ----------------------

@main.route('/suppliers', methods=['POST'])
# @login_required
def create_supplier():
    supplier = Supplier(**request.get_json())
    db.session.add(supplier)
    db.session.commit()
    return jsonify({'message': 'Supplier created', 'supplier': supplier.to_dict()}), 201


@main.route('/suppliers', methods=['GET'])
# @login_required
def get_suppliers():
    suppliers = Supplier.query.all()
    return jsonify([supplier.to_dict() for supplier in suppliers])


@main.route('/suppliers/<int:supplier_id>', methods=['GET'])
# @login_required
def get_supplier(supplier_id):
    supplier = Supplier.query.get_or_404(supplier_id)
    return jsonify(supplier.to_dict())


@main.route('/suppliers/<int:supplier_id>', methods=['PUT'])
# @login_required
def update_supplier(supplier_id):
    supplier = Supplier.query.get_or_404(supplier_id)
    for k, v in request.json.items():
        setattr(supplier, k, v)
    db.session.commit()
    return jsonify({'message': 'Supplier updated', 'supplier': supplier.to_dict()})


@main.route('/suppliers/<int:supplier_id>', methods=['DELETE'])
def delete_supplier(supplier_id):
    supplier = Supplier.query.get_or_404(supplier_id)

    # Check if the supplier is associated with any purchases
    if Purchase.query.filter_by(supplier_id=supplier.id).count() > 0:
        return jsonify({'error': 'Cannot delete supplier, it is associated with one or more purchases.'}), 400

    try:
        db.session.delete(supplier)
        db.session.commit()
        return jsonify({'message': 'Supplier deleted'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

# ---------------------- CUSTOMER CRUD ----------------------

@main.route('/customers', methods=['POST'])
# @login_required
def create_customer():
    customer = Customer(**request.get_json())
    db.session.add(customer)
    db.session.commit()
    return jsonify({'message': 'Customer created', 'customer': customer.to_dict()}), 201


@main.route('/customers', methods=['GET'])
# @login_required
def get_customers():
    customers = Customer.query.all()
    return jsonify([customer.to_dict() for customer in customers])


@main.route('/customers/<int:customer_id>', methods=['GET'])
# @login_required
def get_customer(customer_id):
    customer = Customer.query.get_or_404(customer_id)
    return jsonify(customer.to_dict())


@main.route('/customers/<int:customer_id>', methods=['PUT'])
# @login_required
def update_customer(customer_id):
    customer = Customer.query.get_or_404(customer_id)
    for k, v in request.json.items():
        setattr(customer, k, v)
    db.session.commit()
    return jsonify({'message': 'Customer updated', 'customer': customer.to_dict()})


@main.route('/customers/<int:customer_id>', methods=['DELETE'])
# @login_required
def delete_customer(customer_id):
    customer = Customer.query.get_or_404(customer_id)

    # Check if the customer is associated with any sales
    sale_count = Sale.query.filter_by(customer_id=customer.id).count()

    if sale_count > 0:
        return jsonify({
            'error': 'Cannot delete customer, they are associated with purchases or sales'
        }), 400

    try:
        db.session.delete(customer)
        db.session.commit()
        return jsonify({'message': 'Customer deleted'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


def generate_bill_no(item_name):
    """ Generate a unique bill number by appending a timestamp or random string to avoid collisions. """
    import random
    import string
    timestamp = str(int(time.time()))
    random_suffix = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
    return f"{item_name[:3].upper()}_{timestamp}_{random_suffix}"


@main.route('/purchases', methods=['POST'])
def create_purchase():
    data = request.get_json()

    required_keys = ['purchase_no', 'supplier_name', 'items']
    if not all(key in data for key in required_keys):
        return jsonify({'error': 'Missing required fields: purchase_no, supplier_name, items'}), 400

    supplier = Supplier.query.filter_by(name=data['supplier_name']).first()
    if not supplier:
        return jsonify({'error': 'Invalid supplier name'}), 400

    purchases = []

    for item_data in data['items']:
        if not all(k in item_data for k in ['item_name', 'qty']):
            return jsonify({'error': 'Each item must have item_name and qty'}), 400

        item = Item.query.filter_by(item_name=item_data['item_name']).first()
        if not item:
            return jsonify({'error': f"Invalid item: {item_data['item_name']}"}), 400

        try:
            qty = float(item_data['qty'])
            purchase_rate = float(item_data.get('purchaseRate', item.purchase_rate))
            sale_rate = float(item_data.get('saleRate', item.sale_rate))
        except ValueError:
            return jsonify({'error': 'qty, purchaseRate, and saleRate must be numeric'}), 400

        # Calculate net amount from qty and purchase_rate
        net_amount = qty * purchase_rate

        discount_percent = float(data.get('discount_percentage', 0.0))
        payment = float(data.get('payment', 0.0))
        discount = net_amount * (discount_percent / 100)
        balance = net_amount - discount - payment

        # Generate a unique bill_no
        bill_no = generate_bill_no(item.item_name)
        
        # Check if the generated bill_no already exists
        existing_purchase = Purchase.query.filter_by(bill_no=bill_no).first()
        if existing_purchase:
            # If the bill_no already exists, regenerate the bill_no
            bill_no = generate_bill_no(item.item_name)

        purchase = Purchase(
            purchase_no=data['purchase_no'],
            bill_no=bill_no,
            supplier_id=supplier.id,
            item_id=item.id,
            qty=qty,
            purchase_rate=purchase_rate,
            sale_rate=sale_rate,
            net_amount=net_amount,
            description=item_data.get('description', ''),
            discount_percent=discount_percent,
            discount=discount,
            payment=payment,
            balance=balance
        )

        db.session.add(purchase)
        purchases.append({'item_name': item.item_name, 'bill_no': bill_no})

    db.session.commit()

    return jsonify({'message': 'Purchase(s) added', 'purchases': purchases})





@main.route('/purchases', methods=['GET'])
def get_all_purchases():
    purchases = Purchase.query.all()
    result = []
    for p in purchases:
        # Check if the supplier exists
        supplier_name = p.supplier.name if p.supplier else 'No Supplier'
        result.append({
            'id': p.id,
            'purchase_no': p.purchase_no,
            'bill_no': p.bill_no,
            'date': p.date.isoformat(),
            'supplier': supplier_name,
            'item': p.item.item_name,
            'qty': p.qty,
            'purchase_rate': p.purchase_rate,
            'sale_rate': p.sale_rate,
            'net_amount': p.net_amount,
            'description': p.description,
            'discount_percent': p.discount_percent,
            'discount': p.discount,
            'payment': p.payment,
            'balance': p.balance
        })
    return jsonify(result)


@main.route('/purchases/<int:id>', methods=['GET'])
def get_purchase(id):
    purchase = Purchase.query.get_or_404(id)

    # All line items with the same purchase_no
    related_items = Purchase.query.filter_by(purchase_no=purchase.purchase_no).all()

    if not related_items:
        return jsonify({'error': 'No items found for this purchase number'}), 404

    supplier_name = purchase.supplier.name if purchase.supplier else 'Unknown Supplier'

    items_details = []
    for related_item in related_items:
        item = related_item.item
        if not item:
            continue

        items_details.append({
            'item_id': item.id,
            'item_name': item.name if hasattr(item, 'name') else 'Unknown Item',
            'qty': related_item.qty,
            'purchase_rate': related_item.purchase_rate,
            'sale_rate': related_item.sale_rate,
            'net_amount': related_item.net_amount,
            'description': related_item.description or ''
        })

    return jsonify({
        'purchase_id': purchase.id,
        'purchase_no': purchase.purchase_no,
        'bill_no': purchase.bill_no,
        'date': purchase.date.isoformat(),
        'supplier_name': supplier_name,
        'net_amount': purchase.net_amount,
        'description': purchase.description,
        'discount_percent': purchase.discount_percent,
        'discount': purchase.discount,
        'payment': purchase.payment,
        'balance': purchase.balance,
        'items': items_details
    })

@main.route('/purchases', methods=['DELETE'])
# @login_required
def delete_purchase(id):
    purchase = Purchase.query.get_or_404(id)
    db.session.delete(purchase)
    db.session.commit()
    return jsonify({'message': 'Purchase deleted'})



@main.route('/create-sale', methods=['POST'])
def create_sale():
    data = request.json
    customer = Customer.query.get(data['customer_id'])
    if not customer:
        return jsonify({"error": "Customer not found"}), 404

    # Initialize total quantities and amounts
    total_qty = 0
    total_net_amount = 0
    total_cash = data['cash']
    total_balance = 0

    sale_records = []

    # Iterate over each item in the request
    for item_data in data['items']:
        item = Item.query.get(item_data['item_id'])
        if not item:
            return jsonify({"error": f"Item with ID {item_data['item_id']} not found"}), 404

        previous = item_data['previous_reading']
        current = item_data['current_reading']
        qty = current - previous
        net_amount = qty * item.sale_rate
        balance = net_amount - data['cash']  # Remaining balance after cash is paid

        # Create a Sale entry for each item
        sale = Sale(
            slip_no=data['slip_no'],
            salesperson=data['salesperson'],
            cashier=data['cashier'],
            customer_id=customer.id,
            item_id=item.id,
            previous_reading=previous,
            current_reading=current,
            qty=qty,
            unit_rate=item.sale_rate,
            net_amount=net_amount,
            cash=data['cash'],
            balance=balance
        )
        db.session.add(sale)
        sale_records.append(sale)

        # Accumulate totals
        total_qty += qty
        total_net_amount += net_amount
        total_balance += balance

    # Commit all the Sale records
    db.session.commit()

    # Create Amount entry for tracking payment method (assuming only one amount entry for the sale)
    amount = Amount(
        sale_id=sale_records[0].id,  # Just taking the first sale's ID for the amount entry
        is_online=data.get('is_online', False),
        cash_in_hand=total_cash if not data.get('is_online') else None,
        bank_name=data.get('bank_name'),
        account_number=data.get('account_number')
    )
    db.session.add(amount)
    db.session.commit()

    # If the total net amount is greater than cash, add a credit sale entry
    if total_net_amount > total_cash:
        credit_amount = total_net_amount - total_cash
        credit_description = data.get('credit_description', 'Credit added for sale')

        credit_sale = CreditSale(
            sale_id=sale_records[0].id,  # Just taking the first sale's ID for the credit sale entry
            customer_id=customer.id,
            debit=credit_amount,
            description=credit_description
        )
        db.session.add(credit_sale)
        db.session.commit()

    return jsonify({"message": "Sale created successfully."})


@main.route('/sales', methods=['GET'])
def get_all_sales():
    sales = Sale.query.all()
    sales_data = [sale.to_dict() for sale in sales]
    return jsonify(sales_data)


@main.route('/sales/<int:sale_id>', methods=['GET'])
def get_sale(sale_id):
    sale = Sale.query.get(sale_id)
    if not sale:
        return jsonify({"error": "Sale not found"}), 404

    slip_no = sale.slip_no
    # Fetch all sales with the same slip_no
    sales = Sale.query.filter_by(slip_no=slip_no).all()
    
    # Fetch the amounts for the sales with the same slip_no
    amounts = Amount.query.join(Sale).filter(Sale.slip_no == slip_no).all()

    # Calculate totals
    total_qty = sum(s.qty for s in sales)
    total_net_amount = sum(s.net_amount for s in sales)
    total_balance = total_net_amount - sale.cash  # Assuming 'cash' means total paid so far

    # Prepare the response
    response = {
        "slip_no": slip_no,
        "salesperson": sales[0].salesperson,
        "cashier": sales[0].cashier,
        "customer_id": sales[0].customer_id,
        "cash": sales[0].cash,
        "date": sale.date,  # Assuming you have a 'date' field in your Sale model
        "items": [
            {
                "item_id": s.item_id,
                "previous_reading": s.previous_reading,
                "current_reading": s.current_reading,
                "qty": s.qty,
                "unit_rate": s.unit_rate,
                "net_amount": s.net_amount,
            }
            for s in sales
        ],
        "amounts": [
            {
                "is_online": a.is_online,
                "cash_in_hand": a.cash_in_hand,
                "bank_name": a.bank_name,
                "account_number": a.account_number,
                "timestamp": a.timestamp
            }
            for a in amounts
        ],
        "total_qty": total_qty,
        "total_net_amount": total_net_amount,
        "total_balance": total_balance
    }

    return jsonify(response)



@main.route('/sales/<int:sale_id>', methods=['DELETE'])
def delete_sale(sale_id):
    sale = Sale.query.get(sale_id)
    if not sale:
        return jsonify({"error": "Sale not found"}), 404

    # Optional: Delete related Amount and CreditSale records if needed
    Amount.query.filter_by(sale_id=sale.id).delete()
    CreditSale.query.filter_by(sale_id=sale.id).delete()

    db.session.delete(sale)
    db.session.commit()
    return jsonify({"message": "Sale deleted successfully."})





@main.route("/vouchers", methods=["POST"])
def create_voucher():
    data = request.json

    voucher_no = data["voucher_no"]
    cr_account = data["cr_account"]
    description = data.get("description")

    accounts = data.get("accounts", [])

    if not accounts:
        return jsonify({"error": "Accounts list is required."}), 400

    vouchers = []
    for acc in accounts:
        voucher = CreditVoucher(
            voucher_no=voucher_no,
            cr_account=cr_account,
            account_code=acc["account_code"],
            account_name=acc["account_name"],
            debit=acc["debit"],
            description=description
        )
        db.session.add(voucher)
        vouchers.append(voucher)

    db.session.commit()
    return jsonify([v.to_dict() for v in vouchers]), 201


@main.route("/vouchers", methods=["GET"])
def get_vouchers():
    vouchers = CreditVoucher.query.all()
    return jsonify([v.to_dict() for v in vouchers])


@main.route('/vouchers/<int:voucher_id>', methods=['GET'])
def get_voucher(voucher_id):
    voucher = CreditVoucher.query.get(voucher_id)
    if not voucher:
        return jsonify({"error": "Voucher not found"}), 404

    # Fetch associated accounts using the voucher_no or another relationship method
    accounts = CreditVoucher.query.filter_by(voucher_no=voucher.voucher_no).all()

    # Calculate totals (e.g., total debit from account details)
    total_debit = sum(acc.debit for acc in accounts)

    # Prepare the response
    response = {
        "voucher_no": voucher.voucher_no,
        "cr_account": voucher.cr_account,
        "description": voucher.description,
        "date": voucher.date.isoformat(),  # Assuming you have a 'date' field in your CreditVoucher model
        "accounts": [
            {
                "account_code": acc.account_code,
                "account_name": acc.account_name,
                "debit": acc.debit,
                "date": acc.date.isoformat(),
            }
            for acc in accounts
        ],
        "total_debit": total_debit
    }

    return jsonify(response)


# @main.route("/vouchers/<int:voucher_id>", methods=["PUT"])
# def update_voucher(voucher_id):
#     data = request.json

#     # Get the original voucher to find the voucher_no
#     original_voucher = CreditVoucher.query.get(voucher_id)
#     if not original_voucher:
#         return jsonify({"error": "Voucher not found"}), 404

#     voucher_no = original_voucher.voucher_no

#     # Delete all vouchers with this voucher_no
#     CreditVoucher.query.filter_by(voucher_no=voucher_no).delete()

#     cr_account = data["cr_account"]
#     description = data.get("description")
#     accounts = data.get("accounts", [])

#     if not accounts:
#         return jsonify({"error": "Accounts list is required."}), 400

#     updated_vouchers = []
#     for acc in accounts:
#         voucher = CreditVoucher(
#             voucher_no=voucher_no,
#             cr_account=cr_account,
#             account_code=acc["account_code"],
#             account_name=acc["account_name"],
#             debit=acc["debit"],
#             description=description
#         )
#         db.session.add(voucher)
#         updated_vouchers.append(voucher)

#     db.session.commit()
#     return jsonify([v.to_dict() for v in updated_vouchers])


@main.route("/vouchers/<int:voucher_id>", methods=["DELETE"])
def delete_voucher(voucher_id):
    voucher = CreditVoucher.query.get(voucher_id)
    if not voucher:
        return jsonify({"error": "Voucher not found"}), 404
    db.session.delete(voucher)
    db.session.commit()
    return jsonify({"message": "Voucher deleted"})



# Create a new Debit Voucher
@main.route("/debit_vouchers", methods=["POST"])
def create_debit_voucher():
    data = request.json

    voucher_no = data["voucher_no"]
    db_account = data["db_account"]
    description = data.get("description")

    accounts = data.get("accounts", [])

    if not accounts:
        return jsonify({"error": "Accounts list is required."}), 400

    vouchers = []
    for acc in accounts:
        voucher = DebitVoucher(
            voucher_no=voucher_no,
            db_account=db_account,
            account_code=acc["account_code"],
            account_name=acc["account_name"],
            credit=acc["credit"],
            description=description
        )
        db.session.add(voucher)
        vouchers.append(voucher)

    db.session.commit()
    return jsonify([v.to_dict() for v in vouchers]), 201



# Get all Debit Vouchers
@main.route("/debit_vouchers", methods=["GET"])
def get_debit_vouchers():
    debit_vouchers = DebitVoucher.query.all()
    return jsonify([v.to_dict() for v in debit_vouchers])

# Get a single Debit Voucher by ID
@main.route("/debit_vouchers/<int:voucher_id>", methods=["GET"])
def get_debit_voucher(voucher_id):
    voucher = DebitVoucher.query.get(voucher_id)
    if not voucher:
        return jsonify({"error": "Voucher not found"}), 404

    # Fetch associated accounts using the voucher_no or another relationship method
    accounts = DebitVoucher.query.filter_by(voucher_no=voucher.voucher_no).all()

    # Calculate totals (e.g., total debit from account details)
    total_credit = sum(acc.credit for acc in accounts)

    # Prepare the response
    response = {
        "voucher_no": voucher.voucher_no,
        "db_account": voucher.db_account,
        "description": voucher.description,
        "date": voucher.date.isoformat(),  # Assuming you have a 'date' field in your CreditVoucher model
        "accounts": [
            {
                "account_code": acc.account_code,
                "account_name": acc.account_name,
                "credit": acc.credit,
                "date": acc.date.isoformat(),
            }
            for acc in accounts
        ],
        "total_credit": total_credit
    }

    return jsonify(response)


# Update a Debit Voucher
# @main.route("/debit_vouchers/<int:voucher_id>", methods=["PUT"])
# def update_debit_voucher(voucher_id):
#     data = request.json
#     debit_voucher = DebitVoucher.query.get(voucher_id)
#     if not debit_voucher:
#         return jsonify({"error": "Debit Voucher not found"}), 404

#     # Update fields
#     for field in ["db_account", "account_code", "account_name", "credit", "description"]:
#         if field in data:
#             setattr(debit_voucher, field, data[field])
    
#     db.session.commit()
#     return jsonify(debit_voucher.to_dict())

# Delete a Debit Voucher
@main.route("/debit_vouchers/<int:voucher_id>", methods=["DELETE"])
def delete_debit_voucher(voucher_id):
    debit_voucher = DebitVoucher.query.get(voucher_id)
    if not debit_voucher:
        return jsonify({"error": "Debit Voucher not found"}), 404
    db.session.delete(debit_voucher)
    db.session.commit()
    return jsonify({"message": "Debit Voucher deleted"})


@main.route('/logout', methods=['POST'])
@login_required
def logout():
    logout_user()
    return jsonify({'message': 'Logout successful!'})












# @main.route('/register', methods=['POST'])
# def register():
#     data = request.get_json()

#     email = data.get('email')
#     password = data.get('password')
#     full_name = data.get('full_name')
#     role = data.get('role')
#     company_size = data.get('company_size')
#     token = data.get('token')

#     # Validation
#     if not email or not password or not full_name or not role or not company_size:
#         return jsonify({'error': 'All fields are required!'}), 400

#     if not email.endswith('@thehexaa.com'):
#         return jsonify({'error': 'Please enter a valid @thehexaa.com email address!'}), 400

#     existing_user = User.query.filter_by(email=email).first()
#     if existing_user:
#         return jsonify({'error': 'User with this email already exists.'}), 400

#     # Create new user
#     user = User(
#         email=email,
#         full_name=full_name,
#         role=role,
#         company_size=company_size
#     )
#     user.set_password(password)
#     db.session.add(user)
#     db.session.commit()

#     if token:
#         try:
#             s = Serializer(current_app.config['SECRET_KEY'])
#             data = s.loads(token)
#             channel_id = data['channel_id']
#             invited_email = data['email']
#             if email == invited_email:
#                 channel = Channel.query.get(channel_id)
#                 if channel:
#                     channel.users.append(user)
#                     db.session.commit()
#         except (BadSignature, SignatureExpired):
#             return jsonify({'error': 'Invalid or expired invitation token.'}), 400

#     send_verification_email(user)

#     return jsonify({'message': 'Registration successful! A confirmation email has been sent.'})

# @main.route('/confirm_email/<token>', methods=['GET'])
# def confirm_email(token):
#     user = User.verify_verification_token(token)
#     if user is None:
#         return jsonify({'error': 'The confirmation link is invalid or has expired.'}), 400

#     user.email_verified = True
#     db.session.commit()
#     return jsonify({'message': 'Email verified successfully!'})




# def send_verification_email(user):
#     token = user.generate_verification_token()
#     verification_link = f"http://127.0.0.1:5000/confirm_email/{token}"  # Replace with your actual confirmation URL
#     msg = Message('Confirm Your Email Address', sender=current_app.config['MAIL_USERNAME'], recipients=[user.email])
#     msg.body = f'Please click the following link to verify your email address: {verification_link}'
#     mail.send(msg)








