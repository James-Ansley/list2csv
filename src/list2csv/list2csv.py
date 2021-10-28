import csv as _csv
from operator import attrgetter as _attrgetter
from typing import TypeVar, TextIO, Any, Union, Iterable, Callable, Generic

T = TypeVar('T')
FieldEvaluator = Union[Callable[[T], Any], str]
MultiEvaluator = Union[Callable[[T], Iterable], str]


class Writer(Generic[T]):
    def __init__(self, f: TextIO):
        self._writer = _csv.writer(f)
        self._fields: list[_Field] = []
        self._counters: list[_Counter] = []

    def add_field(self,
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
        self._fields.append(_Field(header, field, data_format, aggregate))

    def add_multi_field(self,
                        header: str,
                        field: MultiEvaluator,
                        number: int,
                        data_format: str = '{}',
                        *,
                        start: int = 1,
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
        :param number: The number of columns to write.
        :param data_format: A format specifier with a single placeholder value
        :param start: The starting number of the columns.
        :param aggregate: Whether the data in these columns will contribute to
            the aggregate value of the row
        """
        self._fields.append(
            _MultiField(header, field, number, data_format, aggregate, start)
        )

    def add_counter(self, header: str = 'ID', *, start: int = 0, step: int = 1):
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
                       aggregator: MultiEvaluator,
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
            header for field in self._fields for header in field.name
        )

    def write(self, item: T):
        """
        Writes the fields of an object of type T.
        """
        aggregate_values = []
        row = []
        for field in self._fields:
            if isinstance(field, _Aggregator):
                value = field.format(aggregate_values)
                aggregate_values = []
            else:
                value = field.format(item)

            if field.aggregate:
                aggregate_values.extend(field.eval(item))
            row.extend(value)
        for counter in self._counters:
            counter.increment()
        self._writer.writerow(row)

    def write_all(self, items: Iterable[T]):
        """
        Writes the fields for each instance of T in an iterable of type T.
        """
        for item in items:
            self.write(item)


class _Field:
    def __init__(self,
                 name: Union[str, list[str]],
                 function: FieldEvaluator,
                 data_format: str = '{}',
                 aggregate: bool = False):
        self.name = [name] if isinstance(name, str) else name
        if isinstance(function, str):
            self.function = _attrgetter(function)
        else:
            self.function = function
        self.data_format = data_format
        self.aggregate = aggregate

    def eval(self, item: T) -> Any:
        return [self.function(item)]

    def format(self, item: T) -> list[str]:
        return [self.data_format.format(self.function(item))]


class _Aggregator(_Field):
    ...


class _Counter(_Field):
    def __init__(self, name: str, start: int, step: int):
        super().__init__(name, lambda _: _)
        self.current = start
        self.step = step

    def eval(self, item: T) -> list[Any]:
        return [self.current]

    def format(self, item: T) -> list[str]:
        return [str(self.current)]

    def increment(self):
        self.current += self.step


class _MultiField(_Field):
    def __init__(self,
                 header: str,
                 field: FieldEvaluator,
                 number: int,
                 data_format: str = '{}',
                 aggregate: bool = False,
                 start: int = 1):
        headers = [header.format(i) for i in range(start, number + start)]
        self.number = number
        self._multi_header = header
        super().__init__(headers, field, data_format, aggregate)

    def eval(self, item: T) -> list[Any]:
        data = list(super().eval(item)[0])
        if len(data) != self.number:
            raise ValueError(
                f'Item: "{item}" does not return the correct number of values\n'
                f'under multicolumn "{self._multi_header}"'
            )
        return data

    def format(self, item: T) -> list[str]:
        return [self.data_format.format(res) for res in self.eval(item)]
