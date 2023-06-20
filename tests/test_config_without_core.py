from pytest import mark

from supertokens_python import InputAppInfo, Supertokens, SupertokensConfig, init
from supertokens_python.recipe import session
from supertokens_python.recipe.session import SessionRecipe


@mark.asyncio
@mark.parametrize(
    "api_domain,origin,cookie_same_site",
    [
        ("https://foo.com/", "https://bar.com/", "none"),  # Different URLs
        (
            "https://foo.example.com/",
            "https://bar.example.com/",
            "lax",
        ),  # Different subdomains
        (
            "https://foo.azurewebsites.net/",
            "https://bar.azurewebsites.net/",
            "none",
        ),  # PSL so same_site should be none despite
        (
            "http://foo.example.com/",
            "http://foo.example.com/",
            "lax",
        ),  # HTTP same url and subdomain
        ("http://example.com/", "http://example.com/", "lax"),  # HTTP same url
    ],
)
async def test_same_site_cookie_values(
    api_domain: str, origin: str, cookie_same_site: str
):
    init(
        supertokens_config=SupertokensConfig("http://localhost:3567"),
        app_info=InputAppInfo(
            app_name="SuperTokens Demo",
            api_domain=api_domain,
            origin=origin,
            api_base_path="/auth",
        ),
        framework="fastapi",
        recipe_list=[
            session.init(
                cookie_same_site="strict" if cookie_same_site == "strict" else None
            ),
        ],
    )

    s = SessionRecipe.get_instance()
    assert (await s.config.cookie_same_site(None, {})) == cookie_same_site  # type: ignore
    s.reset()
    Supertokens.reset()
