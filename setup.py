# python setup.py develop
from setuptools import setup
import setuptools


CLASSIFIERS = '''\
License :: CC0 1.0 Universal (CC0 1.0) Public Domain Dedication
Programming Language :: Python :: 3.7
Topic :: Design Methods
Operating System :: Microsoft :: Windows
Operating System :: POSIX
Operating System :: Unix
Operating System :: MacOS
'''

DISTNAME = 'marsDemonstrator'
AUTHOR = 'Mathias Laile'
AUTHOR_EMAIL = 'mathias.laile@tum.de'
DESCRIPTION = 'This package contains the demonstrator for the project mars.'
README = 'This package contains the demonstrator for the project mars.'

VERSION = '0.1.5'
ISRELEASED = True

PYTHON_MIN_VERSION = '3.6'
PYTHON_MAX_VERSION = '3.8'
PYTHON_REQUIRES = f'>={PYTHON_MIN_VERSION}, <= {PYTHON_MAX_VERSION}'

INSTALL_REQUIRES = [
    'numpy>=1.16',
    'pandas',
    'joblib>=0.17.0',
    'gpytorch>=1.2.0',
    'xlrd==1.2.0',
    'xlsxwriter',
    'openpyxl',
]

# PACKAGES = [
#     'marsDemonstrator',
# ]

PACKAGES = setuptools.find_packages()

metadata = dict(
    include_package_data=True,
    name=DISTNAME,
    version=VERSION,
    long_description=README,
    packages=PACKAGES,
    python_requires=PYTHON_REQUIRES,
    install_requires=INSTALL_REQUIRES,
    author=AUTHOR,
    author_email=AUTHOR_EMAIL,
    description=DESCRIPTION,
    classifiers=[CLASSIFIERS],
)


def setup_package() -> None:
    setup(**metadata)


if __name__ == '__main__':
    setup_package()
