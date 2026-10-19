# Analytics setup for Nexora AI

## Current status
Google Analytics is not installed because no Google Analytics 4 Measurement ID (format `G-XXXXXXXXXX`) has been supplied. Do not invent an ID or send analytics events to a placeholder.

## Enable GA4
1. Open Google Analytics at https://analytics.google.com/ and sign in with the business Google account.
2. Create an account/property for Nexora AI if one does not already exist.
3. Add a Web data stream for the final production hostname.
4. Copy the Measurement ID beginning with `G-`.
5. Store it as a repository/deployment setting such as `PUBLIC_GA4_MEASUREMENT_ID` if the build pipeline supports that variable. Do not commit account credentials or API secrets.
6. Add the official Google tag only after the ID is configured. Keep analytics disabled until the visitor has made the required consent choice, and provide a way to change that choice.
7. Verify real-time traffic in GA4 and inspect the browser network requests before considering the integration complete.

## Privacy and launch checks
- Never use a fabricated Measurement ID.
- Do not track before consent where consent is required.
- Do not send names, email addresses, phone numbers, UPI IDs, payment references, or form contents to analytics.
- Recheck the privacy notice after enabling analytics.
- Submit the canonical sitemap in Google Search Console after the production domain is confirmed to serve the intended Nexora website.
