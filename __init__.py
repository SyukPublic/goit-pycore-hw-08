# -*- coding: utf-8 -*-"

__title__ = 'Home Work 07'
__author__ = 'Roman'

import tasks.address_book.error as address_book_errors
from tasks.address_book import AddressBook, Record
from tasks.contacts_bot import main as contacts_bot

__all__ = ['AddressBook', 'Record', 'address_book_errors', 'contacts_bot']
