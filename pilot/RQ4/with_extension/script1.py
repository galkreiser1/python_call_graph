class Book:
    def __init__(self, title, author):
        self.title = title
        self.author = author
        self.is_reserved = False

    def reserve(self):
        if not self.is_reserved:
            self.is_reserved = True
            return "Reserved"
        return False

class Library:
    def __init__(self):
        self.books = []

    def add_book(self, book):
        self.books.append(book)

    def reserve_book(self, title):
        for book in self.books:
            if book.title == title:
                # Incorrectly returns False
                return False
        return False

def main():
    library = Library()
    library.add_book(Book("1984", "George Orwell"))
    library.add_book(Book("Brave New World", "Aldous Huxley"))

    success = library.reserve_book("1984")
    print("Reservation Successful (boolean):", success)

main()
