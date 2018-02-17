"""
A setuptools based setup module.
"""

from setuptools import setup, find_packages
from codecs import open
from os import path

here = path.abspath(path.dirname(__file__))

setup(
    name='google-image-extractor',
    version='1.0.3b1',
    description='Utility to search and download images from google image search',
    long_description='Library to help download images from Google Image Search for various machine learning and image classification tasks.' +
                     'This library uses web scrapping using selenium to download images from google image search.' +
                     'But the way this library is different from other similar ones is that it utilizes headless chrome to perform this activity,' +
                     'this means that it does not need an UI shell to execute and that it can be used in server environments as well.',
    url='https://github.com/Stryker0301/google-image-extractor',
    author='Sagar R. Jadhav',
    author_email='sagarrjadhav.03@gmail.com',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Libraries',
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
