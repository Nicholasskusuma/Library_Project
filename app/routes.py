from flask import Blueprint, request, jsonify
from app import db
from app.models import Book, Member, Loan
from datetime import date, timedelta

bp = Blueprint('library', __name__, url_prefix='/api')


# ─── BOOKS ───────────────────────────────────────────────────────────────────

@bp.route('/books', methods=['GET'])
def get_books():
    books = Book.query.all()
    return jsonify([b.to_dict() for b in books]), 200


@bp.route('/books/<int:book_id>', methods=['GET'])
def get_book(book_id):
    book = Book.query.get(book_id)
    if not book:
        return jsonify({'error': 'Book not found'}), 404
    return jsonify(book.to_dict()), 200


@bp.route('/books', methods=['POST'])
def add_book():
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data provided'}), 400

    required = ['title', 'author', 'isbn']
    for field in required:
        if not data.get(field):
            return jsonify({'error': f'{field} is required'}), 400

    if not Book.validate_isbn(data['isbn']):
        return jsonify({'error': 'Invalid ISBN format'}), 400

    stock = data.get('stock', 1)
    if not Book.validate_stock(stock):
        return jsonify({'error': 'Stock must be a non-negative integer'}), 400

    if Book.query.filter_by(isbn=data['isbn']).first():
        return jsonify({'error': 'ISBN already exists'}), 409

    book = Book(
        title=data['title'],
        author=data['author'],
        isbn=data['isbn'],
        stock=stock
    )
    db.session.add(book)
    db.session.commit()
    return jsonify(book.to_dict()), 201


@bp.route('/books/<int:book_id>', methods=['PUT'])
def update_book(book_id):
    book = Book.query.get(book_id)
    if not book:
        return jsonify({'error': 'Book not found'}), 404

    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data provided'}), 400

    if 'title' in data:
        book.title = data['title']
    if 'author' in data:
        book.author = data['author']
    if 'stock' in data:
        if not Book.validate_stock(data['stock']):
            return jsonify({'error': 'Stock must be a non-negative integer'}), 400
        book.stock = data['stock']

    db.session.commit()
    return jsonify(book.to_dict()), 200


@bp.route('/books/<int:book_id>', methods=['DELETE'])
def delete_book(book_id):
    book = Book.query.get(book_id)
    if not book:
        return jsonify({'error': 'Book not found'}), 404

    db.session.delete(book)
    db.session.commit()
    return jsonify({'message': 'Book deleted'}), 200


# ─── MEMBERS ─────────────────────────────────────────────────────────────────

@bp.route('/members', methods=['GET'])
def get_members():
    members = Member.query.all()
    return jsonify([m.to_dict() for m in members]), 200


@bp.route('/members/<int:member_id>', methods=['GET'])
def get_member(member_id):
    member = Member.query.get(member_id)
    if not member:
        return jsonify({'error': 'Member not found'}), 404
    return jsonify(member.to_dict()), 200


@bp.route('/members', methods=['POST'])
def add_member():
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data provided'}), 400

    required = ['name', 'email']
    for field in required:
        if not data.get(field):
            return jsonify({'error': f'{field} is required'}), 400

    if not Member.validate_email(data['email']):
        return jsonify({'error': 'Invalid email format'}), 400

    phone = data.get('phone')
    if phone and not Member.validate_phone(phone):
        return jsonify({'error': 'Invalid phone number'}), 400

    if Member.query.filter_by(email=data['email']).first():
        return jsonify({'error': 'Email already registered'}), 409

    member = Member(name=data['name'], email=data['email'], phone=phone)
    db.session.add(member)
    db.session.commit()
    return jsonify(member.to_dict()), 201


@bp.route('/members/<int:member_id>', methods=['DELETE'])
def delete_member(member_id):
    member = Member.query.get(member_id)
    if not member:
        return jsonify({'error': 'Member not found'}), 404

    db.session.delete(member)
    db.session.commit()
    return jsonify({'message': 'Member deleted'}), 200


# ─── LOANS ───────────────────────────────────────────────────────────────────

@bp.route('/loans', methods=['GET'])
def get_loans():
    loans = Loan.query.all()
    return jsonify([l.to_dict() for l in loans]), 200


@bp.route('/loans', methods=['POST'])
def create_loan():
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data provided'}), 400

    required = ['book_id', 'member_id']
    for field in required:
        if not data.get(field):
            return jsonify({'error': f'{field} is required'}), 400

    book = Book.query.get(data['book_id'])
    if not book:
        return jsonify({'error': 'Book not found'}), 404

    if book.stock < 1:
        return jsonify({'error': 'Book out of stock'}), 400

    member = Member.query.get(data['member_id'])
    if not member:
        return jsonify({'error': 'Member not found'}), 404

    loan_days = data.get('loan_days', 7)
    if not isinstance(loan_days, int) or loan_days < 1:
        return jsonify({'error': 'loan_days must be a positive integer'}), 400

    today = date.today()
    loan = Loan(
        book_id=book.id,
        member_id=member.id,
        loan_date=today,
        due_date=today + timedelta(days=loan_days),
        status='active'
    )
    book.stock -= 1
    db.session.add(loan)
    db.session.commit()
    return jsonify(loan.to_dict()), 201


@bp.route('/loans/<int:loan_id>/return', methods=['POST'])
def return_book(loan_id):
    loan = Loan.query.get(loan_id)
    if not loan:
        return jsonify({'error': 'Loan not found'}), 404

    if loan.status == 'returned':
        return jsonify({'error': 'Book already returned'}), 400

    loan.return_date = date.today()
    loan.status = 'returned'
    loan.book.stock += 1
    db.session.commit()

    fine = loan.calculate_fine()
    return jsonify({**loan.to_dict(), 'fine': fine}), 200


@bp.route('/loans/<int:loan_id>/fine', methods=['GET'])
def get_fine(loan_id):
    loan = Loan.query.get(loan_id)
    if not loan:
        return jsonify({'error': 'Loan not found'}), 404

    fine = loan.calculate_fine()
    return jsonify({'loan_id': loan_id, 'fine': fine, 'is_overdue': loan.is_overdue()}), 200