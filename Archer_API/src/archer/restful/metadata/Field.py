from archer.ArcherAuth import ArcherAuth
from archer.restful.RestfulClient import RestfulClient

class Field(RestfulClient):
    def __init__(self, auth: ArcherAuth) -> None:
        super().__init__(auth)
        self.base_url = self.base_url + '/system'
    
    def get_field_defn(self, aid: int = None, fdid: int = None,
                       lid: int = None, vl: bool = False,
                       fil: str = None, sel: str = None,
                       top: int = None, skip: int = None,
                       ord: str = None) -> list:
        """
        Retrieves field definition for an ID in the current Archer
        instance. OData actions other than $select only work with aid &
        lid.

        Parameters
        ----------
        aid : int, optional
            Application ID. If provided, fdid & lid are ignored.
        fdid : int, optional
            Field definition ID. If aid is provided, fdid & lid are
            ignored.
        lid : int, optional
            Level ID. If aid or fdid is provided, lid is ignored.
        vl : bool, optional
            Values list. Flag indicating if filtering by properties
            specific to ValuesListFieldDefinition is allowed. 
        fil : str, optional
            OData $filter action. aid & lid only.
        sel : str, optional
            OData $select action. All.
        top : str, optional
            OData $top action. aid & lid only.
        skip : str, optional
            OData $skip action. aid & lid only.
        ord : str, optional
            OData $orderby action. aid & lid only.

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
        url = f'{self.base_url}/fielddefinition'
        if aid:
            url += f'/application/{aid}'
        elif fdid:
            url += f'/{fdid}'
        elif vl:
            url += f'/level/{lid}/valueslist'
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
        
        if aid:
            response = self.auth.session.get(url, params=params)
        else:
            response = self.auth.session.post(
                url,
                params=params,
                headers=headers
            )

        self._check_request(response)

        return self._listify(response)
    
    def get_field_disp(self, lid: int = None, fil: str = None,
                       sel: str = None, top: int = None,
                       skip: int = None, ord: str = None) -> list:
        """
        Retrieves field displays for the level by the specified level
        ID.

        Parameters
        ----------
        lid : int, optional
            Level ID.
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
        url = f'{self.base_url}/fielddisplay/level/{lid}'
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
    
    def get_field_ids(self, lid: int = None) -> list:
        """
        Retrieves a list of the field definitions that are referenced by
        an Event Rule filter on the specified level.

        Parameters
        ----------
        lid : int, optional
            Level ID.

        Returns
        -------
        list
            List of field definitions.

        Raises
        ------
        RequestError
            If the status code is not 200.
        
        Warns
        ------
        If the some or all of the request is unsuccessful.
        """
        url = f'{self.base_url}/field/eventrulefilter/level/{lid}'
        
        response = self.auth.session.get(url)

        self._check_request(response)

        return self._listify(response)