"""
Copyright (c) 2021, VRAI Labs and/or its affiliates. All rights reserved.

This software is licensed under the Apache License, Version 2.0 (the
"License") as published by the Apache Software Foundation.

You may not use this file except in compliance with the License. You may
obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
License for the specific language governing permissions and limitations
under the License.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Union, TYPE_CHECKING, Literal, List

from .provider import Provider

if TYPE_CHECKING:
    from ..framework import BaseRequest, BaseResponse
    from .utils import ThirdPartyConfig
    from .types import User, UsersResponse


class SignInUpResult(ABC):
    def __init__(self, status: Literal['OK', 'FIELD_ERROR'], user: Union[User, None] = None,
                 created_new_user: Union[bool, None] = None, error: Union[str, None] = None):
        self.status = status
        self.is_ok = False
        self.is_field_error = False
        self.user = user
        self.created_new_user = created_new_user
        self.error = error


class SignInUpOkResult(SignInUpResult):
    def __init__(self, user: User, created_new_user: bool):
        super().__init__('OK', user, created_new_user)
        self.is_ok = True


class SignInUpFieldErrorResult(SignInUpResult):
    def __init__(self, error: str):
        super().__init__('FIELD_ERROR', error=error)
        self.is_field_error = True


class RecipeInterface(ABC):
    def __init__(self):
        pass

    @abstractmethod
    async def get_user_by_id(self, user_id: str) -> Union[User, None]:
        pass

    @abstractmethod
    async def get_users_by_email(self, email: str) -> List[User]:
        pass

    @abstractmethod
    async def get_user_by_thirdparty_info(self, third_party_id: str, third_party_user_id: str) -> Union[User, None]:
        pass

    @abstractmethod
    async def sign_in_up(self, third_party_id: str, third_party_user_id: str, email: str,
                         email_verified: bool) -> SignInUpResult:
        pass

    @abstractmethod
    async def get_users_oldest_first(self, limit: int = None, next_pagination: str = None) -> UsersResponse:
        pass

    @abstractmethod
    async def get_users_newest_first(self, limit: int = None, next_pagination: str = None) -> UsersResponse:
        pass

    @abstractmethod
    async def get_user_count(self) -> int:
        pass


class APIOptions:
    def __init__(self, request: BaseRequest, response: Union[BaseResponse, None], recipe_id: str,
                 config: ThirdPartyConfig, recipe_implementation: RecipeInterface, providers: List[Provider]):
        self.request = request,
        self.response = response
        self.recipe_id = recipe_id
        self.config = config
        self.providers = providers
        self.recipe_implementation = recipe_implementation


class SignInUpPostResponse(ABC):
    def __init__(self, status: Literal['OK', 'FIELD_ERROR'], user: Union[User, None] = None,
                 created_new_user: Union[bool, None] = None, auth_code_response: any = None,
                 error: Union[str, None] = None):
        self.status = status
        self.is_ok = False
        self.is_field_error = False
        self.user = user
        self.created_new_user = created_new_user
        self.error = error
        self.auth_code_response = auth_code_response

    @abstractmethod
    def to_json(self):
        pass


class GeneratePasswordResetTokenResponse(ABC):
    def __init__(self, status: Literal['OK']):
        self.status = status

    @abstractmethod
    def to_json(self):
        pass


class EmailExistsResponse(ABC):
    def __init__(self, status: Literal['OK'], exists: bool):
        self.status = status
        self.exists = exists

    @abstractmethod
    def to_json(self):
        pass


class PasswordResetResponse(ABC):
    def __init__(self, status: Literal['OK', 'RESET_PASSWORD_INVALID_TOKEN_ERROR']):
        self.status = status

    @abstractmethod
    def to_json(self):
        pass


class SignInUpPostOkResponse(SignInUpPostResponse):
    def __init__(self, user: Union, created_new_user: bool, auth_code_response: any):
        super().__init__('OK', user, created_new_user, auth_code_response)
        self.is_ok = True

    def to_json(self):
        return {
            'status': self.status,
            'user': {
                'id': self.user.user_id,
                'email': self.user.email,
                'timeJoined': self.user.time_joined,
                'thirdParty': {
                    'id': self.user.third_party_info.id,
                    'userId': self.user.third_party_info.user_id
                }
            }
        }


class SignInUpPostFieldErrorResponse(SignInUpPostResponse):
    def __init__(self, error: str):
        super().__init__('FIELD_ERROR', error=error)
        self.is_field_error = True

    def to_json(self):
        return {
            'status': self.status,
            'error': self.error
        }


class AuthorisationUrlGetResponse(ABC):
    def __init__(self, status: Literal['OK'], url: str):
        self.status = status
        self.url = url

    def to_json(self):
        return {
            'status': self.status,
            'url': self.url
        }


class AuthorisationUrlGetOkResponse(AuthorisationUrlGetResponse):
    def __init__(self, url: str):
        super().__init__('OK', url)

from supertokens_python.thirdparty.interfaces import APIOptions as ThirdPartyAPIOptions
from supertokens_python.emailpassword.interfaces import APIOptions as EmailPasswordAPIOptions

class APIInterface(ABC):
    def __init__(self):
        self.disable_sign_in_up_post = False
        self.disable_authorisation_url_get = False

    @abstractmethod
    async def authorisation_url_get(self, provider: Provider, api_options: APIOptions) -> AuthorisationUrlGetResponse:
        pass

    @abstractmethod
    async def email_exists_get(self, email: str, options: EmailPasswordAPIOptions) -> EmailExistsResponse:
        pass

    @abstractmethod
    async def generate_password_reset_token_post(self, id: str, value: str,  options: EmailPasswordAPIOptions) -> GeneratePasswordResetTokenResponse:
        pass

    @abstractmethod
    async def password_reset_post(self, id: str, value: str, token,  options: EmailPasswordAPIOptions) -> PasswordResetResponse:
        pass

    @abstractmethod
    async def sign_in_up_post(self, signInUpAPIInput):
        pass


