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
        self.imageQuery = imageQuery
        self.imageCount = imageCount
        self.destinationFolder = destinationFolder
        self.threadCount = threadCount

        self._initialize_chrome_driver()

    def _initialize_chrome_driver(self):
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
            Initializes the option parser with the options for specifying 
            the query, count, destination folder and the thread count
        """

        GoogleImageExtractor.argParser = ArgumentParser(
            description='Utility to search and download images from google')

        requiredArguments = GoogleImageExtractor.argParser.add_argument_group(
            'required arguments')
        requiredArguments.add_argument("-q", "--image-query", dest="imageQuery",
                                       type=str, required=True, help="Image Search Query",
                                       metavar="<image_query>")

        requiredArguments.add_argument("-f", "--destination-folder", dest="destinationFolder",
                                       type=str, required=True, help="Download Destination Folder",
                                       metavar="<destination_folder>")

        optionalArguments = GoogleImageExtractor.argParser.add_argument_group(
            'optional arguments')
        optionalArguments.add_argument("-n", "--image-count", dest="imageCount",
                                       type=int, help="Count of images that neeed to be extracted",
                                       metavar="<image_count>", default=100)

        optionalArguments.add_argument("-t", "--thread-count", dest="threadCount",
                                       type=int, help="Count of threads",
                                       metavar="<thread_count>", default=4)

    def _initialize_chrome_options(self):
        self.chromeOptions = webdriver.ChromeOptions()
        self.chromeOptions.add_argument('headless')

    def extract_images(self):
        self._get_image_urls()
        self._create_storage_folder()
        self._download_images()

        # Print the final message specifying the total count of images downloaded
        print(colored('\n\nImages Downloaded: ' +
                      str(self.imageCounter) + ' of ' + str(self.imageCount) + ' in ' +
                      format_timespan(self.downloadProgressBar.data()['total_seconds_elapsed']) + '\n', 'green'))

    @staticmethod
    def interpret_arguments():
        """
            Interpret the options passed via CLI
        """

        return GoogleImageExtractor.argParser.parse_args()

    def _get_image_urls(self):

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

        resultsPage = self.chromeDriver.page_source

        resultsPageSoup = BeautifulSoup(resultsPage, 'html.parser')
        images = resultsPageSoup.find_all('div', class_='rg_meta')
        images = [json.loads(image.contents[0]) for image in images]

        [self.imageURLs.append(image['ou']) for image in images]

        self.imageURLsExtractedCount += len(images)

    def _page_scroll_down(self):
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

        print('\nDownloading Images for the Query: ' + self.imageQuery)

        try:
            self._initialize_progress_bar()

            threadPool = Pool(self.threadCount)
            threadPool.map(self._download_image, self.imageURLs)

            threadPool.close()
            threadPool.join()

            self.downloadProgressBar.finish()

        except Exception as exception:
            # print('Error - Image Download: ' + format(exception))
            pass

            # [self._download_image(imageURL) for imageURL in self.imageURLs]

    def _initialize_progress_bar(self):
        widgets = ['Download: ', Percentage(), ' ', Bar(),
                   ' ', AdaptiveETA(), ' ', FileTransferSpeed()]

        self.downloadProgressBar = ProgressBar(
            widgets=widgets, max_value=self.imageCount).start()

    def _download_image(self, imageURL):

        # If the required count of images have been download,
        # refrain from downloading the reminder of the images
        if(self.imageCounter >= self.imageCount):
            return

        try:
            imageResponse = requests.get(imageURL)

            imageExtension = mimetypes.guess_extension(
                imageResponse.headers['Content-Type'])

            imageFileName = self.imageQuery.replace(
                ' ', '_') + '_' + str(self.imageCounter) + imageExtension

            imageFileName = os.path.join(self.storageFolder, imageFileName)

            image = Image.open(BytesIO(imageResponse.content))
            image.save(imageFileName)
            # print('Image: ' + imageFileName + ' downloaded')

            self.imageCounter += 1
            self.downloadProgressBar.update(self.imageCounter)

        except Exception as exception:
            # print('Error - Image Download: ', format(exception))
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
            raise Exception(exception)


if __name__ == '__main__':
    GoogleImageExtractor.initialize_arg_parser()
    args = GoogleImageExtractor.interpret_arguments()

    imageExtractor = GoogleImageExtractor(
        args.imageQuery, args.imageCount, args.destinationFolder, args.threadCount)
    imageExtractor.extract_images()
