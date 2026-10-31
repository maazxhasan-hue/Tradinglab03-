# Worker rate limiting

All limits are configurable with Worker environment variables. Values in `wrangler.template.toml` are deployment defaults; the runtime also validates variables and falls back safely when a value is missing or invalid.

| Variable | Default | Scope |
|---|---:|---|
| `AUTH_IP_LIMIT_PER_WINDOW` | 20 | Authentication attempts per IP and action |
| `AUTH_ACCOUNT_LIMIT_PER_WINDOW` | 8 | Authentication attempts per normalized account/email and action |
| `AUTH_RATE_WINDOW_SECONDS` | 3600 | Authentication rolling window |
| `AUTH_BACKOFF_BASE_SECONDS` | 2 | Initial exponential delay after a failed login |
| `AUTH_BACKOFF_MAX_SECONDS` | 300 | Maximum delay after repeated failed logins |
| `PUBLIC_CHAT_LIMIT_PER_WINDOW` | 30 | Public chat requests per IP |
| `PUBLIC_INTAKE_LIMIT_PER_WINDOW` | 12 | Intake attempts per IP |
| `PUBLIC_RATE_WINDOW_SECONDS` | 3600 | Public endpoint rolling window |
| `AUTHENTICATED_ACTION_LIMIT_PER_WINDOW` | 120 | Per-account intake/referral actions |
| `AUTHENTICATED_RATE_WINDOW_SECONDS` | 3600 | Authenticated action rolling window |

The Worker stores only salted hashes for rate-limit identities, not raw IP addresses or raw email addresses. Authentication uses separate IP and account buckets and exponential backoff after failed login attempts; it does not permanently lock an account. Rate-limit state is stored in D1 table `client_rate_limit_events`, created by migration `0006_configurable_rate_limits.sql`.

When changing these settings, deploy the Worker with the updated environment variables and monitor 429 responses. Limits should be tuned to observed legitimate usage and abuse patterns.
