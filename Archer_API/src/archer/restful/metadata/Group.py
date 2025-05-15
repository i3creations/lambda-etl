from archer.ArcherAuth import ArcherAuth
from archer.restful.RestfulClient import RestfulClient

class Group(RestfulClient):
    def __init__(self, auth: ArcherAuth) -> None:
        super().__init__(auth)
        self.base_url = self.base_url + '/system'

    def manage_group_member(self, gid: int, gmid: int,
                            add: bool = True) -> bool:
        """
        Add or remove a group member.

        Parameters
        ----------
        gid : int
            Group ID. ID of a parent group.
        gmid : int
            Group member ID. ID of a child group.
        add : bool, optional
            If True, adds child group to parent group. Otherwise removes
            child group from parent group.

        Returns
        -------
        bool
            If request was successful.

        Raises
        ------
        RequestError
            If the status code is not 200.
        
        Warns
        ------
        If the some or all of the request is unsuccessful.
        """
        url = f'{self.base_url}/groupmember'
        
        json = {
            'GroupId': gid,
            'GroupMemberId': gmid,
            'IsAdd': add
        }

        response = self.auth.session.put(url, json=json)

        self._check_request(response)

        return self._check_success(response.json())
    
    def manage_group_role(self, gid: int, rid: int,
                          add: bool = True) -> bool:
        """
        Add or remove a group role.

        Parameters
        ----------
        gid : int
            Group ID
        rid : int
            Role ID
        add : bool, optional
            If True, adds group to access role. Otherwise removes
            group from access role.

        Returns
        -------
        bool
            If request was successful.

        Raises
        ------
        RequestError
            If the status code is not 200.
        
        Warns
        ------
        If the some or all of the request is unsuccessful.
        """
        url = f'{self.base_url}/rolegroup'
        
        json = {
            'GroupId': gid,
            'RoleId': rid,
            'IsAdd': add
        }

        response = self.auth.session.put(url, json=json)

        self._check_request(response)

        return self._check_success(response.json())
    
    def create_group(self, name: str, descr: str = None,
                     p_groups: list = None, c_groups: list = None,
                     c_users: list = None) -> bool:
        """
        Create a group.

        Parameters
        ----------
        name : str
            Group Name
        descr : str, optional
            Group Description
        p_groups : list, optional
            Parent Groups. Groups to which the group will be a member of
            upon creation.
        c_groups : list, optional
            Child Groups. Groups which will be members of the group upon
            creation.
        c_users : list, optional
            Child Users. Users which will be members of the group upon
            creation.

        Returns
        -------
        bool
            If request was successful.

        Raises
        ------
        RequestError
            If the status code is not 200.
        
        Warns
        ------
        If the some or all of the request is unsuccessful.
        """
        url = f'{self.base_url}/group'
        
        json = {
            'Group': {
                'Name': name,
                'Description': descr
            },
            'ParentGroups': p_groups,
            'ChildGroups': c_groups,
            'ChildUsers': c_users
        }

        response = self.auth.session.post(url, json=json)

        self._check_request(response)

        return self._check_success(response.json())
    
    def manage_group(self, gid: int, name: str,
                     p_groups: list = None, c_groups: list = None,
                     c_users: list = None) -> bool:
        """
        Update a group.

        Parameters
        ----------
        gid : int
            Group ID
        name : str
            Group Name
        p_groups : list, optional
            Parent Groups. If specified, replaces all parent groups.
        c_groups : list, optional
            Child Groups. If specified, replaces all child groups.
        c_users : list, optional
            Child Users. If specified, replaces all users.

        Returns
        -------
        bool
            If request was successful.

        Raises
        ------
        RequestError
            If the status code is not 200.
        
        Warns
        ------
        If the some or all of the request is unsuccessful.
        """
        url = f'{self.base_url}/group'
        
        json = {
            'Group': {
                'Id': gid,
                'Name': name
            },
            'ParentGroups': p_groups,
            'ChildGroups': c_groups,
            'ChildUsers': c_users
        }

        response = self.auth.session.put(url, json=json)

        self._check_request(response)

        return self._check_success(response.json())
    
    def delete_group(self, gid: int) -> bool:
        """
        Delete a group.

        Parameters
        ----------
        gid : int
            Group ID

        Returns
        -------
        bool
            If request was successful.

        Raises
        ------
        RequestError
            If the status code is not 200.
        
        Warns
        ------
        If the some or all of the request is unsuccessful.
        """
        url = f'{self.base_url}/group/{gid}'

        response = self.auth.session.delete(url)

        self._check_request(response)

        return self._check_success(response.json())
    
    def get_group(self, gid: int = None, uid: int = None,
                  fil: str = None, sel: str = None,
                  top: int = None, skip: int = None,
                  ord: str = None) -> list:
        """
        Retrieves all groups. OData actions other than $select will not
        work with gid.

        Parameters
        ----------
        gid : int, optional
            Group ID. If provided, uid is ignored.
        uid : int, optional
            User ID. If gid is provided, uid is ignored.
        fil : str, optional
            OData $filter action. Does not apply to gid.
        sel : str, optional
            OData $select action. All.
        top : str, optional
            OData $top action. Does not apply to gid.
        skip : str, optional
            OData $skip action. Does not apply to gid.
        ord : str, optional
            OData $orderby action. Does not apply to gid.

        Returns
        -------
        list
            List of groups.

        Raises
        ------
        RequestError
            If the status code is not 200.
        
        Warns
        ------
        If the some or all of the request is unsuccessful.
        """
        url = f'{self.base_url}/group'

        if gid:
            url += f'/{gid}'
        elif uid:
            url += f'/user/{uid}'

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
    
    def get_group_hierarchy(self, fil: str = None, sel: str = None,
                            top: int = None, skip: int = None,
                            ord: str = None) -> list:
        """
        Retrieves the hierarchy for all groups.

        Parameters
        ----------
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
            List containing the group hierarchy.

        Raises
        ------
        RequestError
            If the status code is not 200.
        
        Warns
        ------
        If the some or all of the request is unsuccessful.
        """
        url = f'{self.base_url}/grouphierarchy'
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
    
    def get_group_memberships(self, fil: str = None, sel: str = None,
                              top: int = None, skip: int = None,
                              ord: str = None) -> list:
        """
        Retrieves memberships for all groups.

        Parameters
        ----------
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
            List containing memberships for all groups.

        Raises
        ------
        RequestError
            If the status code is not 200.
        
        Warns
        ------
        If the some or all of the request is unsuccessful.
        """
        url = f'{self.base_url}/groupmembership'
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