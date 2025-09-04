# Custom exceptions for the KMZ Creator application

class InvalidFileExtensionError(Exception):
    """Exception raised for invalid file extensions."""
    def __init__(self, file_extension="Unknown", path="Unknown", supported_extensions=[]):
        self.message = f"Invalid file extension: {file_extension} in file {path}. \nSupported extensions are: {', '.join(supported_extensions)}"
        super().__init__(self.message)


class TranslationError(Exception):
    """Exception raised for errors in the coordinate translation process."""
    def __init__(self, original_exception=None):
        self.message = "An error occurred during coordinate translation."
        if original_exception:
            self.message += f" Original exception: {str(original_exception)}"
        super().__init__(self.message)


class ExtractionError(Exception):
    """Exception raised for errors in the coordinate extraction process."""
    def __init__(self, original_exception=None):
        self.message = "An error occurred during coordinate extraction."
        if original_exception:
            self.message += f" Original exception: {str(original_exception)}"
        super().__init__(self.message)