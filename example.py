from giextractor import GoogleImageExtractor

if __name__ == '__main__':
    imageExtractor = GoogleImageExtractor(
        imageQuery='mango fruit', imageCount=200)
    imageExtractor.extract_images()
