import csv as _csv
from dataclasses import dataclass as _dataclass
from operator import attrgetter as _attrgetter
from typing import TypeVar, TextIO, Any, Union, Iterable, Callable

T = TypeVar('T')


class Writer:
    def __init__(self, f: TextIO):
        self._writer = _csv.writer(f)
        self._fields = []

    def add_field(self,
                  header: str,
                  field: Union[Callable[[T], Any], str],
                  data_format: str = '{}'):
        """
        Adds a field that will be written as a column.

        :param header: The name of the column header
        :param field: An instance attribute name of an object of type T or
            a function that maps an instance of T to some result
        :param data_format: A format specifier with a placeholder value
        """
        self._fields.append(_Field(header, field, data_format))

    def write_header(self):
        """
        Writes the header names to columns in the CSV wile.
        Will write to the current row by appending to the file.
        """
        self._writer.writerow(field.name for field in self._fields)

    def write(self, item: T):
        """
        Writes the fields of an object of type T.
        """
        row = [field.eval(item) for field in self._fields]
        self._writer.writerow(row)

    def write_all(self, items: Iterable[T]):
        """
        Writes the fields for each instance of T in an iterable of type T.
        """
        for item in items:
            self.write(item)


@_dataclass
class _Field:
    name: str
    function: Union[Callable[[T], Any], str]
    data_format: str = '{}'

    def __post_init__(self):
        if isinstance(self.function, str):
            self.function = _attrgetter(self.function)

    def eval(self, item: T) -> str:
        return self.data_format.format(self.function(item))
