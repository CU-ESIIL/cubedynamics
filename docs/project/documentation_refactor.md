# Documentation structure and migration

## Problems found

- Library combines noun discovery, verb reference, and extension tutorials.
- The noun list duplicates catalog facts and lacks individual reference pages.
- Verb arguments are copied into multiple pages and can disagree with Python.
  For example, the verb catalog describes `flatten_cube()` as a long table,
  while the runtime returns an xarray object with stacked sample dimensions.
- Gallery-style reference hubs hide basic lists behind promotional headings.
- Tutorials, executable notebooks, and dependency designs are not consistently
  distinguished; there is no short progressive tutorial sequence.
- Navigation repeats pages, while useful legacy routes must remain accessible.

The [complete pre-refactor inventory](documentation_inventory.md) records the
existing material before migration. Scientific behavior is outside this task.

## Information architecture

| Area | Job | Canonical content |
| --- | --- | --- |
| Home | Explain the project and orient visitors | One concept, one pipe, four destinations |
| Learn | Teach progressively | Seven short lessons, installation, quickstart |
| Library | Find environmental data | Noun definitions and catalog-driven source facts |
| Documents | Specify software behavior | Verbs, APIs, objects, grammar, validation, development |
| Vignettes | Work through an analysis | Real-data notebooks, workflows, recipes, dependency designs |

## Page migration map

| Previous route / collection | New canonical destination | Preservation strategy |
| --- | --- | --- |
| `quickstart.md`, Get Started tab | Learn | Keep quickstart URL; add a progressive sequence |
| `data/index.md`, climate and surface summaries | Library noun pages | Old indexes link to generated canonical entries |
| Provider facts in `datasets/` | Library source pages | Preserve operational recipes, QA figures and citations at old routes |
| `api/verbs.md`, `reference/verbs_*.md` | Documents → Verbs | Keep former routes as indexes to the generated references |
| `function_inventory.md` | Documents → Verbs / API | Keep developer inventory separate from public reference |
| `documentation/index.md` | Documents | Preserve URL; replace gallery with a reference directory |
| Core notebooks | Vignettes | Preserve code and narrative; add a common reproducibility shell |
| Duplicate gridMET / Sentinel-2 examples | Canonical live recipes | Preserve old URLs as short links, not second implementations |
| Empty anomaly/variance how-tos | Supported references and workflows | Replace stubs with specific destinations and interpretation guidance |
| Cross-source correlation example | Alignment method guide | Remove unsupported module claims and unvalidated result claims |
| Decision Lab and domain workflows | Vignettes | Preserve scientific material and explicit blocked status |
| Concepts, streaming, visualization, development | Learn supplements / Documents | Preserve URLs; link from canonical directories |

## Page contracts

- Noun: definition, Quick facts, Usage, Available sources, Returned data,
  Minimal reproducible example, Quality and provenance, See also.
- Source: Provider, Product, What it provides, Coverage, Resolution, Temporal
  coverage, Access method, Available CubeDynamics nouns, Current QA/certification
  status, Serving revision / provenance information, Important limitations,
  Examples using this source.
- Verb: definition, Usage, Arguments, Accepts, Returns, Order / grammar
  behavior, Minimal example, Works with, See also. Unsupported/demo functions
  are labeled rather than presented as scientific workflows.
- Learn: Concept, Tiny example, Explanation, Try it / worked example,
  What to learn next.
- Vignette: Question, Grammar / pipeline, Plain-language interpretation,
  Analysis, Result, Data used, Reproduce, See also. Existing equivalent
  narrative headings are documented in the collection contract.

## Generated and authored ownership

`python scripts/build_reference_docs.py` generates catalog reference pages,
source browsing, public verb pages and their indexes. `--check` checks for
stale files without writing. Catalog facts come only from `data.describe()`;
signatures and parameter descriptions come from Python and docstrings. Small
editorial annotations supply categories, real-data examples and cross-links,
not a second data registry. New catalog nouns/sources appear automatically;
their category falls back to Other until an editor classifies them.

Tutorial explanations, analysis narratives, source-method notes, and the Home
page remain authored. Notebook builders remain the source of notebook content.
Do not hand-edit generated references or duplicate argument lists in tutorials.

## Validation and maintenance

Run reference generation, the documentation consistency tests, the strict
MkDocs build, and the existing vignette runner. CI checks reference freshness
before building. This keeps the existing MkDocs stack and publication pipeline;
no second site or scientific catalog is introduced.

## Completed implementation · 27 August 2026

- Inventory: 213 Markdown/notebook sources recorded before the refactor.
- Reference generation: 65 pages covering eight catalog nouns, three source
  flavors, 51 public verbs/callable helpers, and their directories. The Library
  lists implemented entries only; candidate sources remain explicitly separate.
- Progressive teaching: seven Learn lessons with a shared observed PRISM input.
- Examples: 31 verb-reference examples execute on that reviewed real fixture.
  Optional/live workflows link to their acquisition and interpretation context.
- Notebook structure: eight core notebooks plus Working Lands gain Data used,
  Reproduce and See also sections with explicit equivalent narrative headings.
  All nine analysis code-cell sequences are unchanged.
- Authored recipes: a common eight-section template; climate/NDVI live recipes
  distinguish variance from standardized departures and disclose execution scope.
- API reference: Pipe, objects, source lifecycle and visualization use source
  signatures/docstrings; the verb generator accommodates historical docstring
  headings without reproducing parameter sections twice.
- Presentation: quieter reference/lesson typography, clear page-role labels,
  accessible active-tab contrast, and the existing deferred homepage viewer.
- Build integration: reference freshness and built-page link checks in both
  documentation CI and the Pages deployment workflow. Notebook links are
  translated from source paths into published URLs; raw theme overrides are
  excluded from site output.

### Duplication removed

The old data-category and provider directories now point to canonical catalog
facts. Six manually maintained verb-family pages and the former verb API index
are compatibility directories. gridMET and Sentinel-2 example routes link to
one maintained recipe each. Repeated recipe lists and homepage explanations
were reduced. Existing scientific notebooks, method reports, QA figures,
citations and useful historical routes were retained.

### Verified locally

| Check | Outcome |
| --- | --- |
| Offline pytest suite (`not integration and not online`) | 467 passed, 5 skipped, 9 deselected |
| `python scripts/run_vignettes.py` | All nine notebooks executed; required static plot counts passed |
| `python scripts/build_reference_docs.py --check` | 65 generated pages current |
| `mkdocs build --strict` | Passed; all notebook pages rendered |
| `python scripts/check_site_links.py <site-dir>` | Internal targets and fragments resolved, including notebook links |
| Repository-size policy, tracked files | Passed |
| `git diff --check` | Passed |
| Package and notebook-code comparison | No `src/` or `code/` changes; nine notebook code sequences unchanged |
| Browser review | Library, verb reference, notebook figure/link, homepage deferred loading and 390-pixel layout inspected |

The browser review verified a notebook-to-noun link by clicking it. The Library
stays within the mobile viewport; wide reference tables scroll. The viewed
array notebook has its static plot and HTML iframe. Build output still includes
third-party banners, local Jupyter transport warnings, and revision-date notices
for uncommitted pages; these are not scientific certification results.

### Remaining gaps and boundaries

1. Live provider endpoints and long-record/satellite recipes were not rerun or
   recertified. Metadata reports the catalog's validity/health declarations,
   not today's availability. Cross-source climate/NDVI correlation remains a
   method guide until a complete alignment and quality-control workflow exists.
2. Some public helpers have sparse docstrings. Their argument names/defaults
   are exact, but missing descriptions and return contracts are disclosed.
   Twenty reference entries use a linked workflow or an explicit limitation
   instead of a standalone tested example; these include optional fire/Landsat/
   Lexcube helpers and reserved APIs. No substitute observations were fabricated.
3. `fit_model` and `correlation_cube` remain unimplemented; `vase_demo` remains
   a synthetic geometry compatibility helper and is not promoted as science.
   No new nouns, sources or scientific operations were implemented here.
4. Historical advanced recipes and manuscripts retain their original method
   detail; their inclusion is not fresh scientific review. The eight-section
   contract is enforced for supported notebooks and the maintained recipes,
   with the author template available for further legacy normalization.
5. The homepage cube still uses the existing renderer. Its legacy camera/axis
   presentation needs a dedicated viewer review; this documentation refactor
   does not claim to repair that renderer or migrate Fire plotting.
6. Changes are local. No commit, push, live website deployment, new data
   certification or package release was performed.

For a future audit, `python scripts/audit_documentation.py` prints the current
inventory. Use `--output <new-path>` to create a new snapshot; existing snapshots
are never overwritten. Do not regenerate the pre-refactor evidence in place.
