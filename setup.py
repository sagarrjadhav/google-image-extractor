"""
A setuptools based setup module.
"""

from setuptools import setup, find_packages
from codecs import open
from os import path

here = path.abspath(path.dirname(__file__))

setup(
    name='google-image-extractor',
    version='1.0.1b1',
    description='Utility to search and download images from google image search',
    long_description='Utility to search and download images from google image search',
    url='https://github.com/Stryker0301/google-image-extractor',
    author='Sagar R. Jadhav',
    author_email='sagarrjadhav.03@gmail.com',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Build Tools',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3.6',
    ],

    keywords='google image download extractor',
    packages=find_packages(exclude=['contrib', 'docs', 'tests']),
    py_modules=['giextractor'],
    install_requires=['selenium', 'bs4', 'requests',
                      'termcolor', 'progressbar2', 'pillow', 'humanfriendly'],
    # entry_points={  # Optional
    #     'console_scripts': [
    #         'sample=sample:main',
    #     ],
    # },
)
