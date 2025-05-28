from archer.ArcherAuth import ArcherAuth
from archer.restful.RestfulClient import RestfulClient

class Application(RestfulClient):
    def __init__(self, auth: ArcherAuth) -> None:
        super().__init__(auth)
        self.base_url = self.base_url + '/system'

    def get_application_version(self) -> str:
        """
        Get the version number for the Archer instance against which
        the API is running.

        Returns
        -------
        str
            Version Number

        Raises
        ------
        RequestError
            If the status code is not 200.

        Warns
        ------
        If the some or all of the request is unsuccessful.
        """
        url = f'{self.base_url}/applicationinfo/version'
        headers = {
            'X-Http-Method-Override': 'GET'
        }
        
        response = self.auth.session.post(url, headers=headers)

        self._check_request(response)

        self._check_success(response.json())

        return response.json()['RequestedObject']['Version']
    
    def get_application_metadata(self, id: int = None,
                                 fil: str = None, sel: str = None,
                                 top: int = None, skip: int = None,
                                 ord: str = None) -> list:
        """
        Retrieves metadata for all applications. If id is provided, will
        return metadata for the specified application. OData actions
        other than $select only work when id is not provided.

        Parameters
        ----------
        id : int, optional
            ID number for specified application.
        fil : str, optional
            OData $filter action.
        sel : str, optional
            OData $select action.
        top : str, optional
            OData $top action.
        skip : str, optional
            OData $skip action.
        ord : str, optional
            OData $orderby action.

        Returns
        -------
        list
            List of application metadata.

        Raises
        ------
        RequestError
            If the status code is not 200.
        
        Warns
        ------
        If the some or all of the request is unsuccessful.
        """
        url = f'{self.base_url}/application'
        if id:
            url += f'/{id}'
        params = {
            '$filter': fil,
            '$select': sel,
            '$top': top,
            '$skip': skip,
            '$orderby': ord
        }
        headers = {
            'X-Http-Method-Override': 'GET'
        }
        
        response = self.auth.session.post(url, params=params, headers=headers)

        self._check_request(response)

        return self._listify(response)