from archer.ArcherAuth import ArcherAuth
from archer.ArcherClient import ArcherClient

class RestfulClient(ArcherClient):
    def __init__(self, auth: ArcherAuth) -> None:
        super().__init__(auth)
        self.base_url = self.auth.base_url + '/platformapi/core'