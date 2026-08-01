# Tinda Fa Dinna — Meal Planner

Swipe through dinners, build a shopping list, email it out. Same idea as the
Schwarz Eats app in the repo root, rebuilt so the content is defensible enough
to share publicly.

Schwarz Eats is untouched — this is a separate app in its own directory. Both
can be served side by side (`/` and `/tinda/`).

## Files
- `index.html` — the full app, single file
- `recipes.js` — 8,984 recipes (generated; see below)

## How to use
1. Open the app and enter your PIN
2. Set protein and dish-type preferences, then tap **Start Swiping**
3. Swipe **right (👍)** to pick a meal, **left (👎)** to skip
4. Use the cuisine and time chips to narrow the deck
5. Tap the **"X picked"** badge to review selections
6. Tap **Shopping list →** for combined, categorized ingredients
7. Check off what you already have
8. Tap **Send to email →**, add recipients, and send

## Where the content comes from

The dataset carries only the **factual** layer of each recipe — ingredients,
quantities, nutrition, prep/cook times, servings, cuisine, tags. Under US law a
listing of ingredients is not copyrightable (17 U.S.C. §102(b); *Publications
Int'l v. Meredith Corp.*, 88 F.3d 473), so this layer is free to use.

Everything expressive is generated locally instead of copied:

- **Dish names and subtitles** are assembled from each recipe's own structured
  fields — `[method] [flavor] [protein] [form]`, where the flavor lead is the
  rarest non-pantry ingredient and the form is the dish type. No supplier prose
  ships in the data. See `dishArt()` and the build script for the details.
- **Card artwork** is drawn by the app: a gradient chosen by cuisine and a glyph
  chosen by dish, both hashed from the recipe so a dish always looks the same.
  No photographs, no image CDN, no external requests.
- **`cardLink`** points at the publisher's own hosted recipe card. Linking out
  is deliberate — cooking instructions are never copied into this repo, and the
  link sends traffic back to the source.

Two things worth knowing before this goes anywhere public:

- The PIN is a client-side SHA-256 check. It gates the UI, not the data — a
  4-digit PIN brute-forces instantly and `recipes.js` is a plain static file.
  Treat it as a speed bump, not access control.
- If you ever add analytics, email capture, or an affiliate link, you need a
  privacy policy before collecting anything. Never hand user email addresses to
  a third party without disclosed, explicit consent (CCPA treats that as a sale
  of personal information; GDPR requires opt-in).
