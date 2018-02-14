#
# google-image-extractor: Utility to search and download images
#                         from google image search
#
# Author: Sagar R. Jadhav <sagarrjadhav.03@gmail.com>
# Version: 1.0.0b1 (Beta)
#

__author__ = 'Sagar R. Jadhav (sagarrjadhav.03@gmail.com)'
__version__ = '1.0.0b1'
__copyright__ = 'Copyright (c) 2018 Sagar Jadhav'
__license__ = 'MIT'

"""Imports"""

# manipulating and accessing web pages
from selenium import webdriver
from bs4 import BeautifulSoup
from selenium.common.exceptions import ElementNotVisibleException

# downloading images
import requests
import mimetypes
from mimetypes import MimeTypes
from PIL import Image
from io import BytesIO

# multi-processing support
from multiprocessing.dummy import Pool

# miscellaneous
import json
import time
import os
from progressbar import (ProgressBar, Percentage, Bar,
                         AdaptiveETA, FileTransferSpeed)
from humanfriendly import format_timespan
from argparse import ArgumentParser
from termcolor import colored


class GoogleImageExtractor:
    """Utility Class to search and download images from google image search"""

    _chromeOptions = None
    _chromeDriver = None
    _imageURLs = []
    _imageURLsExtractedCount = 0
    WAIT_TIME = 3.0
    _imageQuery = ''
    _imageCount = 0
    _storageFolder = ''
    _destinationFolder = ''
    _imageCounter = 0
    _threadCount = 0
    _downloadProgressBar = None
    __argParser = None

    def __init__(self, imageQuery, imageCount=100, destinationFolder='./', threadCount=4):
        """
        Initializes the GoogleImageExtractor class instance

        Arguments:
            imageQuery {[str]} -- [Image Search Query]
            imageCount {[int]} -- [Count of images that need to be downloaded]
            destinationFolder {[str]} -- [Download Destination Folder]
            threadCount {[int]} -- [Count of Threads, to parallelize download of images]
        """

        self._imageQuery = imageQuery
        self._imageCount = imageCount
        self._destinationFolder = destinationFolder
        self._threadCount = threadCount

        self._initialize_chrome_driver()

    def _initialize_chrome_driver(self):
        """Initializes chrome in headless mode"""

        try:

            print(colored('\n Initializing Headless Chrome...\n', 'yellow'))
            self._initialize_chrome_options()
            self._chromeDriver = webdriver.Chrome(
                chrome_options=self._chromeOptions)

            self._chromeDriver.maximize_window()
            print(colored('\nHeadless Chrome Initialized.', 'green'))

        except Exception as exception:
            print(colored('Error - Driver Initialization: ' + format(exception)), 'red')

    @staticmethod
    def initialize_arg_parser():
        """
        Initializes the option parser with the options -
            -q --image-query {[str]} -- [Image Search Query]
            -n --image-count {[int]} -- [Count of images that need to be downloaded]
            -f --destination-folder {[str]} -- [Download Destination Folder]
            -t --thread-count {[int]} -- [Count of Threads, to parallelize download of images]
        """

        GoogleImageExtractor.__argParser = ArgumentParser(
            description='Utility to search and download images from google')

        # Add the required arguments
        requiredArguments = GoogleImageExtractor.__argParser.add_argument_group(
            'required arguments')
        requiredArguments.add_argument('-q', '--image-query', dest='imageQuery',
                                       type=str, required=True, help='Image Search Query',
                                       metavar='<image_query>')

        # Add the optional arguments
        optionalArguments = GoogleImageExtractor.__argParser.add_argument_group(
            'optional arguments')
        optionalArguments.add_argument('-f', '--destination-folder', dest='destinationFolder',
                                       type=str, help='Download Destination Folder, default is the current folder',
                                       metavar='<destination_folder>', default="./")

        optionalArguments.add_argument('-n', '--image-count', dest='imageCount',
                                       type=int, help='Count of images that neeed to be extracted',
                                       metavar='<image_count>', default=100)

        optionalArguments.add_argument('-t', '--thread-count', dest='threadCount',
                                       type=int, help='Count of threads, to parallelize download of images',
                                       metavar='<thread_count>', default=4)

    def _initialize_chrome_options(self):
        """Initializes options for the chrome driver"""

        self._chromeOptions = webdriver.ChromeOptions()
        self._chromeOptions.add_argument('headless')

    def extract_images(self):
        """
        Searches across Google Image Search with the specified image query and
        downloads the specified count of images
        """

        self._get_image_urls()
        self._create_storage_folder()
        self._download_images()

        # Print the final message specifying the total count of images downloaded
        print(colored('\n\nImages Downloaded: ' +
                      str(self._imageCounter) + ' of ' + str(self._imageCount) + ' in ' +
                      format_timespan(self._downloadProgressBar.data()['total_seconds_elapsed']) + '\n', 'green'))

    @staticmethod
    def interpret_arguments():
        """Interprets the options passed via CLI"""

        return GoogleImageExtractor.__argParser.parse_args()

    def _get_image_urls(self):
        """Retrieves the image URLS corresponding to the image query"""

        print(colored('\nRetrieving Image URLs...', 'yellow'))

        _imageQuery = self._imageQuery.replace(' ', '+')

        self._chromeDriver.get('https://www.google.co.in/search?q=' + _imageQuery +
                               '&newwindow=1&source=lnms&tbm=isch')

        while self._imageURLsExtractedCount <= self._imageCount:
            self._extract_image_urls()
            self._page_scroll_down()

        # Slice the list of image URLs to contain the exact number of image
        # URLs that have been requested
        # self._imageURLs = self._imageURLs[:self._imageCount]

        # Terminate the chrome instance
        self._chromeDriver.close()

        print(colored('Image URLs retrieved.', 'green'))

    def _extract_image_urls(self):
        """Retrieves image URLs from the current page"""

        resultsPage = self._chromeDriver.page_source

        resultsPageSoup = BeautifulSoup(resultsPage, 'html.parser')
        images = resultsPageSoup.find_all('div', class_='rg_meta')
        images = [json.loads(image.contents[0]) for image in images]

        [self._imageURLs.append(image['ou']) for image in images]

        self._imageURLsExtractedCount += len(images)

    def _page_scroll_down(self):
        """Scrolls down to get the next set of images"""

        # Scroll down to request the next set of images
        self._chromeDriver.execute_script(
            'window.scroll(0, document.body.clientHeight)')

        # Wait for the images to load completely
        time.sleep(self.WAIT_TIME)

        # Check if the button - 'Show More Results' is visible
        # If yes, click it and request more messages
        # This step helps is avoiding duplicate image URLS from being captured
        try:
            self._chromeDriver.find_element_by_id('smb').click()
        except ElementNotVisibleException as error:
            pass

    def _download_images(self):
        """
        Downloads the images from the retrieved image URLs and
        stores in the specified destination folder.
        Multiprocessing is being used to minimize the download time
        """

        print('\nDownloading Images for the Query: ' + self._imageQuery)

        try:
            self._initialize_progress_bar()

            # # Initialize and assign work to the threads in the threadpool
            # threadPool = Pool(self._threadCount)
            # threadPool.map(self._download_image, self._imageURLs)

            # threadPool.close()
            # threadPool.join()

            [self._download_image(imageURL) for imageURL in self._imageURLs]

            self._downloadProgressBar.finish()

        except Exception as exception:
            print('Error - Image Download: ' + format(exception))

    def _initialize_progress_bar(self):
        """Initializes the progress bar"""

        widgets = ['Download: ', Percentage(), ' ', Bar(),
                   ' ', AdaptiveETA(), ' ', FileTransferSpeed()]

        self._downloadProgressBar = ProgressBar(
            widgets=widgets, max_value=self._imageCount).start()

    def _download_image(self, imageURL):
        """
        Downloads an image file from the given image URL

        Arguments:
            imageURL {[str]} -- [Image URL]
        """

        # If the required count of images have been download,
        # refrain from downloading the remainder of the images
        if(self._imageCounter >= self._imageCount):
            return

        try:
            imageResponse = requests.get(imageURL)

            # Generate image file name as <_imageQuery>_<_imageCounter>.<extension>
            imageType, imageEncoding = mimetypes.guess_type(imageURL)

            if imageType is not None:
                imageExtension = mimetypes.guess_extension(imageType)
            else:
                imageExtension = mimetypes.guess_extension(
                    imageResponse.headers['Content-Type'])

            imageFileName = self._imageQuery.replace(
                ' ', '_') + '_' + str(self._imageCounter) + imageExtension

            imageFileName = os.path.join(self._storageFolder, imageFileName)

            image = Image.open(BytesIO(imageResponse.content))
            image.save(imageFileName)

            self._imageCounter += 1
            self._downloadProgressBar.update(self._imageCounter)

        except Exception as exception:
            pass

    def _get_image_extension(self, imageURL):
        """
        Extracts the extension from the image URL by getting the last 4 characters of the URL

        Arguments:
            imageURL {[type]} -- [str]

        Returns:
            [type] -- [str]
        """

        index = imageURL.find('.')
        return imageURL[index: index + 4]

    def _create_storage_folder(self):
        '''
            Creates a storage folder using the query name by replacing
            spaces in the query with '_' (underscore)
        '''

        try:
            print(colored('\nCreating Storage Folder...', 'yellow'))
            self._storageFolder = os.path.join(
                self._destinationFolder, self._imageQuery.replace(' ', '_'))

            os.makedirs(self._storageFolder)

            print(colored('Storage Folder - ' +
                          self._storageFolder + ' created.', 'green'))
        except FileExistsError:
            print(colored('Storage Folder - ' +
                          self._storageFolder + ' already exists.', 'yellow'))
        except Exception as exception:
            raise exception


if __name__ == '__main__':
    # Initialize the argument parser and interpret the arguments passed via the CLI
    GoogleImageExtractor.initialize_arg_parser()
    args = GoogleImageExtractor.interpret_arguments()

    # Initialize the GoogleImageExtractor and extract the images
    imageExtractor = GoogleImageExtractor(
        args.imageQuery, args.imageCount, args.destinationFolder, args.threadCount)
    imageExtractor.extract_images()
