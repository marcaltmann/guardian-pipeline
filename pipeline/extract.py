"""Extract top-level array literals (e.g. `pb`, `gb`) from the Guardian app.js.

app.js is a minified browser bundle, so the data arrays live as `const`/bare
assignments inside a closure and cannot be reached by *running* the file. We
instead pull the array literal out as text and evaluate it.

The literal is JavaScript, not JSON (unquoted keys, and `gb` uses the minified
booleans `!0`/`!1`). Rather than re-implement JS semantics in Python, we hand
the literal to `node` to `eval` and return as JSON — node understands the JS
syntax (`!0`/`!1`, etc.) natively, with no preprocessing.

Requires `node` on PATH. Public API:
    find_array_literal(src, name) -> str   # the raw "[...]" text (pure Python)
    extract_array(src, name)      -> list  # parsed Python list (via node)
    normalize_decoded(obj)        -> obj   # NFC + whitespace-trim of the decode
"""

import json
import re
import subprocess
import unicodedata
from typing import Any

# Matches `pb = [`, `const gb = [`, `let x=[`, etc. — optional declaration
# keyword, flexible whitespace. Word boundary so `gb` doesn't match `agb`.
_DECL = r'(?:\b(?:const|let|var)\s+)?\b{name}\s*=\s*\['

# Node program: read the literal from stdin, eval it, write JSON to stdout.
_NODE_EVAL = (
    "const src = require('fs').readFileSync(0, 'utf8');"
    "process.stdout.write(JSON.stringify(eval('(' + src + ')')));"
)


def find_array_literal(src: str, name: str) -> str:
    """Return the `[...]` literal assigned to `name`, brackets included.

    Uses a string-aware bracket scan: brackets and quotes appearing *inside*
    string values (e.g. blurbs) are ignored, so nesting is matched correctly.
    """
    m = re.search(_DECL.format(name=re.escape(name)), src)
    if m is None:
        raise ValueError(f'Could not find an array assignment for {name!r}')

    open_bracket = m.end() - 1  # index of the matched '['

    depth = 0
    in_string: str | None = None  # the active quote char (" ' or `), or None
    i = open_bracket
    while i < len(src):
        ch = src[i]
        if in_string is not None:
            if ch == '\\':  # escaped char inside a string
                i += 2
                continue
            if ch == in_string:
                in_string = None
        elif ch in '"\'`':
            in_string = ch
        elif ch == '[':
            depth += 1
        elif ch == ']':
            depth -= 1
            if depth == 0:
                return src[open_bracket : i + 1]
        i += 1

    raise ValueError(f'Unterminated array literal for {name!r}')


def _eval_with_node(literal: str) -> Any:
    """Evaluate a JS array literal via node and return it as a Python object."""
    try:
        proc = subprocess.run(
            ['node', '-e', _NODE_EVAL],
            input=literal,
            capture_output=True,
            encoding='utf-8',
            check=True,
        )
    except FileNotFoundError as e:
        raise RuntimeError(
            'node not found on PATH — required to evaluate the literal'
        ) from e
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f'node failed to evaluate the literal:\n{e.stderr}') from e
    return json.loads(proc.stdout)


def extract_array(src: str, name: str) -> list[Any]:
    """Find and parse the array literal assigned to `name` into a Python list."""
    return _eval_with_node(find_array_literal(src, name))


def normalize_decoded(obj: Any) -> Any:
    """Return ``obj`` with every string NFC-normalized and stripped of surrounding
    whitespace, recursing through lists and dicts; non-strings pass through unchanged.

    The Guardian bundle decodes to dirty text: the same name appears in both NFC and
    NFD forms (e.g. ``Brontë``), and some values carry stray leading/trailing
    whitespace (e.g. ``'The Alexandria Quartet '``). Every downstream join is exact
    string equality on ``title``/``author``/``slug``, so an un-normalized key silently
    fails to match — and the hand-curated id tables are NFC and trimmed. Canonicalizing
    here, at the one point the arrays are decoded, keeps every later comparison aligned.
    Internal whitespace is preserved; only the ends are trimmed.
    """
    if isinstance(obj, str):
        return unicodedata.normalize('NFC', obj).strip()
    if isinstance(obj, list):
        return [normalize_decoded(v) for v in obj]
    if isinstance(obj, dict):
        return {k: normalize_decoded(v) for k, v in obj.items()}
    return obj
