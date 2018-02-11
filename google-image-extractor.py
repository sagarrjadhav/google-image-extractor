#
# google-image-extractor: Utility to search and download images
#                         from google image search
#
# Author: Sagar R. Jadhav <sagarrjadhav.03@gmail.com>
# Version: 1.0

from selenium import webdriver
from bs4 import BeautifulSoup
import json
import time
from selenium.common.exceptions import ElementNotVisibleException
import requests
import mimetypes
from PIL import Image
from io import BytesIO
import os
from multiprocessing.dummy import Pool
from progressbar import (ProgressBar, Percentage, Bar,
                         AdaptiveETA, FileTransferSpeed)
from humanfriendly import format_timespan
from argparse import ArgumentParser
from termcolor import colored


class GoogleImageExtractor:
    """Utility Class to search and download images from google image search"""

    chromeOptions = None
    chromeDriver = None
    imageURLs = []
    imageURLsExtractedCount = 0
    WAIT_TIME = 3.0
    imageQuery = ''
    imageCount = 0
    storageFolder = ''
    destinationFolder = ''
    imageCounter = 0
    threadCount = 0
    downloadProgressBar = None
    argParser = None

    def __init__(self, imageQuery, imageCount, destinationFolder, threadCount):
        """
        Initializes the GoogleImageExtractor class instance

        Arguments:
            imageQuery {[str]} -- [Image Search Query]
            imageCount {[int]} -- [Count of images that need to be downloaded]
            destinationFolder {[str]} -- [Download Destination Folder]
            threadCount {[int]} -- [Count of Threads, to parallelize download of images]
        """

        self.imageQuery = imageQuery
        self.imageCount = imageCount
        self.destinationFolder = destinationFolder
        self.threadCount = threadCount

        self._initialize_chrome_driver()

    def _initialize_chrome_driver(self):
        """Initializes chrome in headless mode"""

        try:

            print(colored('\n Initialzing Headless Chrome...\n', 'yellow'))
            self._initialize_chrome_options()
            self.chromeDriver = webdriver.Chrome(
                chrome_options=self.chromeOptions)

            self.chromeDriver.maximize_window()
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

        GoogleImageExtractor.argParser = ArgumentParser(
            description='Utility to search and download images from google')

        # Add the required arguments
        requiredArguments = GoogleImageExtractor.argParser.add_argument_group(
            'required arguments')
        requiredArguments.add_argument("-q", "--image-query", dest="imageQuery",
                                       type=str, required=True, help="Image Search Query",
                                       metavar="<image_query>")

        requiredArguments.add_argument("-f", "--destination-folder", dest="destinationFolder",
                                       type=str, required=True, help="Download Destination Folder",
                                       metavar="<destination_folder>")

        # Add the optional arguments
        optionalArguments = GoogleImageExtractor.argParser.add_argument_group(
            'optional arguments')
        optionalArguments.add_argument("-n", "--image-count", dest="imageCount",
                                       type=int, help="Count of images that neeed to be extracted",
                                       metavar="<image_count>", default=100)

        optionalArguments.add_argument("-t", "--thread-count", dest="threadCount",
                                       type=int, help="Count of threads, to parallelize download of images",
                                       metavar="<thread_count>", default=4)

    def _initialize_chrome_options(self):
        """Initializes options for the chrome driver"""

        self.chromeOptions = webdriver.ChromeOptions()
        self.chromeOptions.add_argument('headless')

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
                      str(self.imageCounter) + ' of ' + str(self.imageCount) + ' in ' +
                      format_timespan(self.downloadProgressBar.data()['total_seconds_elapsed']) + '\n', 'green'))

    @staticmethod
    def interpret_arguments():
        """Interprets the options passed via CLI"""

        return GoogleImageExtractor.argParser.parse_args()

    def _get_image_urls(self):
        """Retrieves the image URLS corresponding to the image query"""

        print(colored('\nRetrieving Image URLs...', 'yellow'))

        imageQuery = self.imageQuery.replace(' ', '+')

        self.chromeDriver.get('https://www.google.co.in/search?q=' + imageQuery +
                              '&newwindow=1&source=lnms&tbm=isch')

        while self.imageURLsExtractedCount <= self.imageCount:
            self._extract_image_urls()
            self._page_scroll_down()

        # Slice the list of image URLs to contain the exact number of image
        # URLs that have been requested
        # self.imageURLs = self.imageURLs[:self.imageCount]

        # Terminate the chrome instance
        self.chromeDriver.close()

        print(colored('Image URLs retrieved.', 'green'))

    def _extract_image_urls(self):
        """Retrieves image URLs from the current page"""

        resultsPage = self.chromeDriver.page_source

        resultsPageSoup = BeautifulSoup(resultsPage, 'html.parser')
        images = resultsPageSoup.find_all('div', class_='rg_meta')
        images = [json.loads(image.contents[0]) for image in images]

        [self.imageURLs.append(image['ou']) for image in images]

        self.imageURLsExtractedCount += len(images)

    def _page_scroll_down(self):
        """Scrolls down to get the next set of images"""

        # Scroll down to request the next set of images
        self.chromeDriver.execute_script(
            'window.scroll(0, document.body.clientHeight)')

        # Wait for the images to load completely
        time.sleep(self.WAIT_TIME)

        # Check if the button - 'Show More Results' is visible
        # If yes, click it and request more messages
        # This step helps is avoiding duplicate image URLS from being captured
        try:
            self.chromeDriver.find_element_by_id('smb').click()
        except ElementNotVisibleException as error:
            pass

    def _download_images(self):
        """
        Downloads the images from the retrieved image URLs and 
        stores in the specified destination folder.
        Multiprocessing is being used to minimize the download time
        """

        print('\nDownloading Images for the Query: ' + self.imageQuery)

        try:
            self._initialize_progress_bar()

            # Initialize and assign work to the threads in the threadpool
            threadPool = Pool(self.threadCount)
            threadPool.map(self._download_image, self.imageURLs)

            threadPool.close()
            threadPool.join()

            self.downloadProgressBar.finish()

        except Exception as exception:
            print('Error - Image Download: ' + format(exception))

    def _initialize_progress_bar(self):
        """Initializes the progress bar"""

        widgets = ['Download: ', Percentage(), ' ', Bar(),
                   ' ', AdaptiveETA(), ' ', FileTransferSpeed()]

        self.downloadProgressBar = ProgressBar(
            widgets=widgets, max_value=self.imageCount).start()

    def _download_image(self, imageURL):
        """
        Downloads an image file from the given image URL

        Arguments:
            imageURL {[str]} -- [Image URL]
        """

        # If the required count of images have been download,
        # refrain from downloading the remainder of the images
        if(self.imageCounter >= self.imageCount):
            return

        try:
            imageResponse = requests.get(imageURL)

            # Generate image file name as <imageQuery>_<imageCounter>.<extension>
            imageExtension = mimetypes.guess_extension(
                imageResponse.headers['Content-Type'])

            imageFileName = self.imageQuery.replace(
                ' ', '_') + '_' + str(self.imageCounter) + imageExtension

            imageFileName = os.path.join(self.storageFolder, imageFileName)

            image = Image.open(BytesIO(imageResponse.content))
            image.save(imageFileName)

            self.imageCounter += 1
            self.downloadProgressBar.update(self.imageCounter)

        except Exception as exception:
            pass

    def _create_storage_folder(self):
        '''
            Creates a storage folder using the query name by replacing 
            spaces in the query with '_' (underscore)
        '''

        try:
            print(colored('\nCreating Storage Folder...', 'yellow'))
            self.storageFolder = os.path.join(
                self.destinationFolder, self.imageQuery.replace(' ', '_'))

            os.makedirs(self.storageFolder)

            print(colored('Storage Folder - ' +
                          self.storageFolder + ' created.', 'green'))
        except FileExistsError:
            print(colored('Storage Folder - ' +
                          self.storageFolder + ' already exists.', 'yellow'))
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
