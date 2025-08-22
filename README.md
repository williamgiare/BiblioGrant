# BiblioGrant

![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)
![Repo Status](https://img.shields.io/badge/repo-public-brightgreen)
![Python](https://img.shields.io/badge/python-3.8%2B-blue)

---

**BiblioGrant** turns a BibTeX `.bib` file into a clean, grant-friendly **plain-text** bibliography.
Works as both a **Python package** (`import BiblioGrant`) and a **CLI** (`python -m BiblioGrant`).

* Proper Unicode output (LaTeX → Unicode for accents, quotes, Greek letters)
* Flexible ordering: keep `.bib` order, by **publication year**, or by **arXiv (preprint) date**
* Optional grouping: **PREPRINTS** first, then **PUBLICATIONS**
* Two output styles: **full** or **compact** (“First author et al., Venue Year, …”)
* Print to stdout or **save to file**

---

## Installation

**Requirements:** Python 3.8+, `bibtexparser`

```bash
pip install bibtexparser
```

### Use directly from the repo (recommended)

```
git clone <this-repo-url>
cd BiblioGrant
pip install -e .
```

> The editable install exposes the package `BiblioGrant` and the module entrypoint `python -m BiblioGrant`.

---

## Quick start

### CLI

```bash
# Print to stdout, keep .bib order (default)
python -m BiblioGrant refs.bib

# Save to a file
python -m BiblioGrant refs.bib --out biblio.txt

# Publication-year ordering, compact style
python -m BiblioGrant refs.bib --order-by publication_date --compact

# Global arXiv-date ordering (newest first)
python -m BiblioGrant refs.bib --order-by preprint_date

# Reverse the chosen order (oldest first / reverse .bib)
python -m BiblioGrant refs.bib --reverse
```

### Python API

```python
from BiblioGrant import print_biblio, save_biblio

# Print (keep .bib order)
print_biblio("refs.bib")

# Save compact, grouped by publication (preprints section first)
save_biblio("refs.bib", "biblio.txt", order_by="publication_date", compact=True)

# Sort globally by preprint (arXiv) date, oldest first
print_biblio("refs.bib", order_by="preprint_date", reverse=True)
```

---

## Options & behavior

### Ordering

* `order_by="keep_bib"` *(default)*: keep the original `.bib` order
  → with `reverse=True` prints the reverse of the `.bib` order.
* `order_by="publication_date"`: sort by **publication year**
  → newest first (add `reverse=True` for oldest first).
  → **Preprints** are **extracted and printed first** under `PREPRINTS`, then `PUBLICATIONS`
  (disable with `group_preprints_on_publication=False` or `--no-group-preprints`).
* `order_by="preprint_date"`: global sort by **arXiv yymm** (or old `astro-ph/YYMM…`)
  → newest first (add `reverse=True` for oldest first).
  → no section split in this mode.

### Output style

* **Full** (default):

  ```
  First Last, Second Last, … "Title." Journal 2025, 112(2): 023515. DOI: 10.xxxx/xxxxx
  ```
* **Compact** (`compact=True` / `--compact`):

  * **Published** → `First Author et al., Journal 2025, 112(2): 023515`
  * **Preprint**  → `First Author et al., arXiv:2507.01848`
    *(If there’s a single author, “et al.” is omitted.)*

### Preprint detection

An entry is treated as **preprint** if:

* `ENTRYTYPE` ∈ {`article`, `unpublished`, `misc`} **and**
* there is **no** `journal`/`journaltitle`.
  *(DOI presence is ignored; some preprints have DOIs.)*

### LaTeX → Unicode

Converts common LaTeX markup:

* Accents: `\' \` " ^ \~ \c \v \H \k \u \r = .`(with/without braces),`\i`, `\j\`
* Quotes/dashes: \`\`\`\` / `''`, `\textquote*`, `\textendash`, `\textemdash`
* Greek letters: `\alpha … \Omega`
* Removes wrappers like `\ensuremath`, inline `$…$`, and stray braces

### Author formatting

Outputs names as **“First Middle Last”**.
Handles both `Last, First M.` and `First M. Last` in the `.bib`.

---

## CLI reference

```
python -m BiblioGrant BIBFILE
  --order-by {keep_bib,publication_date,preprint_date}   # default: keep_bib
  --reverse                                              # reverse the chosen order
  --compact                                              # compact output
  --no-group-preprints                                   # disable PREPRINTS/PUBLICATIONS split with publication_date
  --out OUTPUT.txt                                       # save to file instead of printing
```

---

## Jupyter example

```python
from BiblioGrant import print_biblio, save_biblio

# Preview a compact, grant-friendly list
print_biblio("refs.bib", order_by="publication_date", compact=True)

# Save full refs with global preprint-date ordering (oldest first)
save_biblio("refs.bib", "biblio_preprints_oldest.txt",
            order_by="preprint_date", reverse=True, compact=False)
```

* For a walkthrough, see the Jupyter notebook [`Examples/Examples.ipynb`](Examples/Examples.ipynb).

---

## Troubleshooting

* **Strange LaTeX left in output** → only common macros are handled; add more mappings if needed.
* **Published item shown as preprint** → ensure the entry has `journal` or `journaltitle`.
* **Sorting looks odd** → for publication sorting we use the **year**; for preprints we parse arXiv IDs (new and old).

---

