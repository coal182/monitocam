# Sessions are fixed-lifetime; no refresh tokens

A **Session** is a hard 24h from login: the `access_token` cookie is minted once by `LoginView` and never renewed. When it expires, the user is redirected to login. We deliberately do **not** implement silent token refresh (no refresh token is issued or consumed), even though `SIMPLE_JWT` still declares `REFRESH_TOKEN_LIFETIME` / `ROTATE_REFRESH_TOKENS` — that config is dead and should be removed.

This is for a single-user LAN surveillance tool where a sliding session adds moving parts nobody needs; "expired means log in again" is the intended behaviour. Recording this because the unused refresh config looks like refresh *is* implemented, and a future reader would otherwise assume so.
