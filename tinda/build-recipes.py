"""Build tinda/recipes.js from recipes.js.

Keeps the factual layer (ingredients, quantities, nutrition, times, tags) and
regenerates every recipe's name/subtitle from those facts, so no HelloFresh
authored text ships in the new dataset. Drops imageUrl and hellofreshId.

Names are assembled as [method] [flavor] [protein] [form], where every part is
read off the recipe's own structured fields.
"""
import json, re, collections, sys, os

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, '..', 'recipes.js')   # read-only: the original dataset
OUT = os.path.join(HERE, 'recipes.js')

# Present in nearly every recipe, so they say nothing about the dish.
STAPLES = {
    'salt', 'black pepper', 'pepper', 'cooking oil', 'olive oil', 'sugar',
    'butter', 'water', 'flour', 'all-purpose flour', 'cooking spray',
    'vegetable oil', 'oven-ready tray', 'baking mix', 'cornstarch',
    'chicken stock concentrate', 'veggie stock concentrate',
    'beef stock concentrate', 'seafood stock concentrate',
    'pork stock concentrate', 'stock concentrate', 'chicken broth powder',
}

# Dish form is a fact about what the thing is, so reading it off the source
# name carries over no expression.
FORMS = [
    (r'\bbowls?\b', 'Bowls'), (r'\bsalads?\b', 'Salad'), (r'\btacos?\b', 'Tacos'),
    (r'\bwraps?\b', 'Wraps'), (r'\bburritos?\b', 'Burritos'),
    (r'\bquesadillas?\b', 'Quesadillas'), (r'\benchiladas?\b', 'Enchiladas'),
    (r'\bstir-?fry\b', 'Stir-Fry'), (r'\bsoups?\b', 'Soup'), (r'\bstew\b', 'Stew'),
    (r'\bchili\b', 'Chili'), (r'\bcurry\b', 'Curry'), (r'\bramen\b', 'Ramen'),
    (r'\bburgers?\b', 'Burgers'), (r'\bsandwich(es)?\b', 'Sandwiches'),
    (r'\bsandos?\b', 'Sandwiches'), (r'\bsliders?\b', 'Sliders'),
    (r'\bflatbreads?\b', 'Flatbreads'), (r'\bpizzas?\b', 'Pizza'),
    (r'\bmeatballs?\b', 'Meatballs'), (r'\bmeatloa(f|ves)\b', 'Meatloaves'),
    (r'\brisotto\b', 'Risotto'), (r'\bpaella\b', 'Paella'),
    (r'\bravioli\b', 'Ravioli'), (r'\btortelloni\b', 'Tortelloni'),
    (r'\bgnocchi\b', 'Gnocchi'), (r'\bspaghetti\b', 'Spaghetti'),
    (r'\bpenne\b', 'Penne'), (r'\bcavatappi\b', 'Cavatappi'),
    (r'\brigatoni\b', 'Rigatoni'), (r'\bfettuccine\b', 'Fettuccine'),
    (r'\blinguine\b', 'Linguine'), (r'\borzo\b', 'Orzo'),
    (r'\blo mein\b', 'Lo Mein'), (r'\bpad thai\b', 'Pad Thai'),
    (r'\bnoodles?\b', 'Noodles'), (r'\bpasta\b', 'Pasta'),
    (r'\bcouscous\b', 'Couscous'), (r'\bfried rice\b', 'Fried Rice'),
    (r'\bhash\b', 'Hash'), (r'\bskillet\b', 'Skillet'), (r'\bbake\b', 'Bake'),
    (r'\bcasserole\b', 'Casserole'), (r'\bpot pie\b', 'Pot Pie'),
    (r'\bfrittata\b', 'Frittata'), (r'\bpitas?\b', 'Pitas'),
    (r'\bgyros?\b', 'Gyros'), (r'\bbanh mi\b', 'Banh Mi'),
    (r'\bmelts?\b', 'Melts'), (r'\bnachos\b', 'Nachos'),
    (r'\bchops\b', 'Chops'), (r'\bschnitzel\b', 'Schnitzel'),
    (r'\bpi?ccata\b', 'Piccata'), (r'\bkebabs?\b', 'Kebabs'),
    (r'\bskewers?\b', 'Skewers'), (r'\bdumplings?\b', 'Dumplings'),
    (r'\bsushi\b', 'Sushi Bowls'), (r'\bshepherd\b', "Shepherd's Pie"),
]

# When no form is named, fall back to the starch the recipe actually contains.
STARCH_FORMS = [
    ('flour tortillas', 'Tacos'), ('corn tortillas', 'Tacos'),
    ('potato buns', 'Burgers'), ('brioche buns', 'Burgers'),
    ('demi-baguette', 'Subs'), ('naan', 'Naan Plates'),
    ('jasmine rice', 'Rice Bowls'), ('basmati rice', 'Rice Bowls'),
    ('rice', 'Rice Bowls'), ('israeli couscous', 'Couscous Bowls'),
    ('couscous', 'Couscous Bowls'), ('bulgur', 'Grain Bowls'),
    ('farro', 'Grain Bowls'), ('quinoa', 'Grain Bowls'),
]

# Bulk starches carry the dish's form, not its flavor, so they never lead a name.
STARCHY = re.compile(
    r'\b(rice|pasta|spaghetti|penne|cavatappi|rigatoni|fettuccine|linguine|orzo|'
    r'noodles?|tagliatelle|couscous|quinoa|farro|bulgur|potatoes?|tortillas?|'
    r'buns?|baguette|bread|naan|pita|lentils)\b', re.I)

# Words describing how a component was processed or packaged. They belong on a
# picking slip, not in a dish name.
PROCESS = re.compile(
    r'\b(chopped|diced|sliced|shredded|minced|halved|trimmed|peeled|pre-?cooked|'
    r'pre-?portioned|microwavable|boneless|skinless|dark meat|white meat|'
    r'frozen|fresh|organic|thin-?cut|value|family|jumbo|whole)\b', re.I)

# Trailing packaging/format nouns, and the suffixes that turn a supplier's
# branded blend into a plain culinary adjective (Tuscan Heat Spice -> Tuscan).
FORMAT_TAIL = re.compile(
    r'\s*\b(spice blend|seasoning blend|spice|seasoning|paste|sauce base|sauce|'
    r'dressing|crunch|glaze|powder|rub|marinade|stock|concentrate|blend|mix|'
    r'packet|sachet|cup|tray|base|topping)\b\s*$', re.I)

PROTEIN_ROOTS = {
    'Chicken': ['chicken'], 'Turkey': ['turkey'],
    'Beef': ['beef', 'steak', 'sirloin', 'bavette', 'rib-eye', 'ribeye', 'brisket'],
    'Pork': ['pork', 'bacon', 'sausage', 'ham', 'chorizo', 'prosciutto', 'pancetta'],
    'Shrimp': ['shrimp'], 'Salmon': ['salmon'], 'Tofu': ['tofu'],
    'Tilapia': ['tilapia'], 'Cod': ['cod'], 'Lamb': ['lamb'],
    'Lobster': ['lobster'], 'Scallop': ['scallop'], 'Duck': ['duck'],
    'Crab': ['crab'], 'Tuna': ['tuna'],
    'Fish': ['fish', 'trout', 'pollock', 'halibut', 'barramundi'],
}

CUISINE_CANON = {
    'north america': 'North American', 'american': 'North American',
    'southern europe': 'Southern European', 'east asia': 'East Asian',
    'southeast asia': 'Southeast Asian', 'middle east': 'Middle Eastern',
    'central america': 'Latin American', 'south america': 'Latin American',
}


def load():
    s = open(SRC).read()
    s = s[s.index('['):].rstrip().rstrip(';')
    return json.loads(s)


def clean(ing):
    """Normalize a supplier ingredient string into plain culinary English."""
    s = re.sub(r'\s*\([^)]*\)', '', ing)
    s = PROCESS.sub(' ', s)
    s = re.sub(r'\s{2,}', ' ', s).strip(' ,&-')
    # Strip format tails so branded blends collapse to their flavor word
    # ("Bold & Savory Steak Spice" -> "Bold & Savory"). Repeat for stacked
    # tails like "Mushroom Stock Concentrate".
    stripped = s
    for _ in range(3):
        nxt = FORMAT_TAIL.sub('', stripped).strip(' ,&-')
        if nxt == stripped or not nxt:
            break
        stripped = nxt
    if stripped != s:
        # A blend named after its protein ("... Steak Spice") is a flavor, not meat.
        trimmed = re.sub(r'\s+\b(steak|chicken|beef|pork|burger|seafood|fish)\b$',
                         '', stripped, flags=re.I).strip(' ,&-')
        stripped = trimmed or stripped
    return (stripped or s).strip(' ,&-')


def protein_noun(r, ings):
    """The protein as it should read in a name, taken from the ingredient list."""
    p = r.get('protein') or ''
    roots = PROTEIN_ROOTS.get(p)
    if not roots:
        return '' if p in ('Veggie', 'Vegan', 'Other', '') else p
    for raw in ings:
        low = raw.lower()
        if not any(root in low for root in roots):
            continue
        if 'ground' in low:
            return f'Ground {p}'
        for word, out in (('sausage', 'Sausage'), ('bacon', 'Bacon'),
                          ('chorizo', 'Chorizo'), ('ham', 'Ham'),
                          ('prosciutto', 'Prosciutto'), ('meatball', 'Meatball')):
            if word in low:
                return out
        if p == 'Beef' and 'steak' in low:
            return 'Steak'
        return p
    return p


def build(recipes):
    # Rarer ingredient => more distinctive => better at naming the dish.
    freq = collections.Counter(i for r in recipes for i in r['ingredients'])
    used = collections.Counter()

    for r in recipes:
        ings = r['ingredients']
        # Distinctive components, rarest first, cleaned for display.
        heroes, seen = [], set()
        for i in sorted(ings, key=lambda x: freq[x]):
            if i.lower() in STAPLES:
                continue
            c = clean(i)
            if c and c.lower() not in seen:
                seen.add(c.lower())
                heroes.append(c)

        pro = protein_noun(r, ings)
        pro_low = pro.lower()

        src = r['name'].lower()
        form = next((canon for pat, canon in FORMS if re.search(pat, src)), '')
        if not form:
            joined = ' '.join(ings).lower()
            form = next((f for key, f in STARCH_FORMS if key in joined), '')
        if not form:
            form = 'Skillet' if 'One Pot' in (r.get('tags') or []) else 'Plate'

        # Flavor lead: most distinctive component that isn't the protein and
        # isn't already stated by the form.
        roots = PROTEIN_ROOTS.get(r.get('protein') or '', [])

        def is_protein(t):
            return any(root in t.lower() for root in roots)

        def usable(t):
            tl = t.lower()
            if pro_low and (tl in pro_low or pro_low in tl):
                return False
            if any(w in form.lower() for w in tl.split()):
                return False
            return True

        # Prefer a real flavor lead; fall back to anything usable.
        flavor = next((h for h in heroes if usable(h) and not STARCHY.search(h)
                       and not is_protein(h)), '')
        if not flavor:
            flavor = next((h for h in heroes if usable(h)), '')
        # Two-word cap keeps names menu-length.
        if len(flavor.split()) > 3:
            flavor = ' '.join(flavor.split()[:2])

        method = ''
        tags = set(r.get('tags') or [])
        if 'Oven Ready' in tags:
            method = 'Baked'
        elif 'One Pot' in tags and form != 'Skillet':
            method = 'One-Pot'

        # Veggie/vegan dishes have no protein noun to anchor the name, which
        # leaves a bare "Almonds Bowls". Pair the lead with a second component
        # so the name says what the dish is actually made of.
        if not pro:
            second = next((h for h in heroes
                           if usable(h) and h.lower() != flavor.lower()
                           and h.lower() not in flavor.lower()), '')
            if second:
                flavor = f'{flavor} & {second}' if flavor else second

        parts = [method, flavor, pro, form]
        name = re.sub(r'\s{2,}', ' ', ' '.join(p for p in parts if p)).strip()

        # Disambiguate with further distinctive components, then cuisine.
        if used[name.lower()]:
            for extra in heroes:
                if extra.lower() not in name.lower() and usable(extra):
                    cand = f'{name} with {extra}'
                    if not used[cand.lower()]:
                        name = cand
                        break
        if used[name.lower()]:
            raw_cz = (r.get('cuisine') or '').strip()
            cz = CUISINE_CANON.get(raw_cz.lower(), raw_cz)
            if cz and cz.lower() not in name.lower():
                name = f'{cz} {name}'
        n, cand = 2, name
        while used[cand.lower()]:
            cand = f'{name} #{n}'
            n += 1
        name = cand
        used[name.lower()] += 1

        # Subtitle: supporting cast not already named. The protein is stated in
        # the name, so restating the cut here just wastes the line.
        rest = [h for h in heroes
                if h.lower() not in name.lower() and not is_protein(h)][:3]
        if len(rest) == 3:
            subtitle = f'with {rest[0]}, {rest[1]} & {rest[2]}'
        elif rest:
            subtitle = 'with ' + ' & '.join(rest)
        else:
            subtitle = ''

        r['name'] = name
        r['subtitle'] = subtitle
        r['slug'] = re.sub(r'-{2,}', '-',
                           re.sub(r'[^a-z0-9]+', '-', name.lower())).strip('-')
        r.pop('imageUrl', None)
        r.pop('hellofreshId', None)
    return recipes


if __name__ == '__main__':
    d = build(load())
    if '--sample' in sys.argv:
        import random
        random.seed(7)
        for r in random.sample(d, 30):
            print(f"{r['name']}\n    {r['subtitle']}\n    [{r['protein']} | {r['cuisine']}]")
        lens = sorted(len(r['name']) for r in d)
        print('\nname len p50/p95/max:', lens[len(lens)//2], lens[int(len(lens)*.95)], lens[-1])
        print('numbered fallbacks:', sum(1 for r in d if re.search(r'#\d+$', r['name'])))
    else:
        os.makedirs(os.path.dirname(OUT), exist_ok=True)
        open(OUT, 'w').write('const RECIPES = ' + json.dumps(d, separators=(',', ':')) + ';\n')
        print(f'wrote {len(d)} recipes -> {OUT}')
