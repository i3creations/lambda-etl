from archer.ArcherAuth import ArcherAuth
from archer.restful.RestfulClient import RestfulClient

class Content(RestfulClient):
    def __init__(self, auth: ArcherAuth) -> None:
        super().__init__(auth)
        self.base_url = self.base_url + '/content'

    def get_content(self, cid: int | list  = None,
                    fid: int | list  = None,
                    fil: str = None, sel: str = None,
                    top: int = None, skip: int = None,
                    ord: str = None) -> list:
        """
        Get Content (RESTfulAPI).

        Parameters
        ----------
        cid : int | list, optional
            Content ID. If int, fid is ignored and contentid endpoint is
            queried. If list, fid must also be list and fieldcontent
            endpoint is queried. If None, fid must be int.
        fid : int | list, optional
            Field ID. Ignored if cid is int. If cid and fid is list,
            fieldcontent endpoint is queried. Otherwise,
            referencefieldid endpoint is queried.
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
        dict | list
            json value of content(s).

        Raises
        ------
        RequestError
            If the status code is not 200.

        Warns
        ------
        If the some or all of the request is unsuccessful.
        """
        url = self.base_url
        json = {}
        params = {
            '$filter': fil,
            '$select': sel,
            '$top': top,
            '$skip': skip,
            '$orderby': ord
        }
        headers = {}

        if cid:
            if isinstance(cid, list):
                url += '/fieldcontent'
                json['ContentIds'] = cid
                json['FieldIds'] = fid
            else:
                url += '/contentid'
                params['id'] = cid
                headers['X-Http-Method-Override'] = 'GET'
        else:
            url += '/referencefield/referencefieldid'
            params['id'] = fid
            headers['X-Http-Method-Override'] = 'GET'
        
        response = self.auth.session.post(url, json=json, params=params,
                                          headers=headers)
        
        self._check_request(response)

        return self._listify(response)
    
    def expose_history_logs(self, id: int) -> list:
        """
        Get history log data.

        Parameters
        ----------
        id : int
            Tracking ID of record to query for history log data.

        Returns
        -------
        list
            json value of history logs.

        Raises
        ------
        RequestError
            If the status code is not 200.

        Warns
        ------
        If the some or all of the request is unsuccessful.
        """
        url = f'{self.base_url}/history/{id}'
        headers = {
            'X-Http-Method-Override': 'GET'
        }
    
        response = self.auth.session.post(url, headers = headers)

        self._check_request(response)

        return self._listify(response)
    
    def post_content(self, json: list | dict) -> int | list:
        """UNTESTED! DO NOT USE IN PRODUCTION!
        Saves a content record.

        Attempting to update an existing content record results in a
        403 - Forbidden error.

        Parameters
        ----------
        json : Any
            Content to save. Must be serializable.

        Returns
        -------
        int | list
            If successful, the Content ID of the record saved.
            If unsuccessful, a list containing validation records.

        Raises
        ------
        RequestError
            If the status code is not 200.
        """
        url = self.base_url

        response = self.auth.session.post(url, json=json)

        self._check_request(response)
        
        return response.json()['RequestedObject']['Id']

        
    def put_content(self, json: list | dict) -> int | list:
        """UNTESTED! DO NOT USE IN PRODUCTION!
        Updates a content record.

        Attempting to insert a new content record results in a
        403 - Forbidden error.

        Parameters
        ----------
        json : Any
            Content to update. Must be serializable.

        Returns
        -------
        int | list
            If successful, the Content ID of the record updated.
            If unsuccessful, a list containing validation records.

        Raises
        ------
        RequestError
            If the status code is not 200.
        """
        url = self.base_url

        response = self.auth.session.put(url, json=json)

        self._check_request(response)
        
        return response.json()['RequestedObject']['Id']
        
    def data_gateway(self, cpids: list, efids: list) -> bool:
        """UNTESTED! DO NOT USE IN PRODUCTION!
        Notify Archer when content changes.

        Parameters
        ----------
        cpids : list
            One or more ID(s) that correspond to the Archer Content
            ID(s).
        efids : list
            One or more ID(s) that correspond to a external data
            storage application.

        Returns
        -------
        bool
            Value representing if call is successful.

        Raises
        ------
        RequestError
            If the status code is not 200.
        """
        url = f'{self.base_url}/externalContentChangeNotification'
        headers = {
            'X-Http-Method-Override': 'GET'
        }
        json = {
            'Alias': 'ARCHER',
            'ContentPartIds': cpids,
            'ExternalFieldIds': efids
        }

        response = self.auth.session.post(url, json=json, headers=headers)

        self._check_request(response)

        return response.json()['IsSuccessful']
    
    def get_attachment(self, aid: int) -> dict:
        """
        Retrieve an attachment from the Archer file repository.

        Parameters
        ----------
        aid : int
            Attachment ID

        Returns
        -------
        dict
            Dictionary containing attachment name and attachment bytes
            as a Base64 encoded string.

        Raises
        ------
        RequestError
            If the status code is not 200.

        Warns
        ------
        If the some or all of the request is unsuccessful.
        """
        url = f'{self.base_url}/attachment/{aid}'
        headers = {
            'X-Http-Method-Override': 'GET'
        }
        
        response = self.auth.session.post(url, headers=headers)

        self._check_request(response)

        self._check_success(response.json())

        return response.json()['RequestedObject']
    
    def post_attachment(self, name: str, bytes: str,
                        sen: bool = False) -> bool:
        """UNTESTED! DO NOT USE IN PRODUCTION!
        Post an attachment to the Archer file repository.

        Parameters
        ----------
        name : str
            Name of attachment.
        bytes : str
            Attachment as a Base64 encoded string.
        sen : bool, optional
            Sensitive attachment flag. If true, attachment is stored in
            the encrypted folder.

        Returns
        -------
        bool
            If request was successful.

        Raises
        ------
        RequestError
            If the status code is not 200.
        """
        url = f'{self.base_url}/attachment'
        json = {
            'AttachmentName': name,
            'AttachmentBytes': bytes,
            'IsSensitive': sen
        }

        response = self.auth.session.post(url, json=json)

        self._check_request(response)
        
        return self._check_success(response)
    
    def post_multipart_attachment(self, boundary: str, aname: str,
                                  fname: str, bytes: str, ctype: str,
                                  sen: bool = False) -> bool:
        """UNTESTED! DO NOT USE IN PRODUCTION!
        Post a multipart attachment to the Archer file repository.

        Parameters
        ----------
        boundary : str
            Boundary used in multipart request body.
        aname : str
            Name of attachment.
        fname : str
            Name of file.
        bytes : str
            Attachment as a Base64 encoded string.
        ctype : str
            Type of content.
        sen : bool, optional
            Sensitive attachment flag. If true, attachment is stored in
            the encrypted folder.

        Returns
        -------
        bool
            If request was successful.

        Raises
        ------
        RequestError
            If the status code is not 200.
        """
        url = f'{self.base_url}/multipartattachment'
        headers = {
            'Content-Type': f'multipart/form-data; boundary={boundary}'
        }
        data = (f'{boundary}Content-Disposition: form-data; '
                f'name="AttachmentName"{aname}{boundary}'
                f'Content-Disposition: form-data; '
                f'name="IsSensitive" {sen}{boundary}'
                f'Content-Disposition: form-data; '
                f'name="AttachmentBytes"; '
                f'filename="{fname}"Content-Type: {ctype}'
                f'{bytes}{boundary}')
        
        response = self.auth.session.post(url, data=data, headers=headers)

        self._check_request(response)

        return self._check_success(response)