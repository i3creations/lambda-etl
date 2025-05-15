from archer.ArcherAuth import ArcherAuth
from archer.restful.RestfulClient import RestfulClient

class Questionnaire(RestfulClient):
    def __init__(self, auth: ArcherAuth) -> None:
        super().__init__(auth)
        self.base_url = self.base_url + '/system'

    def get_questionnaire(self, qid: int = None,
                          fil: str = None, sel: str = None,
                          top: int = None, skip: int = None,
                          ord: str = None) -> list:
        """
        Retrieves all questionnaires in the current Archer instance.
        OData actions other than $select will not work with qid.

        Parameters
        ----------
        qid : int, optional
            ID number for specified questionnaire.
        fil : str, optional
            OData $filter action. Does not apply to qid.
        sel : str, optional
            OData $select action. All.
        top : str, optional
            OData $top action. Does not apply to qid.
        skip : str, optional
            OData $skip action. Does not apply to qid.
        ord : str, optional
            OData $orderby action. Does not apply to qid.

        Returns
        -------
        list
            List of questionnaire(s).

        Raises
        ------
        RequestError
            If the status code is not 200.
        
        Warns
        ------
        If the some or all of the request is unsuccessful.
        """
        url = f'{self.base_url}/questionnaire'
            
        if qid:
            url += f'/{qid}'

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
    
    def get_questionnaire_rule(self, qrid: int = None, lid: int = None,
                               fil: str = None, sel: str = None,
                               top: int = None, skip: int = None,
                               ord: str = None) -> list:
        """
        Retrieves specified questionnaire rules in the current Archer
        instance. OData actions other than $select will not work with
        qrid.

        Parameters
        ----------
        qrid : int, optional
            ID number for specified questionnaire rule. If provided, lid
            is ignored.
        lid : int, optional
            ID number for specified level. If qrid is provided, lid
            is ignored.
        fil : str, optional
            OData $filter action. Does not apply to qrid.
        sel : str, optional
            OData $select action. All.
        top : str, optional
            OData $top action. Does not apply to qrid.
        skip : str, optional
            OData $skip action. Does not apply to qrid.
        ord : str, optional
            OData $orderby action. Does not apply to qrid.

        Returns
        -------
        list
            List of questionnaire rule(s).

        Raises
        ------
        RequestError
            If the status code is not 200.
        
        Warns
        ------
        If the some or all of the request is unsuccessful.
        """
        url = f'{self.base_url}/questionnairerule'
            
        if qrid:
            url += f'/{qrid}'
        elif lid:
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