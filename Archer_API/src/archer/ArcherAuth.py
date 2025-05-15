"""
ArcherAPI.ArcherAuth

This module provides an ArcherAuth class, whose instantiated objects
will hold signed credentials to the specified Archer instance.

In addition to signed credentials, we store the Archer instance url and
session object that will be used by the ArcherClient classes to make
requests.
"""
import re
import requests

# 3.11
# from typing import Self
from typing_extensions import Self

from archer.SigningError import SigningError

class ArcherAuth:
    # Some basic input validation
    def _clean_url(self, url: str) -> str:
        return re.search('(https?:\/\/[^\/]*)', url).group(1)

    def __init__(self, ins: str,
                 usr: str, pwd: str,
                 url: str, dom: str = '') -> None:
        """
        Instantiate an ArcherAuth object.

        Parameters
        ----------
        ins : str 
            Name of Archer instance. (e.g.'Prod', 'Test', etc.)
        usr : str 
            Username of account to authenticate and request against.
        pwd : str
            Password of account to authenticate and request against.
        url : str
            Base url of Archer instance.
            (e.g https://optstest.uscis.dhs.gov)
        dom : str, optional
            Userdomain. Almost always blank.
        """
        self.ins = ins
        self.dom = dom
        self.usr = usr
        self.pwd = pwd
        self.base_url = self._clean_url(url)
        self.token = None
        self.authenticated = False
        self.session = requests.Session()
        self.session.headers.update(
            {'Accept': 'application/json',
             'Content-Type': 'application/json'}
        )
        #TESTING ONLY!!!
        # self.session.verify = False
        #TESTING ONLY!!!

    def login(self) -> None:
        """
        Login to Archer instance with credentials provided during
        instantiation. 
        """
        if not self.authenticated:
            response = self.session.post(
                f'{self.base_url}/platformapi/core/security/login',
                json = {'InstanceName': self.ins,
                        'Username': self.usr,
                        'UserDomain': self.dom,
                        'Password': self.pwd}
            )
        
        if (response.status_code != 200
            or not response.json()['IsSuccessful']):
            # Login was unsucessful.
            raise SigningError(response.status_code, response.text)
        
        self.token = response.json()['RequestedObject']['SessionToken']
        self.session.headers.update(
            {'Authorization': f'Archer session-id={self.token}'}
        )
        self.authenticated = True

    def logout(self) -> None:
        """
        Logout of Archer instance with signed credentials recieved
        during login.
        """
        if self.authenticated:
            response = self.session.post(
                f'{self.base_url}/platformapi/core/security/logout',
                json = {'Value': self.token}
            )

        if (response.status_code != 200
            or not response.json()['IsSuccessful']):
            # Logout was unsucessful.
            raise SigningError(response.status_code, response.text)
        
        self.authenticated = False

    def __enter__(self) -> Self:
        self.login()
        return self

    def __exit__(self, *args, **kwargs) -> bool:
        self.logout()
        self.session.close() # Not sure this is necessary.
        return False