# Copyright (c) 2021, VRAI Labs and/or its affiliates. All rights reserved.
#
# This software is licensed under the Apache License, Version 2.0 (the
# "License") as published by the Apache Software Foundation.
#
# You may not use this file except in compliance with the License. You may
# obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.
from datetime import datetime, timezone
from http.cookies import SimpleCookie
from os import environ, kill, remove, scandir
from shutil import rmtree
from signal import SIGTERM
from subprocess import DEVNULL, run
from time import sleep
from typing import Any, Dict, List

from fastapi.testclient import TestClient
from requests.models import Response
from supertokens_python import InputAppInfo, Supertokens, SupertokensConfig
from supertokens_python.process_state import ProcessState
from supertokens_python.recipe.emailpassword import EmailPasswordRecipe
from supertokens_python.recipe.emailverification import EmailVerificationRecipe
from supertokens_python.recipe.jwt import JWTRecipe
from supertokens_python.recipe.passwordless import PasswordlessRecipe
from supertokens_python.recipe.session import SessionRecipe
from supertokens_python.recipe.thirdparty import ThirdPartyRecipe
from supertokens_python.recipe.thirdpartyemailpassword import \
    ThirdPartyEmailPasswordRecipe
from supertokens_python.recipe.thirdpartypasswordless import \
    ThirdPartyPasswordlessRecipe
from supertokens_python.recipe.usermetadata import UserMetadataRecipe
from yaml import FullLoader, dump, load

INSTALLATION_PATH = environ['SUPERTOKENS_PATH']
SUPERTOKENS_PROCESS_DIR = INSTALLATION_PATH + '/.started'
LICENSE_FILE_PATH = INSTALLATION_PATH + '/licenseKey'
CONFIG_YAML_FILE_PATH = INSTALLATION_PATH + '/config.yaml'
ORIGINAL_LICENSE_FILE_PATH = INSTALLATION_PATH + '/temp/licenseKey'
ORIGINAL_CONFIG_YAML_FILE_PATH = INSTALLATION_PATH + '/temp/config.yaml'
WEB_SERVER_TEMP_DIR = INSTALLATION_PATH + '/webserver-temp'
API_VERSION_TEST_NON_SUPPORTED_SV = ['0.0', '1.0', '1.1', '2.1']
API_VERSION_TEST_NON_SUPPORTED_CV = ['0.1', '0.2', '1.2', '2.0', '3.0']
API_VERSION_TEST_MULTIPLE_SUPPORTED_SV = ['0.0', '1.0', '1.1', '2.1']
API_VERSION_TEST_MULTIPLE_SUPPORTED_CV = ['0.1', '0.2', '1.1', '2.1', '3.0']
API_VERSION_TEST_MULTIPLE_SUPPORTED_RESULT = '2.1'
API_VERSION_TEST_SINGLE_SUPPORTED_SV = ['0.0', '1.0', '1.1', '2.0']
API_VERSION_TEST_SINGLE_SUPPORTED_CV = ['0.1', '0.2', '1.1', '2.1', '3.0']
API_VERSION_TEST_SINGLE_SUPPORTED_RESULT = '1.1'
API_VERSION_TEST_BASIC_RESULT = ['2.0', '2.1', '2.2', '2.3', '2.9']
SUPPORTED_CORE_DRIVER_INTERFACE_FILE = './coreDriverInterfaceSupported.json'
TEST_ENABLE_ANTI_CSRF_CONFIG_KEY = 'enable_anti_csrf'
TEST_ACCESS_TOKEN_PATH_VALUE = '/test'
TEST_ACCESS_TOKEN_PATH_CONFIG_KEY = 'access_token_path'
TEST_REFRESH_TOKEN_PATH_KEY_VALUE = '/refresh'
TEST_REFRESH_TOKEN_PATH_KEY_VALUE_TEST_DECORATOR = '/refresh'
TEST_REFRESH_TOKEN_PATH_CONFIG_KEY = 'refresh_api_path'
TEST_SESSION_EXPIRED_STATUS_CODE_VALUE = 401
TEST_SESSION_EXPIRED_STATUS_CODE_CONFIG_KEY = 'session_expired_status_code'
TEST_COOKIE_DOMAIN_VALUE = 'test.supertokens.io'
TEST_COOKIE_DOMAIN_CONFIG_KEY = 'cookie_domain'
TEST_ACCESS_TOKEN_MAX_AGE_VALUE: str = "7200"  # seconds
TEST_ACCESS_TOKEN_MAX_AGE_CONFIG_KEY = 'access_token_validity'
TEST_REFRESH_TOKEN_MAX_AGE_VALUE: str = "720"  # minutes
TEST_REFRESH_TOKEN_MAX_AGE_CONFIG_KEY = 'refresh_token_validity'
TEST_COOKIE_SAME_SITE_VALUE = 'Lax'
TEST_COOKIE_SAME_SITE_CONFIG_KEY = 'cookie_same_site'
TEST_COOKIE_SECURE_VALUE = False
TEST_COOKIE_SECURE_CONFIG_KEY = 'cookie_secure'
TEST_DRIVER_CONFIG_COOKIE_DOMAIN = 'supertokens.io'
TEST_DRIVER_CONFIG_COOKIE_SECURE = False
TEST_DRIVER_CONFIG_COOKIE_SAME_SITE = 'lax'
TEST_DRIVER_CONFIG_ACCESS_TOKEN_PATH = '/'
TEST_DRIVER_CONFIG_REFRESH_TOKEN_PATH = '/auth/session/refresh'
ACCESS_CONTROL_EXPOSE_HEADER = 'Access-Control-Expose-Headers'
ACCESS_CONTROL_EXPOSE_HEADER_ANTI_CSRF_ENABLE = 'front-token, id-refresh-token, anti-csrf'
ACCESS_CONTROL_EXPOSE_HEADER_ANTI_CSRF_DISABLE = 'id-refresh-token'
TEST_ID_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyfQ.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c"


def set_key_value_in_config(key: str, value: str):
    f = open(CONFIG_YAML_FILE_PATH, 'r')
    data = load(f, Loader=FullLoader)
    f.close()
    data[key] = value
    f = open(CONFIG_YAML_FILE_PATH, 'w')
    dump(data, f)
    f.close()


def drop_key(key: str):
    f = open(CONFIG_YAML_FILE_PATH, 'r')
    data = load(f, Loader=FullLoader)
    f.close()
    data.pop(key)
    f = open(CONFIG_YAML_FILE_PATH, 'w')
    dump(data, f)
    f.close()


def __stop_st(retry: int = 50):
    process_ids = __get_list_of_process_ids()
    for pid in process_ids:
        kill(int(pid), SIGTERM)
    process_ids = __get_list_of_process_ids()
    if len(process_ids) != 0:
        if retry == 0:
            raise Exception('')
        sleep(0.5)
        __stop_st(retry - 1)
    sleep(1)


def start_st(host: str = 'localhost', port: str = '3567'):
    pid_after = pid_before = __get_list_of_process_ids()
    run('cd ' + INSTALLATION_PATH + ' && java -Djava.security.egd=file:/dev/urandom -classpath '
                                    '"./core/*:./plugin-interface/*" io.supertokens.Main ./ DEV host='
        + host + ' port=' + str(port) + ' test_mode &', shell=True, stdout=DEVNULL)
    for _ in range(35):
        pid_after = __get_list_of_process_ids()
        if len(pid_after) != len(pid_before):
            break
        sleep(0.5)
    if len(pid_after) == len(pid_before):
        raise Exception('could not start ST process')


def setup_st():
    try:
        run("cd " + INSTALLATION_PATH + " && cp temp/licenseKey ./licenseKey")
    except BaseException:
        run("cd " + INSTALLATION_PATH +
            " && cp temp/config.yaml ./config.yaml", shell=True)


def clean_st():
    try:
        remove(LICENSE_FILE_PATH)
    except FileNotFoundError:
        pass
    try:
        remove(CONFIG_YAML_FILE_PATH)
    except FileNotFoundError:
        pass
    try:
        rmtree(SUPERTOKENS_PROCESS_DIR)
    except FileNotFoundError:
        pass
    try:
        rmtree(WEB_SERVER_TEMP_DIR)
    except FileNotFoundError:
        pass


def __get_list_of_process_ids() -> List[str]:
    process_ids: List[str] = []
    try:
        processes = scandir(SUPERTOKENS_PROCESS_DIR)
        for process in processes:
            f = open(SUPERTOKENS_PROCESS_DIR + '/' + process.name, 'r')
            process_ids.append(f.readline())
            f.close()
    except FileNotFoundError:
        pass
    return process_ids


def reset():
    __stop_st()
    ProcessState.get_instance().reset()
    Supertokens.reset()
    SessionRecipe.reset()
    ThirdPartyEmailPasswordRecipe.reset()
    EmailPasswordRecipe.reset()
    EmailVerificationRecipe.reset()
    ThirdPartyRecipe.reset()
    PasswordlessRecipe.reset()
    JWTRecipe.reset()
    UserMetadataRecipe.reset()
    ThirdPartyPasswordlessRecipe.reset()
    PasswordlessRecipe.reset()


def get_cookie_from_response(response: Response, cookie_name: str):
    cookies = extract_all_cookies(response)
    if cookie_name in cookies:
        return cookies[cookie_name]
    return None


def extract_all_cookies(response: Response) -> Dict[str, Any]:
    if response.headers.get('set-cookie') is None:
        return {}
    cookie_headers = SimpleCookie(  # type: ignore
        response.headers.get('set-cookie'))
    cookies: Dict[str, Any] = {}
    for key, morsel in cookie_headers.items():  # type: ignore
        cookies[key] = {
            'value': morsel.value,
            'name': key
        }
        for k, v in morsel.items():
            if (k in ('secure', 'httponly')) and v == '':
                cookies[key][k] = None
            elif k == 'samesite':
                if len(v) > 0 and v[-1] == ',':
                    v = v[:-1]
                cookies[key][k] = v
            else:
                cookies[key][k] = v
    return cookies


def get_unix_timestamp(expiry: str):
    return int(datetime.strptime(
        expiry, '%a, %d %b %Y %H:%M:%S GMT').replace(tzinfo=timezone.utc).timestamp())


def verify_within_5_second_diff(n1: int, n2: int):
    return -5 <= (n1 - n2) <= 5


def sign_up_request(app: TestClient, email: str, password: str):
    return app.post(
        url="/auth/signup",
        headers={
            "Content-Type": "application/json"
        },
        json={
            'formFields':
                [{
                    "id": "password",
                    "value": password
                },
                    {
                        "id": "email",
                        "value": email
                }]
        })


def sign_in_up_request(app: TestClient, email: str, use_server: bool = False):
    if use_server:
        environ['SUPERTOKENS_ENV'] = 'production'
    response = app.post(
        url="/auth/signinup/code",
        headers={
            "Content-Type": "application/json"
        },
        json={
            "email": email
        })
    if use_server:
        environ['SUPERTOKENS_ENV'] = 'testing'
    return response


def sign_in_up_request_phone(app: TestClient, phone: str, use_server: bool = False):
    if use_server:
        environ['SUPERTOKENS_ENV'] = 'production'
    response = app.post(
        url="/auth/signinup/code",
        headers={
            "Content-Type": "application/json"
        },
        json={
            "phoneNumber": phone
        })
    if use_server:
        environ['SUPERTOKENS_ENV'] = 'testing'
    return response


def reset_password_request(app: TestClient, email: str, use_server: bool = False):
    if use_server:
        environ['SUPERTOKENS_ENV'] = 'production'
    response = app.post(
        url="/auth/user/password/reset/token",
        json={
            'formFields':
                [{
                    "id": "email",
                    "value": email
                }]
        }
    )
    if use_server:
        environ['SUPERTOKENS_ENV'] = 'testing'
    return response


def sign_in_request(app: TestClient, email: str, password: str):
    return app.post(
        url="/auth/signin",
        headers={
            "Content-Type": "application/json"
        },
        json={
            'formFields':
                [{
                    "id": "password",
                    "value": password
                },
                    {
                        "id": "email",
                        "value": email
                }]
        })


def email_verify_token_request(
        app: TestClient, accessToken: str, idRefreshTokenFromCookie: str, antiCsrf: str, userId: str, use_server: bool = False):
    if use_server:
        environ['SUPERTOKENS_ENV'] = 'production'
    headers = {
        "Content-Type": "application/json",
    }
    if antiCsrf:
        headers['anti-csrf'] = antiCsrf

    resp = app.post(
        url="/auth/user/email/verify/token",
        headers=headers,
        cookies={
            'sAccessToken': accessToken,
            'sIdRefreshToken': idRefreshTokenFromCookie,
        },
        data=str.encode(userId))
    if use_server:
        environ['SUPERTOKENS_ENV'] = 'testing'

    return resp


WEBSITE_DOMAIN = "http://localhost:3000"

CLOUD = True
if CLOUD:
    supertokens_config = SupertokensConfig(connection_uri="https://try.supertokens.io")
    app_info = InputAppInfo(
        app_name="Demo app testing",
        api_domain="http://localhost:5000",
        website_domain=WEBSITE_DOMAIN,
        api_base_path="/auth",
        website_base_path="/auth",
    )
else:
    supertokens_config = SupertokensConfig('http://localhost:3567')
    app_info = InputAppInfo(
        app_name="Demo app testing",
        api_domain="https://api.supertokens.io",
        website_domain="https://supertokens.io",
        api_base_path="/auth"
    )

from supertokens_python.ingredients.emaildelivery.services.smtp import (
    EmailDeliverySMTPConfig, SMTPServiceConfig, SMTPServiceConfigFrom)
from supertokens_python.ingredients.emaildelivery.types import \
    EmailDeliveryConfig
from supertokens_python.recipe.emailpassword.emaildelivery.services import \
    SMTPService

email_delivery_smtp_config = EmailDeliverySMTPConfig(
    smtp_settings=SMTPServiceConfig(
        host="smtp.mailtrap.io",
        from_=SMTPServiceConfigFrom("NAME", "EMAIL"),
        password="PASSWORD",
        secure=False,
        port=2525,
    )
)

from supertokens_python.ingredients.smsdelivery.service.twilio import (
    SMSDeliveryTwilioConfig, TwilioServiceConfig)
from supertokens_python.ingredients.smsdelivery.types import SMSDeliveryConfig
from supertokens_python.recipe.passwordless.smsdelivery.services import \
    TwilioService

sms_delivery_twilio_config = SMSDeliveryTwilioConfig(
    twilio_settings=TwilioServiceConfig(
        account_sid="ACCOUNT_SID",
        auth_token="AUTH_TOKEN",
        from_="FROM",
    ),
)

smtp_service = SMTPService(config=email_delivery_smtp_config)

email_delivery_config = EmailDeliveryConfig(service=smtp_service)
