from giextractor import GoogleImageExtractor

if __name__ == '__main__':
    imageExtractor = GoogleImageExtractor()
    imageExtractor.extract_images(
        imageQuery='apple fruit', imageCount=10000, destinationFolder='./images/', threadCount=10)
    imageExtractor.extract_images(
        imageQuery='grapes', imageCount=10000, destinationFolder='./images/', threadCount=10)
    imageExtractor.extract_images(
        imageQuery='banana', imageCount=10000, destinationFolder='./images/', threadCount=10)
    imageExtractor.extract_images(
        imageQuery='mango', imageCount=10000, destinationFolder='./images/', threadCount=10)
