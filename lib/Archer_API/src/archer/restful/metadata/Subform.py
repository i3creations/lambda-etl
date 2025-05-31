from archer.ArcherAuth import ArcherAuth
from archer.restful.RestfulClient import RestfulClient

class Subform(RestfulClient):
    def __init__(self, auth: ArcherAuth) -> None:
        super().__init__(auth)
        self.base_url = self.base_url + '/system'

    def get_subform(self, sfid: int = None, sel: str = None) -> list:
        """
        Retrieves a subform by the specified ID.

        Parameters
        ----------
        sfid : int
            ID number of specified subform.
        sel : str, optional
            OData $select action.

        Returns
        -------
        list
            List containing the specified subform.

        Raises
        ------
        RequestError
            If the status code is not 200.
        
        Warns
        ------
        If the some or all of the request is unsuccessful.
        """
        url = f'{self.base_url}/subform/{sfid}'

        params = {
            '$select': sel,
        }
        headers = {
            'X-Http-Method-Override': 'GET'
        }
        
        response = self.auth.session.post(url, params=params, headers=headers)

        self._check_request(response)

        return self._listify(response)