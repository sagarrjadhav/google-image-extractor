from cx_Freeze import setup, Executable

setup(name='google-image-extractor',
      version=1.0,
      description='Utility Class to search and download images from google image search',
      options={'build_exe': {'packages': ['idna']}},
      executables=[Executable('google-image-extractor.py')])
