import json
from typing import Any, Dict, TypeVar, Union
from unittest.mock import patch

from pytest import mark
from supertokens_python.recipe import session

from supertokens_python.recipe.session.recipe import SessionRecipe
from supertokens_python.recipe.session.recipe_implementation import RecipeImplementation
from supertokens_python.recipe.multitenancy.constants import DEFAULT_TENANT_ID
from supertokens_python.recipe.session.claims import PrimitiveClaim
from supertokens_python.recipe.session.interfaces import (
    JSONObject,
    SessionClaimValidator,
    ClaimValidationResult,
    SessionClaim,
)
from supertokens_python.recipe.session.session_class import Session
from supertokens_python import init
from tests.utils import setup_function, teardown_function, start_st, st_init_common_args

_ = setup_function  # type:ignore
_ = teardown_function  # type:ignore

_T = TypeVar("_T")

pytestmark = mark.asyncio


async def test_should_not_throw_for_empty_array():
    st_args = {
        **st_init_common_args,
        "recipe_list": [
            session.init(get_token_transfer_method=lambda _, __, ___: "cookie")
        ],
    }
    init(**st_args)  # type:ignore
    start_st()

    s = SessionRecipe.get_instance()
    assert isinstance(s.recipe_implementation, RecipeImplementation)

    user_session = Session(
        s.recipe_implementation,
        s.recipe_implementation.config,
        "test_access_token",
        "test_front_token",
        None,  # refresh token
        None,  # anti csrf token
        "test_session_handle",
        "test_user_id",
        {},  # user_data_in_access_token
        None,
        False,  # access_token_updated
        DEFAULT_TENANT_ID,
    )
    with patch.object(
        Session,
        "merge_into_access_token_payload",
        wraps=user_session.merge_into_access_token_payload,
    ) as mock:
        await user_session.assert_claims([])
        mock.assert_not_called()


async def test_should_call_validate_with_the_same_payload_object():
    st_args = {
        **st_init_common_args,
        "recipe_list": [
            session.init(get_token_transfer_method=lambda _, __, ___: "cookie")
        ],
    }
    init(**st_args)  # type:ignore
    start_st()

    s = SessionRecipe.get_instance()
    assert isinstance(s.recipe_implementation, RecipeImplementation)

    payload = {"custom-key": "custom-value"}

    user_session = Session(
        s.recipe_implementation,
        s.recipe_implementation.config,
        "test_access_token",
        "test_front_token",
        None,  # refresh token
        None,  # anti csrf token
        "test_session_handle",
        "test_user_id",
        payload,  # user_data_in_access_token
        None,  # req_res_info
        False,  # access_token_updated
        DEFAULT_TENANT_ID,
    )

    class DummyClaimValidator(SessionClaimValidator):
        def __init__(self, claim: SessionClaim[Any]):
            super().__init__("claim_validator_id")
            self.claim = claim
            self.validate_calls: Dict[str, int] = {}

        async def validate(
            self, payload: JSONObject, user_context: Union[Dict[str, Any], None] = None
        ):
            payload_json = json.dumps(payload)
            self.validate_calls[payload_json] = (
                self.validate_calls.get(payload_json, 0) + 1
            )
            return ClaimValidationResult(is_valid=True)

        def should_refetch(self, payload: JSONObject, user_context: Dict[str, Any]):
            return False

    dummy_claim = PrimitiveClaim("st-claim", lambda _, __, ___: "Hello world")

    dummy_claim_validator = DummyClaimValidator(dummy_claim)

    dummy_claim.validators.dummy_claim_validator = dummy_claim_validator  # type: ignore

    with patch.object(
        Session,
        "merge_into_access_token_payload",
        wraps=user_session.merge_into_access_token_payload,
    ) as mock:
        await user_session.assert_claims([dummy_claim.validators.dummy_claim_validator])  # type: ignore

        assert dummy_claim_validator.validate_calls == {json.dumps(payload): 1}
        mock.assert_not_called()
