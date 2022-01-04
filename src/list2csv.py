import abc as _abc
import csv as _csv
from collections import defaultdict as _defaultdict
from operator import attrgetter
from typing import Generic, TypeVar, TextIO, Callable, Iterable, Any, Union

__all__ = ['Writer']

T = TypeVar('T')
V = TypeVar('V')

_eval_func = Union[Callable[[T], Any], str]
_multi_eval_func = Union[Callable[[T], Iterable], str]
_aggregate_func = Callable[[Iterable[T]], Any]


class Writer(Generic[T]):
    def __init__(self, f: TextIO):
        self._writer = _csv.writer(f)
        self._fields = []
        self._to_aggregate = _defaultdict(list)
        self._row_count = 0

    def add_column(self,
                   header: str,
                   evaluator: _eval_func,
                   data_format: str = '{}',
                   aggregate_ids: set = frozenset()):
        """
        Adds a column of name ``header``.

        For each item of type ``T``, the value of ``evaluator(item)`` is
        formatted using ``data_format`` as a format string and used as the
        column data. If ``evaluator`` is a string, it is interpreted as an
        attribute name of the item.

        Any field with ids in ``aggregate_ids`` will be aggregated in the
        relevant aggregator column for each given id.
        See :meth:`add_aggregator` for more.
        """
        field = _Simple(header, evaluator, data_format)
        self._fields.append(field)
        self._add_to_aggregate(field, aggregate_ids)

    def add_aggregator(self,
                       aggregate_id,
                       header: str,
                       aggregate_evaluator: _aggregate_func,
                       data_format: str = '{}',
                       aggregate_ids: set = frozenset()):
        """
        Adds an aggregator column of name ``header``.

        All columns which were added with the id ``aggregate_id`` will be
        aggregated by passing all the values from their respective
        ``evaluator`` functions into the ``aggregate_evaluator`` function.
        The result is formatted using ``data_format``.

        The aggregator column itself can be aggregated in other aggregator
        columns if ids are given in ``aggregate_ids``.
        """
        to_aggregate = self._to_aggregate[aggregate_id]
        field = _Aggregator(
            header, aggregate_evaluator, data_format, to_aggregate
        )
        self._fields.append(field)
        self._add_to_aggregate(field, aggregate_ids)

    def add_counter(self,
                    header: str,
                    start: int = 1,
                    step: int = 1,
                    aggregate_ids: set = frozenset()):
        """
        Adds a counter column of name ``header``.

        For each row, the counter writes the current value and increments by
        the given ``step`` value. The counter starts at ``start`` inclusive.
        """
        field = _Counter(header, start, step)
        self._fields.append(field)
        self._add_to_aggregate(field, aggregate_ids)

    def add_multi(self,
                  header_template: str,
                  evaluator: _multi_eval_func,
                  num_items: int,
                  data_format: str = '{}',
                  aggregate_ids: set = frozenset()):
        """
        Adds several columns, each corresponding to a single value taken from
        an iterable of length ``num_items``.

        Each resulting column will be named ``header_template.format(i)``,
        where ``i`` is the one-based index of the column.

        The values of each column are evaluated and formatted as for columns
        added with ``add_column``.

        If aggregate ids are given, the columns will be aggregated in the
        relevant aggregator columns for each given id.
        """
        evaluator = _Field.normalise_evaluator(evaluator)
        sequence_field = _Simple('', lambda item: tuple(evaluator(item)), '{}')
        for i in range(1, num_items + 1):
            header = header_template.format(i)
            field = _Multi(header, sequence_field, i - 1, data_format)
            self._fields.append(field)
            self._add_to_aggregate(field, aggregate_ids)

    def write_header(self):
        """
        Writes the header row.

        This can be called at any time after adding columns.
        """
        headers = (f.header for f in self._fields)
        self._writer.writerow(headers)

    def write_row(self, item: T):
        """
        Writes a row of data.

        The given ``item`` will be used to generate the data for each column.
        """
        row = []
        for field in self._fields:
            value = field.eval(item, self._row_count)
            value = field.format(value)
            row.append(value)
        self._writer.writerow(row)
        self._row_count += 1

    def write_all(self, items: Iterable[T]):
        """
        Writes all the rows of data. This is equivalent to making repeated
        calls to ``write_row`` with each item .
        """
        for item in items:
            self.write_row(item)

    def _add_to_aggregate(self, field, aggregate_ids):
        for id_ in aggregate_ids:
            self._to_aggregate[id_].append(field)


class _Field(_abc.ABC, Generic[T, V]):
    def __init__(self, header, data_format):
        self.header = header
        self.data_format = data_format
        self.last_row = -1
        self.last_value = None

    def eval(self, item: T, row_number: int) -> V:
        if row_number != self.last_row:
            self.last_row = row_number
            self.last_value = self._eval(item, row_number)
        return self.last_value

    def format(self, value: V) -> str:
        return self.data_format.format(value)

    @_abc.abstractmethod
    def _eval(self, item: T, row_number: int) -> V:
        ...

    @staticmethod
    def normalise_evaluator(evaluator):
        if isinstance(evaluator, str):
            return attrgetter(evaluator)
        return evaluator


class _Simple(_Field):
    def __init__(self, header, evaluator, data_format):
        super().__init__(header, data_format)
        self.evaluator = _Field.normalise_evaluator(evaluator)

    def _eval(self, item: T, row_number: int):
        return self.evaluator(item)


class _Aggregator(_Field):
    def __init__(self, header, evaluator, data_format, to_aggregate):
        super().__init__(header, data_format)
        self.evaluator = _Field.normalise_evaluator(evaluator)
        self.to_aggregate = to_aggregate

    def _eval(self, item: T, row_number: int) -> V:
        values = (field.eval(item, row_number) for field in self.to_aggregate)
        return self.evaluator(values)


class _Counter(_Field):
    def __init__(self, header, start, step):
        super().__init__(header, '{}')
        self.start = start
        self.step = step

    def _eval(self, item: T, row_number: int) -> V:
        return self.start + row_number * self.step


class _Multi(_Field):
    def __init__(self, header, seq_field, idx, data_format):
        super().__init__(header, data_format)
        self.seq_field = seq_field
        self.idx = idx

    def _eval(self, item: T, row_number: int) -> V:
        seq = self.seq_field.eval(item, row_number)
        return seq[self.idx]
