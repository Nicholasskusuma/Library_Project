"""
Unit Tests Library Management System
Menguji logika bisnis, validasi input, dan kalkulasi denda.
"""
import pytest
from datetime import date, timedelta
from app import create_app, db
from app.models import Book, Member, Loan


# ─── FIXTURES ────── persiapan data sebelum test jalan

@pytest.fixture
def app():
    application = create_app({
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
    })
    with application.app_context():
        db.create_all()
        yield application
        db.session.remove()
        db.drop_all()


@pytest.fixture
def sample_book(app):
    with app.app_context():
        book = Book(title='Clean Code', author='Robert Martin', isbn='9780132350884', stock=3)
        db.session.add(book)
        db.session.commit()
        return book.id


@pytest.fixture
def sample_member(app):
    with app.app_context():
        member = Member(name='Budi Santoso', email='budi@example.com', phone='081234567890')
        db.session.add(member)
        db.session.commit()
        return member.id


# ─── BOOK MODEL TESTS ──────── test semua hal yang berhubungan dengan validasi dan data buku

class TestBookValidation:
    def test_validate_isbn_10_digits_valid(self):
        assert Book.validate_isbn('0132350882') is True

    def test_validate_isbn_13_digits_valid(self):
        assert Book.validate_isbn('9780132350884') is True

    def test_validate_isbn_with_dashes_valid(self):
        assert Book.validate_isbn('978-0-13-235088-4') is True

    def test_validate_isbn_letters_invalid(self):
        assert Book.validate_isbn('97801323ABC84') is False

    def test_validate_isbn_wrong_length_invalid(self):
        assert Book.validate_isbn('12345') is False

    def test_validate_stock_zero_valid(self):
        assert Book.validate_stock(0) is True

    def test_validate_stock_positive_valid(self):
        assert Book.validate_stock(10) is True

    def test_validate_stock_negative_invalid(self):
        assert Book.validate_stock(-1) is False

    def test_validate_stock_string_invalid(self):
        assert Book.validate_stock('five') is False

    def test_book_to_dict(self, app, sample_book):
        with app.app_context():
            book = Book.query.get(sample_book)
            d = book.to_dict()
            assert d['title'] == 'Clean Code'
            assert d['author'] == 'Robert Martin'
            assert d['isbn'] == '9780132350884'
            assert d['stock'] == 3


# ─── MEMBER MODEL TESTS ─────── test semua hal yang berhubungan dengan validasi dan data anggota

class TestMemberValidation:
    def test_validate_email_valid(self):
        assert Member.validate_email('user@example.com') is True

    def test_validate_email_no_at_invalid(self):
        assert Member.validate_email('userexample.com') is False

    def test_validate_email_no_dot_after_at_invalid(self):
        assert Member.validate_email('user@examplecom') is False

    def test_validate_phone_valid(self):
        assert Member.validate_phone('081234567890') is True

    def test_validate_phone_none_valid(self):
        assert Member.validate_phone(None) is True

    def test_validate_phone_too_short_invalid(self):
        assert Member.validate_phone('1234') is False

    def test_validate_phone_letters_invalid(self):
        assert Member.validate_phone('08ABC12345') is False

    def test_member_to_dict(self, app, sample_member):
        with app.app_context():
            member = Member.query.get(sample_member)
            d = member.to_dict()
            assert d['name'] == 'Budi Santoso'
            assert d['email'] == 'budi@example.com'


# ─── LOAN MODEL TESTS ────────  test logika peminjaman, pengembalian, dan kalkulasi denda

class TestLoanLogic:
    def _make_loan(self, app, book_id, member_id, days_ago=0, overdue_by=0):
        with app.app_context():
            today = date.today()
            loan_date = today - timedelta(days=days_ago)
            due_date = today - timedelta(days=overdue_by) if overdue_by else today + timedelta(days=7)
            loan = Loan(
                book_id=book_id,
                member_id=member_id,
                loan_date=loan_date,
                due_date=due_date,
                status='active'
            )
            db.session.add(loan)
            db.session.commit()
            return loan.id

    def test_fine_zero_when_not_overdue(self, app, sample_book, sample_member):
        with app.app_context():
            loan = Loan(
                book_id=sample_book,
                member_id=sample_member,
                loan_date=date.today(),
                due_date=date.today() + timedelta(days=7),
                status='active'
            )
            db.session.add(loan)
            db.session.commit()
            assert loan.calculate_fine() == 0

    def test_fine_calculated_correctly_when_overdue(self, app, sample_book, sample_member):
        with app.app_context():
            loan = Loan(
                book_id=sample_book,
                member_id=sample_member,
                loan_date=date.today() - timedelta(days=10),
                due_date=date.today() - timedelta(days=3),
                status='active'
            )
            db.session.add(loan)
            db.session.commit()
            assert loan.calculate_fine() == 3 * 1000

    def test_fine_uses_return_date_when_returned(self, app, sample_book, sample_member):
        with app.app_context():
            due = date.today() - timedelta(days=5)
            returned = date.today() - timedelta(days=3)
            loan = Loan(
                book_id=sample_book,
                member_id=sample_member,
                loan_date=date.today() - timedelta(days=10),
                due_date=due,
                return_date=returned,
                status='returned'
            )
            db.session.add(loan)
            db.session.commit()
            assert loan.calculate_fine() == 2 * 1000

    def test_is_overdue_true(self, app, sample_book, sample_member):
        with app.app_context():
            loan = Loan(
                book_id=sample_book,
                member_id=sample_member,
                loan_date=date.today() - timedelta(days=10),
                due_date=date.today() - timedelta(days=1),
                status='active'
            )
            db.session.add(loan)
            db.session.commit()
            assert loan.is_overdue() is True

    def test_is_overdue_false(self, app, sample_book, sample_member):
        with app.app_context():
            loan = Loan(
                book_id=sample_book,
                member_id=sample_member,
                loan_date=date.today(),
                due_date=date.today() + timedelta(days=7),
                status='active'
            )
            db.session.add(loan)
            db.session.commit()
            assert loan.is_overdue() is False

    def test_loan_to_dict_contains_expected_keys(self, app, sample_book, sample_member):
        with app.app_context():
            loan = Loan(
                book_id=sample_book,
                member_id=sample_member,
                loan_date=date.today(),
                due_date=date.today() + timedelta(days=7),
                status='active'
            )
            db.session.add(loan)
            db.session.commit()
            d = loan.to_dict()
            assert 'id' in d
            assert 'book_id' in d
            assert 'member_id' in d
            assert 'status' in d
            assert d['return_date'] is None

    def test_custom_fine_per_day(self, app, sample_book, sample_member):
        with app.app_context():
            loan = Loan(
                book_id=sample_book,
                member_id=sample_member,
                loan_date=date.today() - timedelta(days=5),
                due_date=date.today() - timedelta(days=2),
                status='active'
            )
            db.session.add(loan)
            db.session.commit()
            assert loan.calculate_fine(fine_per_day=1000) == 2 * 1000