from archer.ArcherAuth import ArcherAuth
from archer.restful.RestfulClient import RestfulClient

class Security(RestfulClient):
    def __init__(self, auth: ArcherAuth) -> None:
        super().__init__(auth)
        self.base_url = self.base_url + '/system'

    def _default_security_parameter(name: str) -> dict:
        """
        Helper function to return a default security parameter.

        Parameters
        ----------
        name : str
            Name of security parameter.

        Returns
        -------
        dict
            Security Parameter
        """
        return {
            'Name': name,
            'Description': '',
            'MinPasswordLength': 9,
            'AlphaCharsRequired': 1,
            'NumericCharsRequired': 1,
            'UppercaseCharsRequired': 1,
            'LowercaseCharsRequired': 1,
            'SpecialCharsRequired': 1,
            'PasswordChangeInterval': 90,
            'PasswordChangeLimit': False,
            'GraceLogins': 3,
            'MaximumFailedLoginAttempts': 3,
            'PreviousPasswordsDisallowed': 10,
            'LockoutPeriod': 999,
            'LockoutPeriodType': 3,
            'SessionTimeout': 10,
            'SessionTimeoutType': 2,
            'StaticSessionTimeout': False,
            'PasswordExpirationNotice': 30,
            'AutomaticAccountDeactivation': 0,
            'IsLimitByTimeFrame': False,
            'PermittedFromTime': '2025-04-01T00:00:00',
            'PermittedToTime': '2025-04-01T00:00:00',
            'IsDisallowedByDays': True,
            'DisallowedSessionDays': [1, 2, 4, 8, 16, 32, 64],
            'IsDisallowedByDates': True,
            'DisallowedDates': [
                {
                    'LockedDate': '2025-04-01T00:00:00'
                }
            ],
            'Default': False,
            'TimeZoneCode': 'Coordinated Universal Time',
            'SecurityParameterType': 2
        }

    def create_security_parameter(self, param: dict = None, **kwargs) -> bool:
        """
        Creates a security parameter in the current Archer instance.

        Parameters
        ----------
        param : dict, optional
            Security Parameter

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
        url = f'{self.base_url}/securityparameter'

        if not param:
            param = self._default_security_parameter(name=kwargs['Name'])
            param.update(kwargs)

        response = self.auth.session.post(url, json=param)

        self._check_request(response)

        return self._check_success(response.json())

    def delete_security_parameter(self, pid: int) -> bool:
        """
        Deletes a security parameter in the current Archer instance.

        Parameters
        ----------
        pid : int
            ID number of parameter to delete.

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
        url = f'{self.base_url}/securityparameter/{pid}'

        response = self.auth.session.delete(url)

        self._check_request(response)

        return self._check_success(response.json())

    def get_security_parameters(self, pid: int = None,
                                fil: str = None, sel: str = None,
                                top: int = None, skip: int = None,
                                ord: str = None) -> list:
        """
        Retrieves all security parameters in the current Archer
        instance. OData actions other than $select will not work with
        pid.

        Parameters
        ----------
        pid : int
            ID of security parameter.
        fil : str, optional
            OData $filter action. Does not apply to pid.
        sel : str, optional
            OData $select action. All.
        top : str, optional
            OData $top action. Does not apply to pid.
        skip : str, optional
            OData $skip action. Does not apply to pid.
        ord : str, optional
            OData $orderby action. Does not apply to pid.

        Returns
        -------
        list
            List of security parameter(s).

        Raises
        ------
        RequestError
            If the status code is not 200.
        
        Warns
        ------
        If the some or all of the request is unsuccessful.
        """
        url = f'{self.base_url}/securityparameter'
            
        if pid:
            url += f'/{pid}'

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
    
    def manage_security_parameter(self, param: dict = None, **kwargs) -> bool:
        """
        Update a security parameter in the current Archer instance.

        Parameters
        ----------
        param : dict, optional
            Security Parameter

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
        url = f'{self.base_url}/securityparameter'

        if not param:
            param = self.get_security_parameters(pid=kwargs['Id'])[0]
            param.update(kwargs)

        response = self.auth.session.put(url, json=param)

        self._check_request(response)

        return self._check_success(response.json())