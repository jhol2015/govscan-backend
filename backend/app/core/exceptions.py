class GovScanException(Exception):
    pass

class ScraperException(GovScanException):
    pass

class ProcessorException(GovScanException):
    pass

class PortalNotFoundException(GovScanException):
    pass
