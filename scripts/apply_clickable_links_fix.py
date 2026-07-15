from pathlib import Path

root = Path(__file__).resolve().parents[1]
js_path = root / "site" / "assets" / "js" / "site.js"
test_path = root / "tests" / "site" / "test_static_site.py"

js = js_path.read_text(encoding="utf-8")

anchor = 'const SERIES_COLORS = ["#2f6fed", "#e8590c", "#2f9e44", "#7048e8", "#c2255c"];\n'
helper = '''const SERIES_COLORS = ["#2f6fed", "#e8590c", "#2f9e44", "#7048e8", "#c2255c"];

function repoPathURL(path, kind) {
  const clean = String(path || "").replace(/^\\/+|\\/+$/g, "");
  return ["https:", "", "github.com", "sherlock0717", "llm-attribution-behavior-evaluation",
    kind === "tree" ? "tree" : "blob", "main", clean].join("/");
}
'''
if anchor not in js:
    raise SystemExit("SERIES_COLORS anchor not found")
js = js.replace(anchor, helper, 1)

old_source_docs = '''    li.appendChild(el("span", { className: "ref-doc-note", text: d.note }));
    li.appendChild(el("code", { text: d.path }));
    docs.appendChild(li);'''
new_source_docs = '''    li.appendChild(el("span", { className: "ref-doc-note", text: d.note }));
    const a = el("a", { className: "ref-doc-link" });
    a.href = repoPathURL(d.path, "blob");
    a.target = "_blank";
    a.rel = "noopener";
    a.appendChild(el("code", { text: d.path }));
    li.appendChild(a);
    docs.appendChild(li);'''
if old_source_docs not in js:
    raise SystemExit("research source docs block not found")
js = js.replace(old_source_docs, new_source_docs, 1)

old_dirs = '''    const li = el("li", { className: "kd-row" });
    li.appendChild(el("code", { text: d.path }));
    li.appendChild(el("span", { className: "kd-note", text: d.note }));
    host.appendChild(li);'''
new_dirs = '''    const li = el("li", { className: "kd-row" });
    const a = el("a", { className: "repo-path-link" });
    a.href = repoPathURL(d.path, "tree");
    a.target = "_blank";
    a.rel = "noopener";
    a.appendChild(el("code", { text: d.path }));
    li.appendChild(a);
    li.appendChild(el("span", { className: "kd-note", text: d.note }));
    host.appendChild(li);'''
if old_dirs not in js:
    raise SystemExit("key directories block not found")
js = js.replace(old_dirs, new_dirs, 1)

old_docs = '''    const li = el("li", { className: "doc-row" });
    li.appendChild(el("span", { className: "doc-label", text: d.label }));
    li.appendChild(el("code", { text: d.path }));
    host.appendChild(li);'''
new_docs = '''    const li = el("li", { className: "doc-row" });
    li.appendChild(el("span", { className: "doc-label", text: d.label }));
    const a = el("a", { className: "repo-path-link" });
    a.href = repoPathURL(d.path, "blob");
    a.target = "_blank";
    a.rel = "noopener";
    a.appendChild(el("code", { text: d.path }));
    li.appendChild(a);
    host.appendChild(li);'''
if old_docs not in js:
    raise SystemExit("document entries block not found")
js = js.replace(old_docs, new_docs, 1)

js_path.write_text(js, encoding="utf-8", newline="\n")

tests = test_path.read_text(encoding="utf-8")
addition = '''

# --- final polish: repository paths are clickable ---------------------------

def test_repository_document_paths_are_clickable():
    assert "function repoPathURL(path, kind)" in JS_SRC
    assert 'a.href = repoPathURL(d.path, "blob")' in JS_SRC
    assert 'a.href = repoPathURL(d.path, "tree")' in JS_SRC
    assert JS_SRC.count('a.target = "_blank"') >= 3
    assert JS_SRC.count('a.rel = "noopener"') >= 3


def test_repository_url_targets_current_slug_and_main():
    assert '"llm-attribution-behavior-evaluation"' in JS_SRC
    assert '"main"' in JS_SRC
    assert OLD_SLUG not in JS_SRC
'''
if "test_repository_document_paths_are_clickable" not in tests:
    tests += addition

test_path.write_text(tests, encoding="utf-8", newline="\n")
