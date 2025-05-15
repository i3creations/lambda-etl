class RequestError(Exception):
    def __init__(self, status_code: str, error_text: str,
                 *args: object) -> None:
        self.status_code = status_code
        self.error_text = error_text
        super().__init__(*args)

    def __str__(self) -> str:
        return f'{self.status_code} - {self.error_text}'

    def __repr__(self) -> str:
        return super().__repr__()