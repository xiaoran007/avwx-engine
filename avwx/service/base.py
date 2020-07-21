"""
Service base class
"""

# stdlib
from typing import Tuple


class Service:
    """
    Base Service class for fetching reports
    """

    url: str = None
    report_type: str
    _valid_types: Tuple[str] = tuple()

    def __init__(self, report_type: str):
        if self._valid_types:
            if report_type not in self._valid_types:
                raise ValueError(
                    f"{report_type} is not a valid report type for {self.__class__.__name__}"
                )
        self.report_type = report_type

    def fetch(self, station: str = None, timeout: int = 10) -> str:
        """
        Fetches a report string from the service
        """
        raise NotImplementedError()

    async def async_fetch(self, station: str = None, timeout: int = 10) -> str:
        """
        Asynchronously fetch a report string from the service
        """
        raise NotImplementedError()
