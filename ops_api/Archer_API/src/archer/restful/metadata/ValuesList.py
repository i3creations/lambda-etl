from archer.ArcherAuth import ArcherAuth
from archer.restful.RestfulClient import RestfulClient

class ValuesList(RestfulClient):
    def __init__(self, auth: ArcherAuth) -> None:
        super().__init__(auth)
        self.base_url = self.base_url + '/system'

    def get_values_list(self, vlid: int = None, sel: str = None,
                        flat: bool = False, hier: bool = False) -> list:
        """
        Retrieves one of the following:
        - The definition of a values list by its ID.
        - A flat list of all values list values by values list definition ID.
        - A hierarchical list of all values list values by values list definition ID.

        Parameters
        ----------
        vlid : int
            ID of values list or values list definition.
        sel : str, optional
            OData $select action.
        flat : bool, optional
            Flat list flag. If True, get_values_list returns a flat list
            of all values list values.
        heir : bool, optional
            Hierarchical list flag. If True, get_values_list returns a
            hierarchical list of all values list values.

        Returns
        -------
        list
            List of specified values list definition or values list
            value(s).

        Raises
        ------
        RequestError
            If the status code is not 200.
        
        Warns
        ------
        If the some or all of the request is unsuccessful.
        """
        if flat:
            url = f'{self.base_url}/valueslistvalue/flat/valueslist/{vlid}'
        elif hier:
            url = f'{self.base_url}/valueslistvalue/valueslist/{vlid}'
        else:
            url = f'{self.base_url}/valueslist/{vlid}'

        params = {
            '$select': sel,
        }
        headers = {
            'X-Http-Method-Override': 'GET'
        }
        
        response = self.auth.session.post(url, params=params, headers=headers)

        self._check_request(response)

        return self._listify(response)