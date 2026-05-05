"""
Integration Tests – Library Management System
Menguji endpoint API, interaksi database, dan alur peminjaman end-to-end.
"""
import pytest
import json
from app import create_app, db
from app.models import Book, Member, Loan
from datetime import date, timedelta


# ─── FIXTURES ────────────────────────────────────────────────────────────────

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
def client(app):
    return app.test_client()


@pytest.fixture
def seeded(app):
    """Seed database dengan satu buku dan satu anggota."""
    with app.app_context():
        book = Book(title='The Pragmatic Programmer', author='Dave Thomas',
                    isbn='9780201616224', stock=2)
        member = Member(name='Siti Rahayu', email='siti@example.com',
                        phone='082345678901')
        db.session.add_all([book, member])
        db.session.commit()
        return {'book_id': book.id, 'member_id': member.id}


# ─── BOOK ENDPOINT TESTS ─────────────────────────────────────────────────────

class TestBookEndpoints:
    def test_add_book_success(self, client):
        res = client.post('/api/books', json={
            'title': 'Clean Code', 'author': 'Robert Martin', 'isbn': '9780132350884'
        })
        assert res.status_code == 201
        data = res.get_json()
        assert data['title'] == 'Clean Code'
        assert data['stock'] == 1

    def test_add_book_missing_field_returns_400(self, client):
        res = client.post('/api/books', json={'title': 'No Author'})
        assert res.status_code == 400

    def test_add_book_duplicate_isbn_returns_409(self, client):
        payload = {'title': 'Book A', 'author': 'Author A', 'isbn': '9780132350884'}
        client.post('/api/books', json=payload)
        res = client.post('/api/books', json=payload)
        assert res.status_code == 409

    def test_add_book_invalid_isbn_returns_400(self, client):
        res = client.post('/api/books', json={
            'title': 'Bad ISBN', 'author': 'Someone', 'isbn': 'INVALID'
        })
        assert res.status_code == 400

    def test_get_books_returns_list(self, client, seeded):
        res = client.get('/api/books')
        assert res.status_code == 200
        assert isinstance(res.get_json(), list)
        assert len(res.get_json()) >= 1

    def test_get_book_by_id_not_found(self, client):
        res = client.get('/api/books/9999')
        assert res.status_code == 404

    def test_update_book_stock(self, client, seeded):
        book_id = seeded['book_id']
        res = client.put(f'/api/books/{book_id}', json={'stock': 10})
        assert res.status_code == 200
        assert res.get_json()['stock'] == 10

    def test_delete_book(self, client, seeded):
        book_id = seeded['book_id']
        res = client.delete(f'/api/books/{book_id}')
        assert res.status_code == 200
        assert client.get(f'/api/books/{book_id}').status_code == 404


# ─── MEMBER ENDPOINT TESTS ───────────────────────────────────────────────────

class TestMemberEndpoints:
    def test_add_member_success(self, client):
        res = client.post('/api/members', json={
            'name': 'Andi', 'email': 'andi@example.com', 'phone': '081111111111'
        })
        assert res.status_code == 201
        assert res.get_json()['email'] == 'andi@example.com'

    def test_add_member_invalid_email_returns_400(self, client):
        res = client.post('/api/members', json={
            'name': 'Bad Email', 'email': 'not-an-email'
        })
        assert res.status_code == 400

    def test_add_member_duplicate_email_returns_409(self, client):
        payload = {'name': 'Devi', 'email': 'devi@example.com'}
        client.post('/api/members', json=payload)
        res = client.post('/api/members', json=payload)
        assert res.status_code == 409

    def test_get_members_returns_list(self, client, seeded):
        res = client.get('/api/members')
        assert res.status_code == 200
        assert len(res.get_json()) >= 1

    def test_get_member_not_found(self, client):
        res = client.get('/api/members/9999')
        assert res.status_code == 404


# ─── LOAN FLOW INTEGRATION TESTS ─────────────────────────────────────────────

class TestLoanFlow:
    def test_full_loan_and_return_flow(self, client, seeded):
        """End-to-end: pinjam buku → kembalikan → cek stok bertambah."""
        book_id = seeded['book_id']
        member_id = seeded['member_id']

        # Catat stok awal
        initial_stock = client.get(f'/api/books/{book_id}').get_json()['stock']

        # Buat pinjaman
        res = client.post('/api/loans', json={
            'book_id': book_id,
            'member_id': member_id,
            'loan_days': 7
        })
        assert res.status_code == 201
        loan_id = res.get_json()['id']

        # Stok berkurang
        stock_after_loan = client.get(f'/api/books/{book_id}').get_json()['stock']
        assert stock_after_loan == initial_stock - 1

        # Kembalikan buku
        res = client.post(f'/api/loans/{loan_id}/return')
        assert res.status_code == 200
        assert res.get_json()['status'] == 'returned'

        # Stok kembali normal
        stock_after_return = client.get(f'/api/books/{book_id}').get_json()['stock']
        assert stock_after_return == initial_stock

    def test_loan_book_out_of_stock(self, client, seeded, app):
        """Tidak bisa meminjam buku dengan stok 0."""
        book_id = seeded['book_id']
        member_id = seeded['member_id']

        # Atur stok ke 0
        with app.app_context():
            book = Book.query.get(book_id)
            book.stock = 0
            db.session.commit()

        res = client.post('/api/loans', json={
            'book_id': book_id, 'member_id': member_id
        })
        assert res.status_code == 400
        assert 'out of stock' in res.get_json()['error'].lower()

    def test_return_already_returned_book(self, client, seeded):
        """Mengembalikan buku yang sudah dikembalikan harus error."""
        book_id = seeded['book_id']
        member_id = seeded['member_id']

        res = client.post('/api/loans', json={'book_id': book_id, 'member_id': member_id})
        loan_id = res.get_json()['id']

        client.post(f'/api/loans/{loan_id}/return')
        res2 = client.post(f'/api/loans/{loan_id}/return')
        assert res2.status_code == 400

    def test_get_fine_for_overdue_loan(self, client, seeded, app):
        """Cek kalkulasi denda melalui endpoint /fine."""
        book_id = seeded['book_id']
        member_id = seeded['member_id']

        with app.app_context():
            loan = Loan(
                book_id=book_id,
                member_id=member_id,
                loan_date=date.today() - timedelta(days=10),
                due_date=date.today() - timedelta(days=3),
                status='active'
            )
            db.session.add(loan)
            db.session.commit()
            loan_id = loan.id

        res = client.get(f'/api/loans/{loan_id}/fine')
        assert res.status_code == 200
        data = res.get_json()
        assert data['fine'] == 3 * 1000
        assert data['is_overdue'] is True

    def test_loan_nonexistent_book_returns_404(self, client, seeded):
        res = client.post('/api/loans', json={
            'book_id': 9999,
            'member_id': seeded['member_id']
        })
        assert res.status_code == 404

    def test_loan_nonexistent_member_returns_404(self, client, seeded):
        res = client.post('/api/loans', json={
            'book_id': seeded['book_id'],
            'member_id': 9999
        })
        assert res.status_code == 404

    def test_get_loans_list(self, client, seeded):
        res = client.get('/api/loans')
        assert res.status_code == 200
        assert isinstance(res.get_json(), list)