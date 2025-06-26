# -*- coding: utf-8 -*-"

"""
Address Book class implementation
"""

import datetime
import pickle
from typing import Optional, Union
from collections import UserDict, namedtuple, defaultdict
from collections.abc import Iterator
from pathlib import Path


from .error import ContactNotFound, ContactAlreadyExist, AddressBookDataFileWrongFormat
from .record import Record


class AddressBook(UserDict):
    def __init__(self, *args, congratulation_range_days: int = 7, datafile: Optional[Union[Path, str]] = None):
        """ Initialize an Address Book with the specified Contacts and the birthday congratulations days range, if given

        :param args: the contact records (Record, optional)
        :param upcoming_birthdays_period: the birthday congratulations days range (int)
        :param datafile: the file path where the address book data will be stored when it is saved, if specified
                         (string, Path, optional)
        """
        super().__init__()
        self.__congratulation_range_days = congratulation_range_days or 7
        self.__datafile = datafile
        # Add contact records if given, removing duplicates
        for contact in args:
            if str(contact.name) not in self:
                self.add_record(contact)

    def __getstate__(self):
        attributes = self.__dict__.copy()
        # Clear the Address Book data file path
        if f"_{self.__class__.__name__}__datafile" in attributes:
            attributes[f"_{self.__class__.__name__}__datafile"] = None
        return attributes

    def __setstate__(self, value):
        self.__dict__ = value

    def __congratulation_date(self, contact: Record, today: Optional[datetime.date] = None) -> Optional[datetime.date]:
        """Private method for calculation the congratulation date.
        If the birthday is not within the next congratulation_range_days days, including today, return None.
        If the birthday falls on a weekend, the congratulation date is shifted to the following Monday.

        :param today: Today's date, if not specified, is calculated as the current date (date, optional)
        :return: Congratulation date (datetime.date, optional)
        """
        try:
            # If today parameter is None, determine the current date
            if today is None:
                today = datetime.datetime.today().date()

            # Calculate next birthday
            next_birthday: Optional[datetime.date] = contact.next_birthday(today)

            # Verify if the birthday is within the next congratulation_range_days days, including today
            if next_birthday is None or not 0 <= (next_birthday - today).days <= self.__congratulation_range_days:
                # If the birthday does not exist or is not within the next congratulation_range_days days,
                # including today, return None
                return None

            # Verify if the birthday falls on a weekend
            if next_birthday.isoweekday() in {6, 7, }:
                # Shift the congratulation date to the following Monday, as it falls on a weekend
                next_birthday += datetime.timedelta(days=((7 - next_birthday.isoweekday()) + 1))

            # Return congratulation date as string in 'YYYY.MM.DD' format
            return next_birthday
        except Exception as e:
            # An unexpected error occurred
            # Raise an exception to the upper level
            raise Exception("An unexpected error occurred: {error}.".format(error=repr(e)))

    def find(self, name: str) -> Record:
        """ Search and return the contact record, or raise the contact not found exception

        :param name: contact name (string, mandatory)
        :return: contact record, if found (Record)
        """
        if name not in self:
            # Contact found - raise the contact not found exception
            raise ContactNotFound
        # Return the contact
        return self.get(name, None)

    def add_record(self, contact: Record) -> None:
        """ Add the contact record, or raise the contact already exists exception

        :param contact: contact record (Record, mandatory)
        """
        if str(contact.name) in self:
            # Contact found - raise the contact already exists exception
            raise ContactAlreadyExist()
        # Add the contact
        self.data[str(contact.name)] = contact

    def delete_record(self, name: str) -> None:
        """ Remove the contact record, or raise the contact not found exception

        :param name: contact name (string, mandatory)
        """
        if name not in self:
            # Contact found - raise the contact not found exception
            raise ContactNotFound()
        # Remove the contact
        self.pop(name, None)

    def upcoming_birthdays(self) -> Iterator[tuple[Record, datetime.date]]:
        """Return all contacts whose birthday is within the next period, including today,
        along with the congratulation date. If the birthday falls on a weekend, the congratulation date
        is moved to the following Monday.

        :return: The next contacts whose birthday is within the next period, including today,
        along with the congratulation date (Iterator of tuple)
        """

        # Named tuple creation
        UpcomingBirthday = namedtuple('UpcomingBirthday', ['contact', 'congratulation_date'])

        today: datetime.date = datetime.datetime.today().date()
        for contact in self.values():
            if (congratulation_date := self.__congratulation_date(contact, today=today)) is not None:
                # Return the upcoming birthday contact and the congratulation date
                yield UpcomingBirthday(contact, congratulation_date)

    def upcoming_birthdays_by_days(self) -> dict[datetime.date, list[Record]]:
        """Return all contacts whose birthday is within the next period, including today, grouped by date,
        along with the congratulation date. If the birthday falls on a weekend, the congratulation date
        is moved to the following Monday.

        :return: contacts whose birthday is within the next period, grouped by date (dictionary)
        """

        # Collect contacts whose birthday is within the next period with the congratulation date
        upcoming_birthdays: dict[datetime.date, list[Record]] = defaultdict(list)
        for record, congratulation_date in self.upcoming_birthdays():
            upcoming_birthdays[congratulation_date].append(record)

        # Sort and return contacts birthdays by date
        return dict(sorted(upcoming_birthdays.items()))

    def save(self) -> bool:
        if self.__datafile:
            # Verify that the specified path is the file if it already exists
            if self.__datafile.exists() and not self.__datafile.is_file():
                raise AddressBookDataFileWrongFormat(str(self.__datafile))

            # Make the data directory if it does not exist
            self.__datafile.parent.mkdir(exist_ok=True)

            # Save the Address Book to a file
            with open(self.__datafile, "wb") as fh:
                pickle.dump(self, fh)
            return True
        else:
            return False

    @classmethod
    def load(cls, datafile: Union[Path, str]):
        # Check whether the specified data file exists
        if datafile.exists():
            # Check whether the specified path is a file
            if not datafile.is_file():
                raise AddressBookDataFileWrongFormat(datafile)

            # Load the Address Book from a file
            with open(datafile, "rb") as fh:
                try:
                    book = pickle.load(fh)
                except Exception:
                    raise AddressBookDataFileWrongFormat(datafile)
                # Set the Address Book data file to the current file
                setattr(book, f"_{cls.__name__}__datafile", datafile)
                return book
        else:
            # File does not exist - create an empty Address Book
            return cls(datafile=datafile)
