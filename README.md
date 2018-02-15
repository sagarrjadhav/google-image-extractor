# google-image-extractor
 
Library to help download images from Google Image Search for various machine learning and image classification tasks.

This library uses web scrapping using selenium to download images from google image search. But the way this library is different from other similar ones is that it utilizes headless chrome to perform this activity, this means that it does not need an UI shell to execute and that it can be used in server environments as well.

 ### Installation
Before installing this library, please make sure to download and install chromedriver (webdriver for chrome).

Please refer - [ChromeDriver - Getting Started](https://sites.google.com/a/chromium.org/chromedriver/getting-started) on steps to install it.

To install the library - 
```python
pip install google-image-extractor
```

### Usage

Python Code - 
```python
from giextractor import GoogleImageExtractor

imageExtractor = GoogleImageExtractor(imageQuery='apple fruit', imageCount=500)
imageExtractor.extract_images()
```

#### Bug Reporting
This library is still in beta and is expected to have bugs.
Please submit a bug report, if you come across any while using this library.

New features to improve this library would be introduced as and when required.
