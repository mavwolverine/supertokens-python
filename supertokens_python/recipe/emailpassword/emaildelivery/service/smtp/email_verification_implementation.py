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

from typing import Any, Dict

from supertokens_python.ingredients.emaildelivery.service.smtp import (
    GetContentResult, ServiceInterface, SMTPServiceConfigFrom)
from supertokens_python.recipe.emailpassword.types import (
    TypeEmailPasswordEmailDeliveryInput,
    TypeEmailVerificationEmailDeliveryInput)


class DefaultServiceImplementation(ServiceInterface[TypeEmailVerificationEmailDeliveryInput]):
    def __init__(self, emailPasswordServiceImpl: ServiceInterface[TypeEmailPasswordEmailDeliveryInput]) -> None:
        self.emailVerificationSeriveImpl = emailPasswordServiceImpl

    async def send_raw_email(self, get_content_result: GetContentResult,
                             config_from: SMTPServiceConfigFrom, user_context: Dict[str, Any]) -> None:
        return await self.emailVerificationSeriveImpl.send_raw_email(get_content_result, config_from, user_context)

    def get_content(self, email_input: TypeEmailVerificationEmailDeliveryInput, user_context: Dict[str, Any]) -> GetContentResult:
        return self.emailVerificationSeriveImpl.get_content(email_input, user_context)


def getServiceInterface(emailPasswordServiceImplementation: ServiceInterface[TypeEmailPasswordEmailDeliveryInput]) -> ServiceInterface[TypeEmailVerificationEmailDeliveryInput]:
    si = DefaultServiceImplementation(emailPasswordServiceImplementation)
    return si
