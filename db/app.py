from flask import Flask, request, jsonify
import psycopg2
import os
from dotenv import load_dotenv

app = Flask(__name__)
load_dotenv()

# Connect to PostgreSQL using environment variables
conn = psycopg2.connect(
    dbname="restapi",
    user="postgres",
    password=os.getenv("DB_PASSWORD"),
    host="localhost"
)
cur = conn.cursor()

# Create table if not exists
cur.execute("""
    CREATE TABLE IF NOT EXISTS books (
        id SERIAL PRIMARY KEY,
        title TEXT NOT NULL,
        author TEXT NOT NULL,
        isbn TEXT NOT NULL,
        publication_date DATE NOT NULL
    );
""")
conn.commit()

# Function to check if a book ID exists
def book_exists(book_id):
    cur.execute("SELECT COUNT(*) FROM books WHERE id = %s", (book_id,))
    return cur.fetchone()[0] > 0

# Function to validate book data
def validate_book_data(data):
    if 'title' not in data or 'author' not in data or 'isbn' not in data or 'publication_date' not in data:
        return False
    if not all(data[key] for key in ['title', 'author', 'isbn', 'publication_date']):
        return False
    # Add more specific validation logic here if needed
    return True

@app.route('/books', methods=['POST'])
def create_book():
    data = request.get_json()
    if not validate_book_data(data):
        return jsonify({'error': 'Invalid book data or missing required fields'}), 400

    title = data.get('title')
    author = data.get('author')
    isbn = data.get('isbn')
    publication_date = data.get('publication_date')

    # Check if the book already exists
    cur.execute("SELECT * FROM books WHERE title = %s AND author = %s AND isbn = %s AND publication_date = %s",
                (title, author, isbn, publication_date))
    existing_book = cur.fetchone()
    if existing_book:
        return jsonify({'error': 'Book with the same title, author, ISBN, and publication date already exists'}), 400

    # If the book doesn't exist, insert it into the database
    cur.execute("INSERT INTO books (title, author, isbn, publication_date) VALUES (%s, %s, %s, %s)",
                (title, author, isbn, publication_date))
    conn.commit()

    return jsonify({'message': 'Book created successfully'}), 201


@app.route('/books', methods=['GET'])
def get_books():
    cur.execute("SELECT * FROM books")
    books = cur.fetchall()
    return jsonify(books)

@app.route('/books/<int:book_id>', methods=['PUT'])
def update_book(book_id):
    if not book_exists(book_id):
        return jsonify({'error': f'Book with ID {book_id} does not exist'}), 404

    data = request.get_json()
    if not validate_book_data(data):
        return jsonify({'error': 'Invalid book data or missing required fields'}), 400

    title = data.get('title')
    author = data.get('author')
    isbn = data.get('isbn')
    publication_date = data.get('publication_date')

    cur.execute("UPDATE books SET title = %s, author = %s, isbn = %s, publication_date = %s WHERE id = %s",
                (title, author, isbn, publication_date, book_id))
    conn.commit()

    return jsonify({'message': 'Book updated successfully'})

@app.route('/books/<int:book_id>', methods=['DELETE'])
def delete_book(book_id):
    if not book_exists(book_id):
        return jsonify({'error': f'Book with ID {book_id} does not exist'}), 404

    cur.execute("DELETE FROM books WHERE id = %s", (book_id,))
    conn.commit()
    return jsonify({'message': 'Book deleted successfully'})

if __name__ == '__main__':
    app.run(debug=True)
