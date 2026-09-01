* config.do — project globals
* Include at the top of every do-file: include "[relative path to]/code/config.do"

set more off
set linesize 120

* ── Project root ────────────────────────────────────────────────────────────
global root "{{PROJECT_ROOT}}"

* ── Data ────────────────────────────────────────────────────────────────────
global raw    "$root/data/raw"
global clean  "$root/data/clean"

* ── Code ────────────────────────────────────────────────────────────────────
global download  "$root/code/download"
global code_data "$root/code/data"
global analysis  "$root/code/analysis"

* ── Output ──────────────────────────────────────────────────────────────────
global tables  "$root/output/tables"
global figures "$root/output/figures"
global logs    "$root/output/logs"

* ── Log setup (uncomment to activate in any do-file) ────────────────────────
* cap log close
* log using "$logs/${SCRIPTNAME}.log", replace text
