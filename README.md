# Schwarz Eats — Meal Planner App

Mobile-first weekly meal planning app for Parker & wife. Swipe through HelloFresh recipes, build a shopping list, and email it to both of you.

## Files
- `index.html` — the full app
- `recipes.js` — all 88 recipes with images and ingredient data (auto-generated)

## Setup (one-time, ~5 minutes)

### Step 1: Set your PIN
In `index.html`, find this line near the top of the `<script>` section:
```js
const PIN = "2580";
```
Change it to any 4-digit PIN you and your wife will share.

### Step 2: Add your wife's email
```js
const EMAIL_2 = "UPDATE_WIFES_EMAIL_HERE";
```
Replace with her actual email address.

### Step 3: Set up Zapier webhook (sends the email)

1. Go to [zapier.com](https://zapier.com) and click **Create Zap**
2. **Trigger**: Search for "Webhooks by Zapier" → select **Catch Hook** → click Continue
3. Copy the **webhook URL** shown (looks like `https://hooks.zapier.com/hooks/catch/...`)
4. **Action**: Search for "Gmail" → select **Send Email**
5. Map the fields:
   - **To**: type `parkerschwarz@gmail.com, your.wife@email.com` (or use the `emails` field from the webhook)
   - **Subject**: use the `subject` field from the webhook body
   - **Body (Plain)**: paste this template:
     ```
     🍽 THIS WEEK'S MEALS:
     {{meals}}

     🛒 SHOPPING LIST ({{item_count}} items):
     {{shopping_list}}

     ✅ ALREADY HAVE:
     {{have_list}}
     ```
6. Test and turn on the Zap
7. Paste the webhook URL into `index.html`:
```js
const ZAPIER_WEBHOOK = "https://hooks.zapier.com/hooks/catch/YOUR_ID_HERE";
```

### Step 4: Deploy to GitHub Pages

1. Create a new **public** GitHub repo (e.g. `schwarz-eats`)
2. Upload both files (`index.html` and `recipes.js`)
3. Go to **Settings → Pages → Source → Deploy from branch → main → / (root)**
4. Your app will be live at `https://YOUR_GITHUB_USERNAME.github.io/schwarz-eats/`
5. Bookmark it on both phones — add to home screen for app-like feel

## How to use

1. Open the URL, enter your PIN
2. Swipe **right (♥)** to pick a meal, **left (✕)** to skip
3. Tap **"X picked"** badge to review your selections
4. Tap **Shopping list →** to see all ingredients combined and categorized
5. Check off items you already have at home
6. Tap **Send to email →** — both of you get the meal plan + shopping list

## Updating recipes
When you add new recipes to Recipe Database.xlsx and their PDFs to this folder, re-run the build script to regenerate `recipes.js`. Contact Parker's AI assistant to do this.
