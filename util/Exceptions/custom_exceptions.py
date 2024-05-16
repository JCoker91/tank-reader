'''Custom Exceptions for the project'''


class SimpleError(Exception):
    '''Custom Exception for connections'''
    def __init__(self, message):
        super().__init__(message)


class CriticalError(Exception):
    '''Custom Exception for critical errors'''
    def __init__(self, message):
        super().__init__(message)
