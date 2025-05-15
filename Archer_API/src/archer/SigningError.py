from archer.RequestError import RequestError

class SigningError(RequestError):
    def __init__(self, status_code: str, error_text: str,
                 *args: object) -> None:
        super().__init__(status_code, error_text, *args)

    def __str__(self) -> str:
        return super.__str__()
    
    def __repr__(self) -> str:
        return super().__repr__()