from archer.ArcherAuth import ArcherAuth
from archer.restful.RestfulClient import RestfulClient

class Event(RestfulClient):
    def __init__(self, auth: ArcherAuth) -> None:
        super().__init__(auth)
        self.base_url = self.base_url + '/system'
    
    def get_event_action(self, eaid: int = None, erid: int = None,
                         fil: str = None, sel: str = None,
                         top: int = None, skip: int = None,
                         ord: str = None) -> list:
        """
        Retrieves the data driven event action of the specified ID.
        OData actions other than $select only work with erid.

        Parameters
        ----------
        eaid : int, optional
            ID number for specified event action. If provided,
            erid is ignored.
        erid : int, optional
            ID number for specified event rule. If eaid is provided,
            erid is ignored.
        fil : str, optional
            OData $filter action. erid only.
        sel : str, optional
            OData $select action. Both eaid and erid.
        top : str, optional
            OData $top action. erid only.
        skip : str, optional
            OData $skip action. erid only.
        ord : str, optional
            OData $orderby action. erid only.

        Returns
        -------
        list
            List of event action(s).

        Raises
        ------
        RequestError
            If the status code is not 200.
        
        Warns
        ------
        If the some or all of the request is unsuccessful.
        """
        url = f'{self.base_url}/eventaction'
        if eaid:
            url += f'/{eaid}'
        else:
            url += f'/eventrule/{erid}'
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
    
    def get_event_rule(self, erid: int = None, lid: int = None,
                       fil: str = None, sel: str = None,
                       top: int = None, skip: int = None,
                       ord: str = None) -> list:
        """
        Retrieves the data driven event rule by the specified ID.
        OData actions other than $select only work with lid.

        Parameters
        ----------
        erid : int, optional
            ID number for specified event rule. If provided,
            lid is ignored.
        lid : int, optional
            ID number for specified level. If erid is provided,
            lid is ignored.
        fil : str, optional
            OData $filter action. lid only.
        sel : str, optional
            OData $select action. Both erid and lid.
        top : str, optional
            OData $top action. lid only.
        skip : str, optional
            OData $skip action. lid only.
        ord : str, optional
            OData $orderby action. lid only.

        Returns
        -------
        list
            List of event rule(s).

        Raises
        ------
        RequestError
            If the status code is not 200.
        
        Warns
        ------
        If the some or all of the request is unsuccessful.
        """
        url = f'{self.base_url}/eventrule'
        if erid:
            url += f'/{erid}'
        else:
            url += f'/level/{lid}'
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