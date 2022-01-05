import setuptools

with open('README.md', 'r', encoding='utf-8') as fh:
    long_description = fh.read()

setuptools.setup(
    name='list2csv',
    version='1.3.6',
    author='James Finnie-Ansley',
    description='A simple package intended to help write iterables '
                'of objects to CSV files',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/James-Ansley/list2csv',
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Topic :: Utilities',
        'Intended Audience :: Developers',
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
    package_dir={'': 'src'},
    packages=setuptools.find_packages(
        where='src',
    ),
    package_data={'': ['*.pyi']},
    python_requires='>=3.6',
    install_requires=[],
)
