class BusinessError(Exception):
    """Erro de regra de negócio para operações de domínio."""
    def __init__(self, message: str):
        super().__init__(message)
        self.message = message