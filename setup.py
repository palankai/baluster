#!/usr/bin/env python
import os

from setuptools import setup, find_packages


def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()


VERSION = '0.2.1'


if __name__ == '__main__':
    setup(
        name='Baluster',
        author='Csaba Palankai',
        author_email='csaba.palankai@gmail.com',
        packages=find_packages(
            'src', exclude=['*.tests', 'tests', '*.tests.*']
        ),
        package_dir={'': 'src'},
        include_package_data=True,
        version=VERSION,
        license='MIT',
        description="Provides hierarchical factory",
        long_description=read('README.rst'),
        url='https://gitlab.com/palankai/baluster',
        classifiers=[
            'Development Status :: 3 - Alpha',
            'Intended Audience :: Developers',
            'License :: OSI Approved :: MIT License',
            'Natural Language :: English',
            'Programming Language :: Python :: 3.6',
            'Operating System :: OS Independent',
        ],
        keywords=('context', 'context manager', 'async',),
        zip_safe=False,
        python_requires='>=3.6',
        install_requires=[],
        setup_requires=['pytest-runner', 'flake8'],
        tests_require=['pytest-asyncio', 'pytest-cov', 'colorama', 'pytest'],
    )
