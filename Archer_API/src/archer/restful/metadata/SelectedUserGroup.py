from archer.ArcherAuth import ArcherAuth
from archer.restful.RestfulClient import RestfulClient

class SelectedUserGroup(RestfulClient):
    def __init__(self, auth: ArcherAuth) -> None:
        super().__init__(auth)
        self.base_url = self.base_url + '/system'

    def get_selected_user_group(self, fid: int,
                                fil: str = None, sel: str = None,
                                top: int = None, skip: int = None,
                                ord: str = None) -> list:
        """
        Retrieves a list of selected user groups for the specified
        user group list field ID. This list represents the list of
        available selections of users and groups.

        Parameters
        ----------
        fid : int
            ID of user group list field.
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
            List of selected user group(s).

        Raises
        ------
        RequestError
            If the status code is not 200.
        
        Warns
        ------
        If the some or all of the request is unsuccessful.
        """
        url = f'{self.base_url}/usergroupselection/usergrouplist/{fid}'

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