import importlib.util
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
_SCORE = _ROOT / "eval" / "score.py"
_SPEC = importlib.util.spec_from_file_location("eval_score", _SCORE)
_MODULE = importlib.util.module_from_spec(_SPEC)
sys.modules["eval_score"] = _MODULE
assert _SPEC.loader is not None
_SPEC.loader.exec_module(_MODULE)
