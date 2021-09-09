import setuptools

with open('README.md', 'r', encoding='utf-8') as fh:
    long_description = fh.read()

setuptools.setup(
    name='list2csv',
    version='1.0.0',
    author='James Finnie-Ansley',
    description='A simple package intended to help write iterables '
                'of objects to CSV files',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/James-Ansley/list2csv',
    classifiers=[
        'Development Status :: 1 - Planning',
        'Topic :: Utilities',
        'Intended Audience :: Developers',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
    packages=setuptools.find_packages(
        where='src',
    ),
    package_dir={'': 'src'},
    python_requires='>=3.8',
    install_requires=[],
)
