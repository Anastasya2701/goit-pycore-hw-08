from collections import UserDict
from datetime import datetime, timedelta
import pickle

class Field: #Базовий клас для полів запису
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return str(self.value)

class Name(Field): #Клас для зберігання імені контакту. Обов'язкове поле.
    def __init__(self, value):
        super().__init__(value)

class Phone(Field): #Клас для зберігання номеру телефона. Має валідацію формату.
    def __init__(self, phone):
        if not phone.isdigit() or len(phone) != 10:
            raise ValueError("Номер телефону має складатись з 10 цифр.")
        super().__init__(phone)

class Birthday(Field):
    def __init__(self, value):
        try:
            self.value = datetime.strptime(value, "%d.%m.%Y").date()
        except ValueError:
            raise ValueError("Не правильний формат дати має бути ДД.ММ.РРРР.")

class AddressBook(UserDict): # Клас для зберігання всіх контатів
    def add_record(self, record): # Метод додавання контакту
        self.data[record.name.value] = record

    def find(self, name): # Метод для знаходження та перевірки контакту
        return self.data.get(name)

    def string_to_date(self, date_string):
        return datetime.strptime(date_string, "%d.%m.%Y").date()

    def date_to_string(self, date):
        return date.strftime("%d.%m.%Y")

    def find_next_weekday(self, birthday, start_date, weekday):
        days_ahead = weekday - start_date.weekday()
        if days_ahead <= 0:
            days_ahead += 7
        return start_date + timedelta(days_ahead)
    
    def adjust_for_weekday(self, date):
        if date.weekday() == 5:
            date += timedelta(days=2)
        elif date.weekday() == 6:
            date += timedelta(days=1)
        return date

    def get_upcoming_birthdays(self, days=7):
        upcoming_birthdays = []
        today = datetime.today().date()

        for contact in self.data.values():
            if contact.birthday:  # Перевірка наявності дати народження
                birthday_date = contact.birthday.value
                birthday = birthday_date.replace(year=today.year)
                birthday = self.adjust_for_weekday(birthday)
                if birthday < today:
                    birthday = birthday.replace(year=birthday.year + 1)
                delta_days = (birthday - today).days
                birthday = self.adjust_for_weekday(birthday)
                if 0 <= delta_days <= days:
                    congratulation_date_str = self.date_to_string(birthday)
                    upcoming_birthdays.append({"name": contact.name.value, "congratulation_date": congratulation_date_str})

        return upcoming_birthdays

    def delete(self, name): # Метод для видалення контакту
        del self[name]

    def __str__(self):
        return "\n".join(str(record) for record in self.data.values())

class Record: # Клас для зберігання інформації про контакт (ім'я та номер телефону).
    def __init__(self, name):
        self.name = Name(name)
        self.birthday = None
        self.phones = []

    def add_phone(self, phone): # додавання
        self.phones.append(Phone(phone))

    def edit_phone(self, old_phone, new_phone): # зміна
        for ind, number in enumerate(self.phones):
            if number.value == old_phone:
                self.phones[ind] = Phone(new_phone)
                break
        else:
            raise ValueError

    def remove_phone(self, phone): #видалення
        for number in self.phones:
            if number.value == phone:
                self.phones.remove(number)
                return
        raise ValueError

    def add_birthday(self, birthday): 
        self.birthday = birthday

    def find_phone(self, phone: str) -> str: #пошук
        for number in self.phones:
            if number.value == phone:
                return number
        return None

    def __str__(self):
        return f"Contact name: {self.name.value}, phones: {'; '.join(number.value for number in self.phones)}"

def input_error(func):
    def inner(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except ValueError as e:
            print(str(e))
        except AttributeError as e:
            print(str(e))
    return inner

def parse_input(user_input: str):
    command, *args = user_input.split()
    command = command.strip().lower()
    return command, args

def get_greeting():
    return "How can I help you?"

@input_error
def add_contact(args, book: AddressBook):
    name, phone = args
    record = book.find(name)

    if record is None:
        record = Record(name)
        book.add_record(record)
        record.add_phone(phone)
        return "Contact added."
    else:
        record.add_phone(phone)
        return 'Contact updated'

@input_error
def change_contact(args, book: AddressBook):
    name, old_phone, new_phone = args
    record = book.find(name)
    if record:
        try:
            record.edit_phone(old_phone, new_phone)
            return 'Contact updated'
        except ValueError:
            raise ValueError('Number not found')
    else:
        raise ValueError('Contact not found')

@input_error
def show_phone(args, book: AddressBook):
    name = args[0]
    record = book.find(name)
    if record:
        return f"{record.name.value}: {', '.join(phone.value for phone in record.phones)}"
    else:
        return f"Contact with name {name} not found."

@input_error
def show_all(book: AddressBook):
    if len(book.data) == 0:
        return "Contacts list is empty."
    return "\n".join(str(record) for record in book.data.values())

@input_error
def add_birthday(args, book: AddressBook):
    name, birthday = args
    record = book.find(name)

    if not record:
        record = Record(name)
        book.add_record(record)

    record.add_birthday(Birthday(birthday))

    return "Birthday added."

@input_error
def show_birthday(args, book: AddressBook):
    name = args[0]
    record = book.find(name)

    if not record:
        return f"{name} doesn't exist."
    if not record.birthday:
        return f"{name} doesn't have birthday."
    return record.birthday.value

def birthdays(book: AddressBook):
    upcoming_birthdays = book.get_upcoming_birthdays()
    if upcoming_birthdays:
        return "Upcoming birthdays:\n" + "\n".join(f"{user['name']}'s birthday: {user['congratulation_date']}" for user in upcoming_birthdays)
    else:
        return "No upcoming birthdays within the next week."
    
import pickle

def save_data(book, filename="addressbook.pkl"):
    with open(filename, "wb") as f:
        pickle.dump(book, f)

def load_data(filename="addressbook.pkl"):
    try:
        with open(filename, "rb") as f:
            return pickle.load(f)
    except FileNotFoundError:
        return AddressBook()  # Повернення нової адресної книги, якщо файл не знайдено


def get_good_bye():
    return "Good bye!"

def main():
    # book = AddressBook()
    book = load_data()
    print("Welcome to the assistant bot!")
    while True:
        user_input = input("Enter a command: ")
        command, args = parse_input(user_input)

        if command == "hello":
            print(get_greeting())
        elif command == "add":
            print(add_contact(args, book))
        elif command == "change":
            print(change_contact(args, book))
        elif command == "phone":
            print(show_phone(args, book))
        elif command == "all":
            print(show_all(book))
        elif command == "add-birthday":
            print(add_birthday(args, book))
        elif command == "show-birthday":
            print(show_birthday(args, book))
        elif command == "birthdays":
            print(birthdays(book))
        elif command in ("close", "exit"):
            save_data(book)
            print(get_good_bye())
            break
        else:
            print("Invalid command.")

if __name__ == "__main__":
    main()