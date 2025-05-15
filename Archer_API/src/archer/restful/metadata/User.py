from archer.ArcherAuth import ArcherAuth
from archer.restful.RestfulClient import RestfulClient

class User(RestfulClient):
    def __init__(self, auth: ArcherAuth) -> None:
        super().__init__(auth)
        self.base_url = self.base_url + '/system'

    def set_status(self, uid: int, active: bool = True) -> bool:
        """
        Change user status by the specified ID.

        Parameters
        ----------
        uid : int
            ID number of specified user.
        active : bool, optional
            Flag indicating if user should be set to active or inactive.

        Returns
        -------
        bool
            If request is successful.

        Raises
        ------
        RequestError
            If the status code is not 200.
        
        Warns
        ------
        If the some or all of the request is unsuccessful.
        """
        if active:
            url = f'{self.base_url}/user/status/active/{uid}'
        else:
            url = f'{self.base_url}/user/status/inactive/{uid}'

        response = self.auth.session.post(url)

        self._check_request(response)

        return self._check_success(response.json())
    
    def manage_membership(self, uid: int, id: int = None,
                          group: bool = False,
                          add: bool = False) -> bool:
        """
        Add to or remove from group or role.

        Parameters
        ----------
        uid : int
            ID number of specified user.
        id : int, optional
            ID number of specified group or role.
        group : bool, optional
            Flag indicating if add/remove is from a group or role.
        add : bool, optional
            Flag indicating if user is being added or removed.

        Returns
        -------
        bool
            If request is successful.

        Raises
        ------
        RequestError
            If the status code is not 200.
        
        Warns
        ------
        If the some or all of the request is unsuccessful.
        """
        json = {
            'UserId': uid,
            'IsAdd': add
        }
        
        if group:
            json['GroupId'] = id
            url = f'{self.base_url}/usergroup'
        else:
            json['RoleId'] = id
            url = f'{self.base_url}/userrole'
            
        response = self.auth.session.put(url, json=json)

        self._check_request(response)

        return self._check_success(response.json())
    
    def change_pass(self, uid: int, pwd: str) -> bool:
        """
        Change user password.

        Parameters
        ----------
        uid : int
            ID number of specified user.
        pwd : str
            New user password.

        Returns
        -------
        bool
            If request is successful.

        Raises
        ------
        RequestError
            If the status code is not 200.
        
        Warns
        ------
        If the some or all of the request is unsuccessful.
        """
        url = f'{self.base_url}/userpassword'
        
        json = {
            'UserId': uid,
            'NewPassword': pwd
        }
            
        response = self.auth.session.put(url, json=json)

        self._check_request(response)

        return self._check_success(response.json())
    
    def create_user(self, fst_nm: str, lst_nm: str, pwd: str,
                    usr_nm: str = None, status: int = None,
                    roles: list = None, lid: int = None) -> bool:
        """
        Create a user.

        Parameters
        ----------
        fst_nm : str
            First name of user.
        lst_nm : str
            Last name of user.
        pwd : str
            Password of user.
        usr_nm : str, optional
            Username of user.
        status : int, optional
            Status of user.
        roles : list, optional
            Roles assigned to user.
        lid : int, optional
            Language ID of user's language.

        Returns
        -------
        bool
            If request is successful.

        Raises
        ------
        RequestError
            If the status code is not 200.
        
        Warns
        ------
        If the some or all of the request is unsuccessful.
        """
        url = f'{self.base_url}/user'

        json = {
            'User': {
                'FirstName': fst_nm,
                'LastName': lst_nm,
                'UserName': usr_nm,
                'AccountStatus': status
            },
            'Roles': roles,
            'LanguageId': lid,
            'Password': pwd
        }

        response = self.auth.session.post(url, json=json)

        self._check_request(response)

        return self._check_success(response.json())
    
    def delete_user(self, uid: int) -> bool:
        """
        Deletes a user in the current Archer instance.

        Parameters
        ----------
        uid : int
            ID of user to delete.

        Returns
        -------
        bool
            If request is successful.

        Raises
        ------
        RequestError
            If the status code is not 200.
        
        Warns
        ------
        If the some or all of the request is unsuccessful.
        """
        url = f'{self.base_url}/user/{uid}'

        response = self.auth.session.delete(url)

        self._check_request(response)

        return self._check_success(response.json())
    
    def get_user(self, uid: int = None, gid: int = None,
                 fil: str = None, sel: str = None,
                 top: int = None, skip: int = None,
                 ord: str = None) -> list:
        """
        Retrieves all users in the current Archer instance.
        OData actions other than $select will not work with uid.

        Parameters
        ----------
        uid : int
            ID of user.
        gid : int, optional
            ID of group.
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
            List of user(s).

        Raises
        ------
        RequestError
            If the status code is not 200.
        
        Warns
        ------
        If the some or all of the request is unsuccessful.
        """
        url = f'{self.base_url}/user'

        if uid:
            url += f'/{uid}'
        elif gid:
            url += f'/group/{gid}'

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
    
    def get_usercontact(self, uid: int = None,
                        fil: str = None, sel: str = None,
                        top: int = None, skip: int = None,
                        ord: str = None) -> list:
        """
        Retrieves all user contacts in the current Archer instance.

        Parameters
        ----------
        uid : int
            ID of user.
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
            List of user contact(s).

        Raises
        ------
        RequestError
            If the status code is not 200.
        
        Warns
        ------
        If the some or all of the request is unsuccessful.
        """
        url = f'{self.base_url}/usercontact'

        if uid:
            url += f'/{uid}'

        params = {
            '$filter': fil,
            '$select': sel,
            '$top': top,
            '$skip': skip,
            '$orderby': ord
        }
        
        response = self.auth.session.get(url, params=params)

        self._check_request(response)

        return self._listify(response)
    
    def get_user_task(self, fil: str = None, top: int = None,
                      skip: int = None) -> list:
        """
        Retrieves all tasks assigned to a user in the current Archer
        instance.

        Parameters
        ----------
        fil : str, optional
            OData $filter action.
        top : str, optional
            OData $top action.
        skip : str, optional
            OData $skip action.

        Returns
        -------
        list
            List of task(s).

        Raises
        ------
        RequestError
            If the status code is not 200.
        
        Warns
        ------
        If the some or all of the request is unsuccessful.
        """
        url = f'{self.base_url}/task'

        params = {
            '$filter': fil,
            '$top': top,
            '$skip': skip,
        }   
        headers = {
            'X-Http-Method-Override': 'GET'
        }
        
        response = self.auth.session.post(url, params=params, headers=headers)

        self._check_request(response)

        return self._listify(response)
    
    def manage_user(self, user: dict = None, **kwargs) -> bool:
        """
        Update a user in the current Archer instance.

        Parameters
        ----------
        param : dict, optional
            User

        Returns
        -------
        bool
            If request is successful.

        Raises
        ------
        RequestError
            If the status code is not 200.
        
        Warns
        ------
        If the some or all of the request is unsuccessful.
        """
        url = f'{self.base_url}/user'

        if not user:
            user = self.get_users(uid=kwargs['Id'])[0]
            user.update(kwargs)

        response = self.auth.session.put(url, json=user)

        self._check_request(response)

        return self._check_success(response.json())