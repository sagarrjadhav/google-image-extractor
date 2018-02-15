from giextractor import GoogleImageExtractor

if __name__ == '__main__':
    imageExtractor = GoogleImageExtractor(
        imageQuery='apple fruit', imageCount=200)
    imageExtractor.extract_images()
