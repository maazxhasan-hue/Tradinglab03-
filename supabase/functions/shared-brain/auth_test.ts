import { verifyGitHubActionsOidc } from "./auth.ts";

const encoder = new TextEncoder();

function base64Url(bytes: Uint8Array): string {
  let binary = "";
  for (const byte of bytes) binary += String.fromCharCode(byte);
  return btoa(binary).replace(/=/g, "").replace(/\+/g, "-").replace(/\//g, "_");
}

async function signedToken(overrides: Record<string, unknown> = {}) {
  const now = Math.floor(Date.now() / 1000);
  const pair = await crypto.subtle.generateKey(
    {
      name: "RSASSA-PKCS1-v1_5",
      modulusLength: 2048,
      publicExponent: new Uint8Array([1, 0, 1]),
      hash: "SHA-256",
    },
    true,
    ["sign", "verify"],
  ) as CryptoKeyPair;
  const jwk = await crypto.subtle.exportKey("jwk", pair.publicKey) as JsonWebKey & {
    kid?: string; use?: string; alg?: string;
  };
  jwk.kid = "unit-test-key";
  jwk.use = "sig";
  jwk.alg = "RS256";

  const header = base64Url(encoder.encode(JSON.stringify({ alg: "RS256", typ: "JWT", kid: "unit-test-key" })));
  const claims = {
    iss: "https://token.actions.githubusercontent.com",
    aud: "nexora-shared-brain",
    exp: now + 300,
    nbf: now - 5,
    iat: now - 5,
    repository: "maazxhasan-hue/Tradinglab03-",
    repository_id: "1417902142",
    workflow_ref: "maazxhasan-hue/Tradinglab03-/.github/workflows/shared-brain-registry.yml@refs/heads/main",
    event_name: "workflow_run",
    ...overrides,
  };
  const payload = base64Url(encoder.encode(JSON.stringify(claims)));
  const unsigned = header + "." + payload;
  const signature = await crypto.subtle.sign(
    "RSASSA-PKCS1-v1_5",
    pair.privateKey,
    encoder.encode(unsigned),
  );
  const token = unsigned + "." + base64Url(new Uint8Array(signature));
  const fetcher: typeof fetch = async () =>
    new Response(JSON.stringify({ keys: [jwk] }), {
      status: 200,
      headers: { "content-type": "application/json" },
    });
  return { token, fetcher, now };
}

function assert(condition: unknown, message: string): asserts condition {
  if (!condition) throw new Error(message);
}

Deno.test("accepts a correctly signed token from the approved workflow", async () => {
  const fixture = await signedToken();
  assert(await verifyGitHubActionsOidc(fixture.token, fixture.fetcher, fixture.now), "valid OIDC token was rejected");
});

Deno.test("rejects a token from a different repository", async () => {
  const fixture = await signedToken({ repository: "attacker/other-repo", repository_id: "12345" });
  assert(!(await verifyGitHubActionsOidc(fixture.token, fixture.fetcher, fixture.now)), "foreign repository token was accepted");
});

Deno.test("rejects a token with the wrong audience", async () => {
  const fixture = await signedToken({ aud: "other-service" });
  assert(!(await verifyGitHubActionsOidc(fixture.token, fixture.fetcher, fixture.now)), "wrong audience was accepted");
});

Deno.test("rejects an expired token", async () => {
  const now = Math.floor(Date.now() / 1000);
  const fixture = await signedToken({ exp: now - 1 });
  assert(!(await verifyGitHubActionsOidc(fixture.token, fixture.fetcher, now)), "expired token was accepted");
});

Deno.test("rejects a tampered signature", async () => {
  const fixture = await signedToken();
  const parts = fixture.token.split(".");
  parts[2] = (parts[2][0] === "A" ? "B" : "A") + parts[2].slice(1);
  assert(!(await verifyGitHubActionsOidc(parts.join("."), fixture.fetcher, fixture.now)), "tampered signature was accepted");
});

Deno.test("fails closed when GitHub JWKS cannot be fetched", async () => {
  const fixture = await signedToken();
  const failingFetcher: typeof fetch = async () => new Response("unavailable", { status: 503 });
  assert(!(await verifyGitHubActionsOidc(fixture.token, failingFetcher, fixture.now)), "JWKS failure was accepted");
});
