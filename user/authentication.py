import jwt
from django.conf import settings
from django.contrib.auth import get_user_model
from django.middleware.csrf import CsrfViewMiddleware
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.authentication import BaseAuthentication


class CSRFCheck(CsrfViewMiddleware):
    def _reject(self, request, reason):
        if reason == "Referer checking failed - no Referer.":
            return None
        return reason if reason else None


class SafeJWTAuthentication(BaseAuthentication):

    def authenticate(self, request):
        print('[+] request cookies: ', end='')
        print(request.COOKIES)
        User = get_user_model()
        authorization_header = request.headers.get('Authorization')
        xcsrf_token = request.headers.get('X-CSRFToken')
        print('[+] csrf token: ', end='')
        print(xcsrf_token)
        if not authorization_header:
            return None
        try:
            access_token = authorization_header.split(' ')[1]
            payload = jwt.decode(access_token, settings.SECRET_KEY, algorithms=['HS256'])
        except jwt.ExpiredSignatureError:
            if xcsrf_token:
                return None
            raise AuthenticationFailed('access token expired!')
        except jwt.InvalidSignatureError or jwt.DecodeError:
            raise AuthenticationFailed('Invalid token!')
        except IndexError:
            raise AuthenticationFailed('Token prefix missing')

        user = User.objects.filter(id=payload['user_id']).first()
        if user is None:
            raise AuthenticationFailed('User not found')
        print('[+] Access token verified')
        self.enforce_csrf(request)
        return user, None

    def enforce_csrf(self, request):
        check = CSRFCheck()
        check.process_request(request)
        reason = check.process_view(request, None, (), {})
        if reason:
            raise AuthenticationFailed('CSRF Failed: %s' % reason)
