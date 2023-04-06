import zipfile


def unzip(file: str, path: str):
    with zipfile.ZipFile(file) as zip_file:
        zip_file.extractall(path)
