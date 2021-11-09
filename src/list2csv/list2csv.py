import csv as _csv
from operator import attrgetter as _attrgetter
from typing import TypeVar, TextIO, Any, Union, Iterable, Callable, Generic

__all__ = ['Writer']

T = TypeVar('T')
V = TypeVar('V')
FieldEvaluator = Union[Callable[[T], V], str]
MultiEvaluator = Union[Callable[[Iterable[T]], Iterable[V]], str]
Aggregator = Callable[[Iterable[V]], Any]


class Writer(Generic[T, V]):
    def __init__(self, f: TextIO):
        self._writer = _csv.writer(f)
        self._fields: list[_Column] = []
        self._counters: list[_Counter] = []

    def add_column(self,
                   header: str,
                   field: FieldEvaluator,
                   data_format: str = '{}',
                   *,
                   aggregate: bool = False):
        """
        Adds a field that will be written as a column.

        :param header: The name of the column header
        :param field: An instance attribute name of an object of type T or
            a function that maps an instance of T to some result
        :param data_format: A format specifier with a single placeholder value
        :param aggregate: Whether the data in this column will contribute to
            the aggregate value of the row
        """
        self._fields.append(_Column(header, field, data_format, aggregate))

    def add_multi_column(self,
                         header: str,
                         field: MultiEvaluator,
                         range_: range,
                         data_format: str = '{}',
                         *,
                         aggregate: bool = False):
        """
        Adds a field that will be written as set of columns.

        :param header: The name of the column header. This must contain exactly
            one placeholder value ('{}') which will be filled in with the number
            of the column.
        :param field: An instance attribute name of an object of type T or
            a function that maps an instance of T to some iterable of length
            `number`. If the function does not return or the field is not an
            iterable of length `number`, a ValueError will be raised upon
            writing.
        :param range_: A Range that will provide the numbers that can be used
            to index the columns.
        :param data_format: A format specifier with a single placeholder value
        :param aggregate: Whether the data in these columns will contribute to
            the aggregate value of the row
        """
        self._fields.append(
            _MultiColumn(header, field, range_, data_format, aggregate)
        )

    def add_counter(self, header: str, *, start: int = 0, step: int = 1):
        """
        Adds an auto incrementing counter to the CSV.

        :param header: The name of the column header
        :param start: The starting value of the counter
        :param step: The increment value of the counter
        """
        counter = _Counter(header, start, step)
        self._counters.append(counter)
        self._fields.append(counter)

    def add_aggregator(self,
                       header: str,
                       aggregator: Aggregator,
                       data_format: str = '{}'):
        """
        Adds an aggregator to the CSV. This combines all values to the left of
        this column after the last aggregator using the given aggregator
        function.

        :param header: The name of the column header
        :param aggregator: A function that maps an iterable of values to
            some value.
        :param data_format: A format specifier with a single placeholder value
        """
        self._fields.append(_Aggregator(header, aggregator, data_format))

    def write_header(self):
        """
        Writes the header names to columns in the CSV wile.
        Will write to the current row by appending to the file.
        """
        self._writer.writerow(
            header for field in self._fields for header in field.header
        )

    def write(self, item: T):
        """
        Writes the fields of an object of type T.
        """
        aggregate_values = []
        row = []
        for field in self._fields:
            if isinstance(field, _Aggregator):
                value = field.eval(aggregate_values)
                aggregate_values = []
            else:
                value = field.eval(item)

            if field.aggregate:
                aggregate_values.extend(value)
            row.extend(field.format(value))
        for counter in self._counters:
            counter.increment()
        self._writer.writerow(row)

    def write_all(self, items: Iterable[T]):
        """
        Writes the fields for each instance of T in an iterable of type T.
        """
        for item in items:
            self.write(item)


class _Column(Generic[T, V]):
    def __init__(self,
                 header: str,
                 function: FieldEvaluator,
                 data_format: str = '{}',
                 aggregate: bool = False):
        self._header = header
        if isinstance(function, str):
            self.function = _attrgetter(function)
        else:
            self.function = function
        self.data_format = data_format
        self.aggregate = aggregate

    @property
    def header(self):
        return [self._header]

    def eval(self, item: T) -> list[V]:
        return [self.function(item)]

    def format(self, data: list[V]) -> list[str]:
        return [self.data_format.format(data[0])]


class _Aggregator(_Column):
    ...


class _Counter(_Column):
    def __init__(self, header: str, start: int, step: int):
        super().__init__(header, '')
        self.current = start
        self.step = step

    def eval(self, item: T) -> list[int]:
        return [self.current]

    def format(self, data: list[int]) -> list[str]:
        return [str(self.current)]

    def increment(self):
        self.current += self.step


class _MultiColumn(_Column):
    def __init__(self,
                 header: str,
                 function: FieldEvaluator,
                 range_: range,
                 data_format: str = '{}',
                 aggregate: bool = False):
        super().__init__(header, function, data_format, aggregate)
        self._range = range_

    @property
    def header(self):
        return [self._header.format(i) for i in self._range]

    def eval(self, item: T) -> list[V]:
        data = self.function(item)
        if len(data) != len(self._range):
            raise ValueError(
                f'Item: "{item}" does not return the correct number of values '
                f'under multicolumn "{self._header}"'
            )
        return data

    def format(self, data: list[V]) -> list[str]:
        return [self.data_format.format(res) for res in data]
