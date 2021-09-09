# List2CSV

List2CSV is a simple package that helps with writing lists of objects to CSV files.

The main class `Writer` takes a writable file as a parameter and can have various fields added with format specifiers.
Fields can either be instance attribute names or functions that map an object to some value.
For example:

```python
from dataclasses import dataclass
from statistics import mean
from list2csv import Writer

@dataclass
class Student:
    student_id: str
    test_mark: float
    lab_marks: list[float]


students = [
    Student('abcd123', 78.5, [92.3, 98, 100, 70]),
    Student('efgh456', 62, [98, 68.2, 0, 93.5]),
    Student('ijkl789', 100, [100, 100, 98.7, 100]),
]

with open('student_overview.csv', 'w') as f:
    writer = Writer(f)
    writer.add_field('ID', 'student_id')
    writer.add_field('Test Mark', 'test_mark', '{:.2f}')
    writer.add_field('Average Lab Mark', lambda s: mean(s.lab_marks), '{:.2f}')

    writer.write_header()
    writer.write_all(students)
```

Would produce the following table:

|ID     |Test Mark|Average Lab Mark|
|-------|---------|----------------|
|abcd123|78.50    |90.08           |
|efgh456|62.00    |64.92           |
|ijkl789|100.00   |99.67           |
