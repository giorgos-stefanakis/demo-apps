import jwt
from fastapi import HTTPException, status


class TokenValidator:
    """Validates Entra ID v2.0 access tokens."""

    def __init__(self, tenant_id: str, client_id: str, api_audience: str) -> None:
        self._issuer = f"https://login.microsoftonline.com/{tenant_id}/v2.0"
        # v2.0 tokens carry the client ID as audience; the App ID URI is accepted as well.
        self._audiences = [api_audience, client_id]
        self._keys = jwt.PyJWKClient(f"https://login.microsoftonline.com/{tenant_id}/discovery/v2.0/keys")

    def validate(self, authorization: str | None) -> dict:
        if not authorization or not authorization.startswith("Bearer "):
            raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Missing bearer token")
        token = authorization.removeprefix("Bearer ")
        try:
            signing_key = self._keys.get_signing_key_from_jwt(token)
            return jwt.decode(
                token,
                signing_key.key,
                algorithms=["RS256"],
                audience=self._audiences,
                issuer=self._issuer,
            )
        except jwt.PyJWTError as error:
            raise HTTPException(status.HTTP_401_UNAUTHORIZED, f"Invalid token: {error}") from error
