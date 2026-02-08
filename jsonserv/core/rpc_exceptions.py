# Обработка собственных оошибок rpc-сервера
from jsonrpc import exceptions


class RPCCustomException(exceptions.Error):
    def __init__(self, message=None, code=None):
        if message is not None:
            self.message = message

        if code is not None:
            self.code = code
