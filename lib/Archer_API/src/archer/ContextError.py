class ContextError(Exception):
  def __init__(self,
               error_text: str,
               *args: object) -> None:
    self.error_text = error_text
    super().__init__(*args)

  def __str__(self) -> str:
     return self.error_text

  def __repr__(self) -> str:
    return super().__repr__()