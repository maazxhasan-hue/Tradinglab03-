# Nexora AI — Apple-Inspired Design Principles

**Purpose:** apply the useful principles behind Apple's Human Interface Guidelines to Nexora AI's customer experience and internal tools. This is an independent design system, not an attempt to copy Apple's branding, proprietary assets, icons, or exact layouts.

## Product promise

Nexora AI should feel calm, capable, understandable, and trustworthy. Every screen should help a client answer: What is this? What can I do? What happens next? What data or commitment is involved?

## 1. Clarity over decoration
- One primary action per screen or section; secondary actions are visibly quieter.
- Use plain language and concrete verbs. Avoid inflated AI claims, jargon, fake metrics, and ambiguous status labels.
- Keep titles short, paragraphs scannable, and navigation predictable.
- Show the next step and the reason a user needs to take it.

## 2. Deference to the work
- The content, project brief, deliverable, and customer decision are the focus—not decorative UI.
- Use generous whitespace, restrained borders, subtle surfaces, and limited accent color.
- Use motion only to explain state changes or add useful feedback. Respect reduced-motion preferences.
- Avoid gratuitous gradients, neon, unnecessary badges, and animated dashboard noise.

## 3. Consistency and familiar patterns
- Reuse the same design tokens, spacing, buttons, form fields, cards, status styles, and focus treatment across the public site, inbox, client packs, and HQ.
- Keep labels and action names stable across pages.
- Prefer semantic HTML and native controls where possible; do not invent custom interactions without a clear benefit.

## 4. Typography and hierarchy
- Use a system-font stack, strong headline hierarchy, readable body text, and comfortable line length.
- Use weight, spacing, and size before introducing more colors.
- Keep long-form text readable and avoid tiny low-contrast metadata.

## 5. Accessibility by default
- Every interaction must work with keyboard and touch.
- Provide visible focus indicators, semantic headings, labelled form fields, accessible error/status announcements, and useful link text.
- Maintain WCAG AA contrast targets for normal text (4.5:1) and large text (3:1).
- Use target sizes of at least 44×44 CSS pixels where practical; never rely on color alone to communicate status.
- Respect `prefers-reduced-motion`, browser zoom, narrow screens, and assistive technologies.
- Validate forms clearly, preserve entered values on recoverable errors, and explain whether an action actually succeeded.

## 6. Feedback, control, and trust
- Show progress for long actions, disable duplicate submissions when needed, and explain failure in plain language.
- Provide undo or confirmation for destructive actions where feasible.
- Never imply a brief was sent, a file was deployed, a lead was contacted, or revenue was earned unless the system has evidence.
- Keep automation observable: status, timestamp, source, outcome, error, and next action.

## 7. Privacy and security
- Collect only the information needed to scope a project.
- Explain why information is requested and where it goes before submission.
- Never put credentials, access tokens, client secrets, or private customer data into prompts, logs, public pages, or artifacts.
- Keep owner/admin interfaces out of search indexing, require server-side authorization, and avoid storing secrets in browser storage.
- Separate public-facing Nexora AI branding from internal TradingLab03 infrastructure and handles; do not expose internal implementation details unnecessarily.

## 8. Depth and restrained visual language
- Use subtle surface separation and consistent corner radii to establish hierarchy; avoid stacking cards inside cards without a reason.
- Use one primary accent (Nexora blue: `#0071E3`) with neutral backgrounds and text. Status colors must retain sufficient contrast.
- Use icons only when they clarify meaning; pair unfamiliar icons with labels.
- Images, illustrations, and motion must communicate something useful, not merely fill space.

## 9. Responsive and resilient experiences
- Design mobile-first for small screens, touch, slow connections, and incomplete input.
- Make layouts reflow without horizontal scrolling at common viewport sizes.
- Every network-backed action needs loading, success, failure, and retry guidance.
- Provide a useful fallback when a connected service is unavailable, while being explicit that the fallback did not submit or send anything.

## 10. Ethical AI and commercial honesty
- Explain when work is AI-assisted if it materially affects a customer's expectations.
- Mark concepts, demos, estimates, and drafts as such until approved.
- Do not fabricate testimonials, client names, case studies, revenue, guarantees, or delivery capacity.
- Use approval gates for price, scope, external messages, production deployment, spending, and payment status.

## Design tokens

| Token | Value | Use |
|---|---|---|
| Background | `#F5F5F7` | Main canvas |
| Surface | `#FFFFFF` | Cards and form surfaces |
| Primary text | `#1D1D1F` | Headings and body text |
| Secondary text | `#6E6E73` | Supporting copy |
| Primary accent | `#0071E3` | Main actions, links, focus |
| Border | `#DEDEE3` | Dividers and outlines |
| Success | Dark green on pale green | Confirmed success only |
| Error | Dark red on pale red | Errors requiring attention |

Use spacing increments based on 4px (4, 8, 12, 16, 24, 32, 48, 64). Use rounded pills for primary actions and moderate rounded rectangles for content surfaces. Do not use radius, blur, or shadow to obscure content hierarchy.

## Interaction contract

Every important action should have:
1. A clear label and explanation before action.
2. A visible pending state if asynchronous.
3. A truthful result message.
4. A recoverable error path when possible.
5. An audit record for sensitive business operations.

## Application checklist

- [ ] Public website uses the Nexora AI name consistently.
- [ ] Internal TradingLab03 infrastructure and existing social handles remain unchanged.
- [ ] Enquiry form clearly distinguishes saved/submitted from local draft/failure.
- [ ] Inbox/admin actions are authenticated and destructive actions require confirmation.
- [ ] Keyboard navigation and focus visibility tested.
- [ ] Text contrast checked against WCAG AA.
- [ ] Mobile layout tested at narrow widths and 200% zoom.
- [ ] Reduced motion preference respected.
- [ ] Loading, empty, success, and error states checked.
- [ ] No fabricated customer proof or unsupported autonomy claims.
- [ ] All links, forms, privacy notices, and contact paths tested before release.

## Scope and ownership

The public website's first styling pass applies this system using system typography, neutral surfaces, blue accents, stronger hierarchy, accessible focus states, and reduced-motion support. The same tokens should be adopted gradually by inbox, HQ, proposal packs, and delivery views. Do not claim every internal screen conforms until each one has been audited and tested.

## Reference

Use Apple's public Human Interface Guidelines as inspiration for platform-independent principles such as clarity, consistency, deference, feedback, accessibility, and user control. Nexora AI's implementation should remain original and brand-appropriate.
