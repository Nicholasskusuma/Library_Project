from app import db
from datetime import datetime, date


class Book(db.Model):
    __tablename__ = 'books'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    author = db.Column(db.String(100), nullable=False)
    isbn = db.Column(db.String(20), unique=True, nullable=False)
    stock = db.Column(db.Integer, default=1)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    loans = db.relationship('Loan', backref='book', lazy=True)

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'author': self.author,
            'isbn': self.isbn,
            'stock': self.stock,
            'created_at': self.created_at.isoformat()
        }

    @staticmethod
    def validate_isbn(isbn):
        cleaned = isbn.replace('-', '').replace(' ', '')
        return cleaned.isdigit() and len(cleaned) in (10, 13)

    @staticmethod
    def validate_stock(stock):
        return isinstance(stock, int) and stock >= 0


class Member(db.Model):
    __tablename__ = 'members'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    phone = db.Column(db.String(20), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    loans = db.relationship('Loan', backref='member', lazy=True)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'email': self.email,
            'phone': self.phone,
            'created_at': self.created_at.isoformat()
        }

    @staticmethod
    def validate_email(email):
        return '@' in email and '.' in email.split('@')[-1]

    @staticmethod
    def validate_phone(phone):
        if phone is None:
            return True
        cleaned = phone.replace('+', '').replace('-', '').replace(' ', '')
        return cleaned.isdigit() and 8 <= len(cleaned) <= 15


class Loan(db.Model):
    __tablename__ = 'loans'

    id = db.Column(db.Integer, primary_key=True)
    book_id = db.Column(db.Integer, db.ForeignKey('books.id'), nullable=False)
    member_id = db.Column(db.Integer, db.ForeignKey('members.id'), nullable=False)
    loan_date = db.Column(db.Date, default=date.today)
    due_date = db.Column(db.Date, nullable=False)
    return_date = db.Column(db.Date, nullable=True)
    status = db.Column(db.String(20), default='active')  # active, returned, overdue

    def to_dict(self):
        return {
            'id': self.id,
            'book_id': self.book_id,
            'member_id': self.member_id,
            'loan_date': self.loan_date.isoformat(),
            'due_date': self.due_date.isoformat(),
            'return_date': self.return_date.isoformat() if self.return_date else None,
            'status': self.status
        }

    def calculate_fine(self, fine_per_day=1000):
        """Calculate fine for overdue books. Returns fine amount in IDR."""
        if self.return_date:
            ref_date = self.return_date
        else:
            ref_date = date.today()

        if ref_date > self.due_date:
            days_overdue = (ref_date - self.due_date).days
            return days_overdue * fine_per_day
        return 0

    def is_overdue(self):
        ref_date = self.return_date if self.return_date else date.today()
        return ref_date > self.due_date