# List2CSV

List2CSV is a simple package that helps with writing lists of objects to CSV
files.

## Installation

list2csv can be downloaded from [pypi](https://pypi.org/project/list2csv/) or
installed using pip:

    pip install list2csv

## Usage

List2CSV exposes a `Writer` class that manages CSV columns and writing to a
TextIO stream. Columns are first configured on a `Writer` instance before data
is written in CSV format to the stream.

The following examples will use this `Student` class and list to demonstrate
usage.

```python
from dataclasses import dataclass
from statistics import mean


@dataclass
class Student:
    student_id: str
    test_1_mark: float
    test_2_mark: float
    assignment_marks: list[float]
    lab_marks: list[float]
    comments: list[str]

    @property
    def grade(self):
        return (
                60 * mean((self.test_1_mark, self.test_2_mark))
                + 30 * mean(self.assignment_marks)
                + 10 * mean(self.lab_marks)
        )


students = [
    Student('abcd123',
            78.5, 88,
            [84.5, 96, 87],
            [92.3, 98, 100, 70],
            ['Good', 'Needs work on classes']),
    Student('efgh456',
            62, 74,
            [70.5, 76, 80],
            [98, 68.2, 0, 93.5],
            ['Good', 'Needs work on formatting', 'Needs work on recursion']),
    Student('ijkl789',
            100, 99.5,
            [98.5, 100, 100],
            [100, 100, 98.7, 100],
            ['Excellent']),
]
```

### Adding Columns

The most basic column configuration is to use the `add_column` method to add a
column with a name and a function that returns the value for that column.

Column data can be formatted with an optional format string to specify how data
should be formatted as it is written to the CSV file.

```python
import list2csv

with open('grades.csv') as f:
    writer = list2csv.Writer(f)
    writer.add_column('ID', lambda s: s.student_id)

    writer.write_header()
    writer.write_all(students)
```

Which will produce the following table:

|C1     |
|-------|
|ID     |
|abcd123|
|efgh456|
|ijkl789|

However, instead of a function, `lambda s: s.student_id`, you can also use a
string of the attribute name of the objects being written:

```python
import list2csv

with open('grades.csv') as f:
    writer = list2csv.Writer(f)
    writer.add_column('ID', 'student_id')

    writer.write_header()
    writer.write_all(students)
```

Would produce the same table as before.

Several columns can be added with subsequent calls to `add_column`.

```python
import list2csv

with open('grades.csv', 'w') as f:
    writer = list2csv.Writer(f)
    writer.add_column('ID', 'student_id')
    writer.add_column('Test 1', 'test_1_mark', '{:.2f}')
    writer.add_column('Test 2', 'test_2_mark', '{:.2f}')

    writer.write_header()
    writer.write_all(students)
```

Would produce the following table:

|ID     |Test 1|Test 2|
|-------|------|------|
|abcd123|78.5  |88    |
|efgh456|62    |74    |
|ijkl789|100   |99.5  |

### Counters

Counter columns can be added which increment by a given step value for each row
written to the CSV. Counter columns have a default start value of 1 and a
default step value of 1.

```python
with open('grades.csv', 'w') as f:
    writer = list2csv.Writer(f)
    writer.add_counter('Student Num')
    writer.add_column('ID', 'student_id')
    writer.add_column('Test 1', 'test_1_mark', '{:.2f}')
    writer.add_column('Test 2', 'test_2_mark', '{:.2f}')

    writer.write_header()
    writer.write_all(students)
```

Which would produce the following table:

|Student Num|ID     |Test 1|Test 2|
|-----------|-------|------|------|
|1          |abcd123|78.5  |88    |
|2          |efgh456|62    |74    |
|3          |ijkl789|100   |99.5  |

Any number of counters with separate start and step values can be added to the
same CSV file.

### Multi Columns

It is often desirable to write iterables of data to separate columns of a CSV
file. in such cases, a multi_column can be added to the `Writer` instance.

Multi columns take a `headder_formatter` as opposed to a `header` name. Each
resulting column will be named ``header_template.format(i)``, where ``i`` is the
one-based index of the column.

Multi columns will also need to be defined with the number of columns that will
be added.

```python
with open('grades.csv', 'w') as f:
    writer = list2csv.Writer(f)
    writer.add_counter('Student Num')
    writer.add_column('ID', 'student_id')
    writer.add_column('Test 1', 'test_1_mark', '{:.2f}')
    writer.add_column('Test 2', 'test_2_mark', '{:.2f}')
    writer.add_multi('Assignment {}', 'assignment_marks', 3, '{:.2f}')

    writer.write_header()
    writer.write_all(students)
```

Would produce the following table:

|Student Num|ID     |Test 1|Test 2|Assignment 1|Assignment 2|Assignment 3|
|-----------|-------|------|------|------------|------------|------------|
|1          |abcd123|78.50 |88.00 |84.50       |96.00       |87.00       |
|2          |efgh456|62.00 |74.00 |70.50       |76.00       |80.00       |
|3          |ijkl789|100.00|99.50 |98.50       |100.00      |100.00      |

### Aggregator Columns

Aggregator columns can collate the data from several columns into a single
column. Each column can be added with a set of aggregator IDs. When aggregator
columns are added with an ID, all columns with a matching ID will be aggregated
into a single column using an aggregator function. For example:

```python
with open('grades.csv', 'w') as f:
    writer = list2csv.Writer(f)
    writer.add_counter('Student Num')
    writer.add_column('ID', 'student_id')
    writer.add_column('Test 1', 'test_1_mark', '{:.2f}', {'test'})
    writer.add_column('Test 2', 'test_2_mark', '{:.2f}', {'test'})
    writer.add_aggregator('test', 'Av Test Mark', mean, '{:.2f}')
    writer.add_multi(
        'Assignment {}', 'assignment_marks', 3, '{:.2f}', {'assignment'}
    )
    writer.add_aggregator('assignment', 'Av Assignment Mark', mean, '{:.2f}')

    writer.write_header()
    writer.write_all(students)
```

Would produce the following table:

|Student Num|ID     |Test 1|Test 2|Av Test Mark|Assignment 1|Assignment 2|Assignment 3|Av Assignment Mark|
|-----------|-------|------|------|------------|------------|------------|------------|------------------|
|1          |abcd123|78.50 |88.00 |83.25       |84.50       |96.00       |87.00       |89.17             |
|2          |efgh456|62.00 |74.00 |68.00       |70.50       |76.00       |80.00       |75.50             |
|3          |ijkl789|100.00|99.50 |99.75       |98.50       |100.00      |100.00      |99.50             |

While aggregator columns may be useful for aggregating data from multiple
attributes, in the case of aggregating multi columns it may just be more useful
to add a single column with an aggregating function. For example:

```python
    ...
    writer.add_multi('Assignment {}', 'assignment_marks', 3, '{:.2f}')
    writer.add_column(
        'Av Assignment Mark', lambda s: mean(s.assignment_marks), '{:.2f}'
    )
    ...
```

### Extended Example

```python
with open('grades.csv', 'w') as f:
    writer = list2csv.Writer(f)
    writer.add_counter('Student Num')
    writer.add_column('ID', 'student_id')
    writer.add_column('Test 1', 'test_1_mark', '{:.2f}', {'test'})
    writer.add_column('Test 2', 'test_2_mark', '{:.2f}', {'test'})
    writer.add_aggregator('test', 'Av Test Mark', mean, '{:.2f}')
    writer.add_multi(
        'Assignment {}', 'assignment_marks', 3, '{:.2f}', {'assignment'}
    )
    writer.add_aggregator('assignment', 'Av Assignment Mark', mean, '{:.2f}')
    writer.add_multi('Lab {}', 'lab_marks', 4, '{:.2f}', {'lab'})
    writer.add_aggregator('lab', 'Av. Lab Mark', mean, '{:.2f}')
    writer.add_column('Grade', 'grade', '{:.2f}')
    writer.add_column('Comments', lambda s: '\n'.join(s.comments))

    writer.write_header()
    writer.write_all(students)
```

|Student Num|ID     |Test 1|Test 2|Av Test Mark|Assignment 1|Assignment 2|Assignment 3|Av Assignment Mark|Lab 1 |Lab 2 |Lab 3 |Lab 4 |Av. Lab Mark|Grade  |Comments                                             |
|-----------|-------|------|------|------------|------------|------------|------------|------------------|------|------|------|------|------------|-------|-----------------------------------------------------|
|1          |abcd123|78.50 |88.00 |83.25       |84.50       |96.00       |87.00       |89.17             |92.30 |98.00 |100.00|70.00 |90.08       |8570.75|Good<br>Needs work on classes                           |
|2          |efgh456|62.00 |74.00 |68.00       |70.50       |76.00       |80.00       |75.50             |98.00 |68.20 |0.00  |93.50 |64.92       |6994.25|Good<br>Needs work on formatting<br>Needs work on recursion|
|3          |ijkl789|100.00|99.50 |99.75       |98.50       |100.00      |100.00      |99.50             |100.00|100.00|98.70 |100.00|99.67       |9966.75|Excellent                                            |
