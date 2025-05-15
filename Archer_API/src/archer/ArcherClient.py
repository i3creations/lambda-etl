import requests
import warnings

from archer.ArcherAuth import ArcherAuth
from archer.RequestError import RequestError

class ArcherClient:
    """
    ArcherAPI.ArcherClient

    Base class to be extended by the following subclasses for each
    Archer API.
    - ContentClient
    - RestfulClient
    - WebServicesClient
    """
    def __init__(self, auth: ArcherAuth) -> None:
        self.auth = auth

    def _check_request(self, resp: requests.Response) -> None:
        """
        Check for a successful status code.

        Parameters
        ----------
        resp : requests.Response
            Response from API call.

        Returns
        -------
        None

        Raises
        ------
        RequestError
            If the status code is not 200.
        """
        if resp.status_code != 200:
            raise RequestError(resp.status_code, resp.text)

    def _check_success(self, obj: dict) -> bool:
        """
        Check for a successful request.

        Parameters
        ----------
        obj : dict
            Object returned by API call.

        Returns
        -------
        bool
            Flag indicating success or failure.

        Warns
        ------
        If the some or all of the request is unsuccessful.
        """
        if not obj['IsSuccessful']:
            warnings.warn('Unsuccessful API Request: '
                          f'{obj["ValidationMessages"]}', Warning)
            
        return obj['IsSuccessful']
    
    def _listify(self, resp: requests.Response) -> list:
        """
        Helper function to remove everything from an API response except
        relevant data.

        Parameters
        ----------
        resp : requests.Response
            Response from API call.

        Returns
        -------
        list
            List of requested objects.

        Warns
        ------
        If the some or all of the request is unsuccessful.
        """
        objects = resp.json()
        if(isinstance(objects, dict)):
            objects = [objects]

        return [
            obj['RequestedObject']
            for obj in objects
            if self._check_success(obj)
        ]