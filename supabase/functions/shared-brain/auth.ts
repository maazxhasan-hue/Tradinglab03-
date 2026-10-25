const ISSUER = "https://token.actions.githubusercontent.com";
const AUDIENCE = "nexora-shared-brain";
const REPOSITORY = "maazxhasan-hue/Tradinglab03-";
const REPOSITORY_ID = "1417902142";
const WORKFLOW_REF = "maazxhasan-hue/Tradinglab03-/.github/workflows/shared-brain-registry.yml@refs/heads/main";
const JWKS_URL = "https://token.actions.githubusercontent.com/.well-known/jwks";

type JwtClaims = Record<string, unknown>;
type JwtHeader = Record<string, unknown>;

function decodeBase64Url(segment: string): Uint8Array {
  if (!/^[A-Za-z0-9_-]+$/.test(segment)) throw new Error("Invalid base64url");
  const normalized = segment.replace(/-/g, "+").replace(/_/g, "/");
  const padded = normalized + "=".repeat((4 - (normalized.length % 4)) % 4);
  const binary = atob(padded);
  return Uint8Array.from(binary, (character) => character.charCodeAt(0));
}

function decodeJsonSegment(segment: string): Record<string, unknown> {
  return JSON.parse(new TextDecoder().decode(decodeBase64Url(segment)));
}

/**
 * Validate the short-lived identity token issued to the one approved workflow.
 * Any parse, network, key, claim, or signature failure returns false (fail closed).
 */
export async function verifyGitHubActionsOidc(
  token: string,
  fetcher: typeof fetch = fetch,
  nowSeconds = Math.floor(Date.now() / 1000),
): Promise<boolean> {
  try {
    const parts = token.split(".");
    if (parts.length !== 3 || parts.some((part) => part.length === 0)) return false;

    const header = decodeJsonSegment(parts[0]) as JwtHeader;
    const claims = decodeJsonSegment(parts[1]) as JwtClaims;
    if (header.alg !== "RS256" || typeof header.kid !== "string") return false;

    const audience = claims.aud;
    const audienceMatches = audience === AUDIENCE ||
      (Array.isArray(audience) && audience.includes(AUDIENCE));
    const exp = Number(claims.exp);
    const iat = Number(claims.iat);
    const nbf = claims.nbf === undefined ? iat : Number(claims.nbf);

    if (
      claims.iss !== ISSUER ||
      !audienceMatches ||
      claims.repository !== REPOSITORY ||
      String(claims.repository_id) !== REPOSITORY_ID ||
      claims.workflow_ref !== WORKFLOW_REF ||
      !["workflow_run", "workflow_dispatch"].includes(String(claims.event_name)) ||
      !Number.isFinite(exp) || exp <= nowSeconds || exp > nowSeconds + 600 ||
      !Number.isFinite(iat) || iat > nowSeconds + 60 || iat < nowSeconds - 600 ||
      !Number.isFinite(nbf) || nbf > nowSeconds + 60
    ) return false;

    const response = await fetcher(JWKS_URL, { headers: { accept: "application/json" } });
    if (!response.ok) return false;
    const jwks = await response.json() as { keys?: JsonWebKey[] };
    if (!Array.isArray(jwks.keys)) return false;
    const key = jwks.keys.find((candidate) => {
      const extended = candidate as JsonWebKey & { kid?: string; use?: string; alg?: string };
      return extended.kid === header.kid &&
        extended.kty === "RSA" &&
        (extended.use === undefined || extended.use === "sig") &&
        (extended.alg === undefined || extended.alg === "RS256");
    });
    if (!key) return false;

    const cryptoKey = await crypto.subtle.importKey(
      "jwk",
      key,
      { name: "RSASSA-PKCS1-v1_5", hash: "SHA-256" },
      false,
      ["verify"],
    );
    return await crypto.subtle.verify(
      { name: "RSASSA-PKCS1-v1_5" },
      cryptoKey,
      decodeBase64Url(parts[2]),
      new TextEncoder().encode(parts[0] + "." + parts[1]),
    );
  } catch {
    return false;
  }
}
