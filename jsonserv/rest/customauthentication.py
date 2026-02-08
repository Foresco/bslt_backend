# Класс доработанной аутентификации
# Учитывающий особенности хранения сессий в Базальте
from rest_framework import authentication


class CustomAuthentication(authentication.SessionAuthentication):
    def authenticate(self, request):
        print('CustomAuthentication')
        # perform custom authentication logic here
        a = super(CustomAuthentication, self).authenticate(request)
        # return a tuple of (user, auth) or None if authentication fails
        return None
        return a
