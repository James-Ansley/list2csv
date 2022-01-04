from typing import TypeVar, Union, Callable, Any, Iterable, Generic, TextIO

_T = TypeVar('_T')
_V = TypeVar('_V')

_eval_func = Union[Callable[[_T], Any], str]
_multi_eval_func = Union[Callable[[_T], Iterable], str]
_aggregate_func = Callable[[Iterable[_T]], Any]


class Writer(Generic[_T]):
    def __init__(self, f: TextIO): ...
    def add_column(self,
                   header: str,
                   evaluator: _eval_func,
                   data_format: str = '{}',
                   aggregate_ids: set = ...): ...
    def add_aggregator(self,
                       aggregate_id: Any,
                       header: str,
                       aggregate_evaluator: _aggregate_func,
                       data_format: str = '{}',
                       aggregate_ids: set = ...): ...
    def add_counter(self,
                    header: str,
                    start: int = 1,
                    step: int = 1,
                    aggregate_ids: set = ...): ...
    def add_multi(self,
                  header_template: str,
                  evaluator: _multi_eval_func,
                  num_items: int,
                  data_format: str = '{}',
                  aggregate_ids: set = ...): ...
    def write_header(self): ...
    def write_row(self, item: _T): ...
    def write_all(self, items: Iterable[_T]): ...
