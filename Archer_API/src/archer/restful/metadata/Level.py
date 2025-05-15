from archer.ArcherAuth import ArcherAuth
from archer.restful.RestfulClient import RestfulClient

class Level(RestfulClient):
    def __init__(self, auth: ArcherAuth) -> None:
        super().__init__(auth)
        self.base_url = self.base_url + '/system'

    def get_level(self, lid: int = None, mid: int = None, fid: int = None,
                  fil: str = None, sel: str = None,
                  top: int = None, skip: int = None,
                  ord: str = None) -> list:
        """
        Retrieves specified level(s) in the current Archer instance.
        OData actions other than $select will not work with lid.

        Parameters
        ----------
        lid : int, optional
            ID number for specified level. If provided,
            mid & fid are ignored.
        mid : int, optional
            ID number for specified module. If lid is provided,
            mid & fid are ignored.
        fid : int, optional
            ID number for specified field. If lid or mid is provided,
            fid is ignored.
        fil : str, optional
            OData $filter action. Does not apply to lid.
        sel : str, optional
            OData $select action. All.
        top : str, optional
            OData $top action. Does not apply to lid.
        skip : str, optional
            OData $skip action. Does not apply to lid.
        ord : str, optional
            OData $orderby action. Does not apply to lid.

        Returns
        -------
        list
            List of level(s).

        Raises
        ------
        RequestError
            If the status code is not 200.
        
        Warns
        ------
        If the some or all of the request is unsuccessful.
        """
        url = f'{self.base_url}/level'

        if lid:
            url += f'/{lid}'
        elif mid:
            url += f'/module/{mid}'
        elif fid:
            url += f'/referencefield/{fid}'
            
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
    
    def get_level_layout(self, lid: int, sel: str = None) -> list:
        """
        Retrieves specified level layouts in the current Archer
        instance.

        Parameters
        ----------
        lid : int
            Level ID.
        sel : str, optional
            OData $select action.

        Returns
        -------
        list
            List of level layout.

        Raises
        ------
        RequestError
            If the status code is not 200.
        
        Warns
        ------
        If the some or all of the request is unsuccessful.
        """
        url = f'{self.base_url}/levellayout/level/{lid}'
            
        params = {
            '$select': sel
        }   
        headers = {
            'X-Http-Method-Override': 'GET'
        }
        
        response = self.auth.session.post(url, params=params, headers=headers)

        self._check_request(response)

        return self._listify(response)