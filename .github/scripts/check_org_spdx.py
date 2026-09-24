#!/usr/bin/env python3
# SPDX-License-Identifier: MPL-2.0
"""本组织新增文件的 SPDX 头检查（panel-starter-kit spec/02 CONV-25）。

内核 fork 只检查本组织新增的文件：相对上游基点（Xboard-Node 所用的提交）新增的已跟踪文件，
前两行之内必须有 SPDX-License-Identifier；REUSE.toml 中以 precedence = "override" 登记的
路径除外。上游文件与对上游文件的修改不检查。

用法：check_org_spdx.py <上游基点提交>
"""

import re
import subprocess
import sys
import tomllib

TAG = "SPDX-License-" + "Identifier:"


def glob_to_regex(pattern: str) -> re.Pattern:
    # REUSE.toml 的匹配规则：* 不跨越 /，** 跨越 /，\* 为字面量 *。
    out, i = "", 0
    while i < len(pattern):
        if pattern.startswith("\\*", i):
            out, i = out + re.escape("*"), i + 2
        elif pattern.startswith("**", i):
            out, i = out + ".*", i + 2
        elif pattern[i] == "*":
            out, i = out + "[^/]*", i + 1
        else:
            out, i = out + re.escape(pattern[i]), i + 1
    return re.compile(out + r"\Z")


def registered_patterns() -> list[re.Pattern]:
    try:
        with open("REUSE.toml", "rb") as f:
            data = tomllib.load(f)
    except FileNotFoundError:
        return []
    patterns = []
    for ann in data.get("annotations", []):
        if ann.get("precedence") != "override":
            continue
        paths = ann["path"]
        for p in [paths] if isinstance(paths, str) else paths:
            patterns.append(glob_to_regex(p))
    return patterns


def main() -> int:
    if len(sys.argv) != 2:
        print(__doc__)
        return 2
    base = sys.argv[1]
    added = subprocess.run(
        ["git", "diff", "--name-only", "--diff-filter=A", "-z", base, "HEAD"],
        check=True, capture_output=True,
    ).stdout.decode().split("\0")
    patterns = registered_patterns()
    missing = []
    for path in added:
        if not path or any(p.match(path) for p in patterns):
            continue
        with open(path, encoding="utf-8", errors="replace") as f:
            head = [f.readline(), f.readline()]
        if not any(TAG in line for line in head):
            missing.append(path)
    if missing:
        print(f"以下本组织新增的文件（相对 {base}）缺少 SPDX 头（前两行之内），或应在 REUSE.toml 中登记：")
        print("\n".join(missing))
        return 1
    print(f"check-org-spdx: 通过（相对 {base} 新增 {len([p for p in added if p])} 个文件）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
