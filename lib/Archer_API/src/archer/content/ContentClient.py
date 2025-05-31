from requests import Response

from archer.ArcherAuth import ArcherAuth
from archer.ArcherClient import ArcherClient

class ContentClient(ArcherClient):
    def __init__(self, auth: ArcherAuth) -> None:
        super().__init__(auth)
        self.max_records = 1000 # Max records returned per API call.
        self.base_url = self.auth.base_url + '/contentapi'

    def _decrement_top(self, top: int | None, dec: int) -> int | None:
        """
        Helper method to safely decrement top of type int | None.

        Parameters
        ----------
        top : int
            From get_level_metadata().
        dec : int
            Amount to decrement top by.

        Returns
        -------
        int | None
            (top - dec) OR None if top is None
        """
        if top is None:
            return top
        else:
            return top - dec

    def get_endpoints(self) -> list:
        """
        Get Content API endpoints. Will return all of the levels and
        cross-references the user has access to.

        Returns
        -------
        list
            List containing dictionaries with endpoint names and urls.

        Raises
        ------
        RequestError
            If the status code is not 200.
        """
        url = self.base_url
        headers = {'Cache-Control': 'no-cache'}

        response = self.auth.session.get(url, headers = headers)

        self._check_request(response)       

        return response.json()['value']
    
    def get_level_metadata(self, level_alias: str,
                           skip: int = 0, top: int = None,
                           tracking_id: int = None) -> list | dict:
        """
        Query Content API.

        Parameters
        ----------
        level_alias : str
            URL returned by get_endpoints().
        skip : int, optional
            Skip the first n records.
        top : int | None, optional
            Return the top p records. If not specified, will return all
            records. When specified with skip, will skip the first n
            records and return the next p records.
        tracking_id : int | None, optional
            Return the specified record. If specified, top and skip will
            be ignored.

        Returns
        -------
        list | dict
            json value of contents. An empty list may be returned if
            skip exceeds the number of records in a level.

        Raises
        ------
        RequestError
            If the status code is not 200.
        """
        # Developer Note: Max 1000 contents per API call.
        # ?top=all returns: error 400 - Invalid $top Query param
        url = f'{self.base_url}/{level_alias}'
        headers = {'Cache-Control': 'no-cache'}
        params = {'skip': skip}

        if top and top < self.max_records:
            params['top'] = top

        if tracking_id:
            url += f'({tracking_id})'

        response = self.auth.session.get(url, params=params, headers=headers)

        self._check_request(response)
        
        if tracking_id:
            return response.json()

        num_records = len(response.json()['value'])
        if num_records <= self.max_records:
            return response.json()['value']
        else:
            return response.json()['value'] + self.get_level_metadata(
                level_alias=level_alias,
                skip=skip + num_records,
                top=self._decrement_top(top, num_records)
            )
    
    def get_levels_metadata(self, level_aliases: list) -> dict:
        """
        Get level metadata for a list of levels. Will return all records
        in each level.

        Parameters
        ----------
        level_aliases : list
            Level aliases returned by get_endpoints().

        Returns
        -------
        dict
            Dictionary mapping level aliases to data.
        """
        contents = dict.fromkeys(level_aliases)

        for alias in level_aliases:
            contents[alias] = self.get_level_metadata(alias)

        return contents
    
    def get_xref_rel(self, level_alias: str, field_alias: str) -> list:
        """
        Get Cross-References or Related Records for a specified field.

        Parameters
        ----------
        level_aliases : str
            Level aliases returned by get_endpoints().
        field_alias : str
            Alias of field.

        Returns
        -------
        list
            json-formatted list of relationships.

        Raises
        ------
        RequestError
            If the status code is not 200.
        """
        url = f'{self.base_url}/{level_alias}_{field_alias}'
        headers = {'Cache-Control': 'no-cache'}

        response = self.auth.session.get(url, headers=headers)

        self._check_request(response)
        
        return response.json()['value']
    
    def post_content(self, app_alias: str,
                     json: list | dict) -> Response:
        """UNTESTED! DO NOT USE IN PRODUCTION!
        Save content to specified application. 0 in the ID line creates
        a new record; any other content updates an existing record.

        Parameters
        ----------
        app_alias : str
            Alias of application to save content.
        json : Any
            Content to save. Must be serializable.

        Returns
        -------
        requests.Response
            For evaluation by user in the event of a failed post.
        """
        url = f'{self.base_url}/{app_alias}'
        headers = {'Cache-Control': 'no-cache'}

        return self.auth.session.post(url, headers=headers, json=json)