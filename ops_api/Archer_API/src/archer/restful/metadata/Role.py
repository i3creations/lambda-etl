from archer.ArcherAuth import ArcherAuth
from archer.restful.RestfulClient import RestfulClient

class Role(RestfulClient):
    def __init__(self, auth: ArcherAuth) -> None:
        super().__init__(auth)
        self.base_url = self.base_url + '/system'

    def create_role(self, name: str, descr: str = None, default: bool = False,
                    group_ids: list = None, role_tasks: list = None) -> bool:
        """
        Creates a role in the current Archer instance.

        Parameters
        ----------
        name : str
            Name of role.
        descr : str, optional
            Description of role.
        default : bool, optional
            Default role flag.
        group_ids : list, optional
            Groups assigned to this role.
        role_tasks : list, optional
            Access role tasks associated with this role.

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
        url = f'{self.base_url}/role'
        
        json = {
            'AccessRole': {
                'Name': name,
                'Description': descr,
                'IsDefault': default
            },
            'GroupIds': group_ids,
            'AccessRoleTasks': role_tasks
        }

        response = self.auth.session.post(url, json=json)

        self._check_request(response)

        return self._check_success(response.json())
    
    def delete_role(self, rid: int) -> bool:
        """
        Deletes a role in the current Archer instance.

        Parameters
        ----------
        rid : int
            ID of role to delete.

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
        url = f'{self.base_url}/role/{rid}'

        response = self.auth.session.delete(url)

        self._check_request(response)

        return self._check_success(response.json())
    
    def get_role(self, uid: int = None,
                 fil: str = None, sel: str = None,
                 top: int = None, skip: int = None,
                 ord: str = None) -> list:
        """
        Retrieves all access roles in the current Archer instance.

        Parameters
        ----------
        uid : int
            ID of user for which to get roles.
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
            List of access role(s).

        Raises
        ------
        RequestError
            If the status code is not 200.
        
        Warns
        ------
        If the some or all of the request is unsuccessful.
        """
        url = f'{self.base_url}/role'
            
        if uid:
            url += f'/user/{uid}'

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
    
    def get_role_membership(self, fil: str = None, sel: str = None,
                            top: int = None, skip: int = None,
                            ord: str = None) -> list:
        """
        Retrieves memberships for all roles in the current Archer
        instance. Membership includes all users and all groups for a
        role.

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
            List of membership(s).

        Raises
        ------
        RequestError
            If the status code is not 200.
        
        Warns
        ------
        If the some or all of the request is unsuccessful.
        """
        url = f'{self.base_url}/rolememberships'
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
    
    def manage_role(self, rid: int, name: str, alias: str,
                    descr: str = None, default: bool = False,
                    group_ids: list = None, role_tasks: list = None) -> bool:
        """
        Update an access role in the current Archer instance.

        Parameters
        ----------
        rid : int
            ID of role to update.
        name : str
            Name of role to update.
        alias : str
            alias of role to update.
        descr : str, optional
            Description of role.
        default : bool, optional
            Default role flag.
        group_ids : list, optional
            Groups assigned to this role.
        role_tasks : list, optional
            Access role tasks associated with this role.

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
        url = f'{self.base_url}/role'
        
        json = {
            'AccessRole': {
                'Id': rid,
                'Name': name,
                'Description': descr,
                'IsDefault': default,
                'Alias': alias
            },
            'GroupIds': group_ids,
            'AccessRoleTasks': role_tasks
        }

        response = self.auth.session.put(url, json=json)

        self._check_request(response)

        return self._check_success(response.json())
    
    def create_role_task(self, tid: int,
                         create: bool = False, read: bool = False,
                         update: bool = False, delete: bool = False) -> dict:
        """
        Helper function to create a role task. Use with create_role or
        manage_role.

        Parameters
        ----------
        tid : int
            Task ID
        create : bool, optional
            Name of role to update.
        read : bool, optional
            alias of role to update.
        update : bool, optional
            Description of role.
        delete : bool, optional
            Default role flag.

        Returns
        -------
        dict
            Role Task
        """
        return {
            'TaskId': tid,
            'HasCreate': create,
            'HasRead': read,
            'HasUpdate': update,
            'HasDelete': delete
        }