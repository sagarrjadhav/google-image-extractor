from giextractor import GoogleImageExtractor

if __name__ == '__main__':
    imageExtractor = GoogleImageExtractor(imageQuery='mango fruit')
    imageExtractor.extract_images()
