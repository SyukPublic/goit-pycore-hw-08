# -*- coding: utf-8 -*-"

"""
Core functions for contacts bot
"""

import signal
import functools
from typing import Optional, Any, Callable
from contextlib import contextmanager
from pathlib import Path


from .cutil import console_style_reset, print_error, print_welcome, print_exit, print_help, print_colored
from .cutil import ERROR_TEXT_COLOR
from .futil import get_absolute_path
from .address_book import AddressBook, Record
from .address_book.error import ContactNotFound, AddressBookDataFileNotFound, AddressBookDataFileWrongFormat
from .contacts_bot_help import CONTACTS_BOT_HELP


CONTACTS_FILE: Path = get_absolute_path(Path(__file__).parent / "__data__" / "addressbook.pkl")


def exit_by_terminate_by_signals(number: int, stack: Any) -> None:
    """Exit by the SIGTERM/SIGINT signal

    :param number: signal number (number, mandatory)
    :param stack: current stack frame (number, mandatory)
    """
    print()


@contextmanager
def contacts_bot_data():
    """Context manager for contacts bot
    """

    print_welcome("Welcome to the assistant bot!")
    # Read the address book from a file or create a new one, if the file does not exist
    book = AddressBook.load(CONTACTS_FILE)
    try:
        yield book
    finally:
        # Write the address book to a file
        book.save()
        print_exit("Good bye!")


def parse_input(user_input: str) -> tuple[str, ...]:
    """Parse user input data

    :param user_input: user input data (string, mandatory)
    :return command and arguments (tuple of strings)
    """
    try:
        cmd, *args = user_input.split()
        cmd = cmd.strip().lower()
        return cmd, *args
    except ValueError:
        return ("", )

def input_error(
        value_error_message: Optional[str] = None,
        key_error_message: Optional[str] = None,
        index_error_message: Optional[str] = None,
) -> Callable:
    """Decorator functions with exceptions processing

    :param value_error_message: value error message (string, optional)
    :param key_error_message: key error message (string, optional)
    :param index_error_message: index error message (string, optional)
    :return exceptions processing function (Callable)
    """

    def _input_error(func: Callable):

        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> tuple:
            try:
                return func(*args, **kwargs)
            except Exception as e:
                exception_message: str = (str(e.args[0]) if hasattr(e, 'args') and len(args) > 0 else str(e))
                if isinstance(e, IndexError):
                    return ERROR_TEXT_COLOR, index_error_message or exception_message
                elif isinstance(e, KeyError):
                    return ERROR_TEXT_COLOR, key_error_message or exception_message
                elif isinstance(e, ValueError):
                    return ERROR_TEXT_COLOR, value_error_message or exception_message
                else:
                    return ERROR_TEXT_COLOR, exception_message

        return wrapper

    return _input_error


def show_all(args: list[str], book: AddressBook) -> str:
    """Return all contacts as string

    :param args: arguments, not used  (list of string, mandatory)
    :param book: address book (AddressBook, mandatory)
    :return contacts as string (string)
    """

    return "\n".join([f"{contact}" for contact in book.values()]) or "The address book is empty."


@input_error(index_error_message="Give me the name, please.")
def show_phone(args: list[str], book: AddressBook) -> str:
    """Return the phones for contact

    :param args: arguments with contact name (list of string, mandatory)
    :param book: address book (AddressBook, mandatory)
    :return contact's phones (string)
    """

    # Verify the number of arguments
    if len(args) < 1:
        raise IndexError("Invalid command arguments")

    # Unpack the arguments to the name
    name, *_ = args

    # Search for contact in the address book
    contact: Record = book.find(name)

    return "\n".join([str(phone) for phone in contact.phones]) or "The contact does not have any phone numbers."


@input_error(index_error_message="Give me the name and phone number, please.")
def add_contact(args: list[str], book: AddressBook) -> str:
    """Add the contact to the contacts or the phone number if the contact already exists

    :param args: arguments with contact name and phone number (list of string, mandatory)
    :param book: address book (AddressBook, mandatory)
    :return Operation status string (string)
    """

    # Verify the number of arguments
    if len(args) < 2:
        raise IndexError("Invalid command arguments")

    # Unpack the arguments to the name and phone number
    name, phone, *_ = args

    try:
        # Search for contact in the address book
        contact: Record = book.find(name)
        contact.add_phone(phone)
        return "Contact updated."
    except ContactNotFound:
        # The contact not found - add the contact
        book.add_record(Record(name, phones=[phone]))
        return "Contact added."


@input_error(index_error_message="Give me the name, existing phone number and new phone number, please.")
def change_contact(args: list[str], book: AddressBook) -> str:
    """Change the contact phone number

    :param args: arguments with contact name and phone numbers (list of string, mandatory)
    :param book: address book (AddressBook, mandatory)
    :return Operation status string (string)
    """

    # Verify the number of arguments
    if len(args) < 3:
        raise IndexError("Invalid command arguments")

    # Unpack the arguments to the name and phone number
    name, existing_phone, phone, *_ = args

    # Search for contact in the address book
    contact: Record = book.find(name)

    # Search for the specific phone number in the contact's record
    contact.edit_phone(existing_phone, phone)

    return "Contact updated."


@input_error(index_error_message="Give me the name, please.")
def delete_contact(args: list[str], book: AddressBook) -> str:
    """Delete the contact

    :param args: arguments with contact name (list of string, mandatory)
    :param book: address book (AddressBook, mandatory)
    :return Operation status string (string)
    """

    # Verify the number of arguments
    if len(args) < 1:
        raise IndexError("Invalid command arguments")

    # Unpack the arguments to the name
    name, *_ = args

    # Delete the contact
    book.delete_record(name)

    return "Contact deleted."


@input_error(index_error_message="Give me the name and date of birth, please.")
def add_contact_birthday(args: list[str], book: AddressBook) -> str:
    """Add the date of birth for the contact

    :param args: arguments with contact name and date of birth (list of string, mandatory)
    :param book: address book (AddressBook, mandatory)
    :return Operation status string (string)
    """

    # Verify the number of arguments
    if len(args) < 2:
        raise IndexError("Invalid command arguments")

    # Unpack the arguments to the name and phone number
    name, birthday, *_ = args

    # Search for contact in the address book
    contact: Record = book.find(name)

    # Add the date of birth for the contact
    contact.add_birthday(birthday)

    return "Date of birth added."


@input_error(index_error_message="Give me the name and date of birth, please.")
def change_contact_birthday(args: list[str], book: AddressBook) -> str:
    """Change the date of birth for the contact

    :param args: arguments with contact name and date of birth (list of string, mandatory)
    :param book: address book (AddressBook, mandatory)
    :return Operation status string (string)
    """

    # Verify the number of arguments
    if len(args) < 2:
        raise IndexError("Invalid command arguments")

    # Unpack the arguments to the name and phone number
    name, birthday, *_ = args

    # Search for contact in the address book
    contact: Record = book.find(name)

    # Change the date of birth for the contact
    contact.edit_birthday(birthday)

    return "Date of birth updated."


@input_error(index_error_message="Give me the name, please.")
def show_contact_birthday(args: list[str], book: AddressBook) -> str:
    """Return the date of birth for the contact

    :param args: arguments with contact name (list of string, mandatory)
    :param book: address book (AddressBook, mandatory)
    :return contact's date of birth (string)
    """

    # Verify the number of arguments
    if len(args) < 1:
        raise IndexError("Invalid command arguments")

    # Unpack the arguments to the name
    name, *_ = args

    # Search for contact in the address book
    contact: Record = book.find(name)

    return str(contact.birthday) if contact.birthday is not None else "The contact does not have a date of birth."


def show_upcoming_birthdays(args: list[str], book: AddressBook) -> str:
    """Return all contacts whose birthday is within the next week, including today, grouped by date

    :param args: arguments, not used  (list of string, mandatory)
    :param book: address book (AddressBook, mandatory)
    :return contacts whose birthday is within the next period (string)
    """

    upcoming_birthdays_text: str = ""
    # Add all the upcoming birthdays grouped by days
    for congratulation_date, records in book.upcoming_birthdays_by_days().items():
        upcoming_birthdays_text += "\n" + 3 * "-" + "\n"
        upcoming_birthdays_text += congratulation_date.strftime("%d.%m.%Y")
        upcoming_birthdays_text += "\n"
        upcoming_birthdays_text += "\n".join([str(record) for record in records])
    if upcoming_birthdays_text:
        upcoming_birthdays_text += "\n" + 3 * "-" + "\n"

    return upcoming_birthdays_text or "There are currently no upcoming birthdays."


def main() -> None:
    # Interceptors for the SIGINT and SIGTERM signals (for example Ctrl + c exit)
    signal.signal(signal.SIGINT, exit_by_terminate_by_signals)
    signal.signal(signal.SIGTERM, exit_by_terminate_by_signals)

    address_book_commands = {
        "all": show_all,
        "phone": show_phone,
        "add": add_contact,
        "change": change_contact,
        "delete": delete_contact,
        "add-birthday": add_contact_birthday,
        "change-birthday": change_contact_birthday,
        "show-birthday": show_contact_birthday,
        "birthdays": show_upcoming_birthdays,
    }

    try:
        with contacts_bot_data() as book:

            print_help("Enter 'help' for a list of built-in commands.")

            while True:
                command: Optional[str] = None
                args: list[str] = []
                try:
                    command, *args = parse_input(input("Enter a command: "))
                except EOFError:
                    break
                try:
                    if command in address_book_commands:
                        print_colored(address_book_commands[command](args, book))
                    else:
                        if command in {"close", "exit", "quit", }:
                            break
                        elif command == "hello":
                            print_colored("How can I help you?")
                            print_help("Enter 'help' for a list of built-in commands.")
                        elif  command == "help":
                            print_help(CONTACTS_BOT_HELP)
                        else:
                            print_error("Invalid command.")
                except Exception as e:
                    print_error("An unexpected error occurred: {error}.".format(error=repr(e)))
    except (AddressBookDataFileNotFound, AddressBookDataFileWrongFormat, ) as e:
        print_error(e)
    except Exception as e:
        print_error("An unexpected error occurred: {error}.".format(error=repr(e)))

    # Reset console styles to default
    console_style_reset()

    exit(0)


if __name__ == "__main__":
    main()
