from archer.ArcherAuth import ArcherAuth
from archer.ArcherClient import ArcherClient

class WebServicesClient(ArcherClient):
    def __init__(self, auth: ArcherAuth) -> None:
        super().__init__(auth)
        self.page_size = 1000