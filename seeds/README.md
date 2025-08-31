# Seeds Schema (v2)

Seeds define which **narratives** Primecipher tracks.
Each narrative is a cluster of terms + rules that can later “grow” into branches.

---

## File

`backend/seeds/narratives.seed.json`

---

## Schema (version 2)

### Top-level

- **`version`** (number)
  Schema version. Must be `2`.

- **`narratives`** (list of objects)
  Each object defines one narrative.

---

### Narrative object

- **`name`** (string, required)
  Short unique identifier, e.g. `"dogs"`, `"ai"`.

- **`terms`** (list of strings, required)
  Core keywords that trigger matches.
  _Example:_ `["dog", "wif", "bonk"]`

- **`synonyms`** (list of strings, optional)
  Alternative spellings/phrases.
  _Example:_ `["doge", "doggy"]`

- **`require_all`** (list of strings, optional)
  Terms that **must all** appear for a match to count.
  _Example:_ `["ai"]` ensures “AI” must be present.

- **`block`** (list of strings, optional)
  Exclusion terms; if present, the parent is ignored.
  _Example:_ `["fake", "scam"]`

- **`weight`** (float, default = 1.0)
  Narrative-level multiplier applied to the heat score.
  Used to nudge relative importance, not dominate.

- **`branches`** (list of objects, optional)
  Sub-clusters within the narrative.
  Each branch has:
  - **`name`** (string) – label for the branch.
  - **`weight`** (float, default = 1.0) – relative multiplier.
  - **`terms`** (list of strings) – branch-specific keywords.

---

## Example

```json
{
  "version": 2,
  "narratives": [
    {
      "name": "dogs",
      "terms": ["dog", "wif", "bonk", "shiba"],
      "synonyms": ["doge", "doggy"],
      "require_all": [],
      "block": ["fake", "scam"],
      "weight": 1.0,
      "branches": [
        { "name": "solana-dogs", "weight": 1.2, "terms": ["wif", "bonk"] },
        { "name": "eth-dogs", "weight": 1.0, "terms": ["doge", "shiba"] }
      ]
    }
  ]
}
```
