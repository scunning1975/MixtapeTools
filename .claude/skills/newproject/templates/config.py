from pathlib import Path

ROOT = Path("{{PROJECT_ROOT}}")

DATA_RAW    = ROOT / "data" / "raw"
DATA_CLEAN  = ROOT / "data" / "clean"

OUTPUT_FIGURES = ROOT / "output" / "figures"
OUTPUT_TABLES  = ROOT / "output" / "tables"
OUTPUT_LOGS    = ROOT / "output" / "logs"

CODE_DOWNLOAD = ROOT / "code" / "download"
CODE_DATA     = ROOT / "code" / "data"
CODE_ANALYSIS = ROOT / "code" / "analysis"
