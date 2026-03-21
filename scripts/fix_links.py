#!/usr/bin/env python3
"""Fix relative links in protocol markdown files after reorganization.

Scans all .md files for relative links like [Text](../old-dir/file.md)
and updates them to point to the correct new location.
"""

import os
import re
from pathlib import Path

PROTOCOLS_DIR = Path("protocols")

def build_file_map():
    """Build a map of filename -> current relative path from protocols/."""
    file_map = {}
    for md_file in PROTOCOLS_DIR.rglob("*.md"):
        if md_file.name == "_template.md":
            continue
        # Map filename to its path relative to protocols/
        rel = md_file.relative_to(PROTOCOLS_DIR)
        file_map[md_file.name] = str(rel)
    return file_map

def fix_links_in_file(filepath, file_map):
    """Fix all relative markdown links in a file."""
    with open(filepath, 'r') as f:
        content = f.read()

    # Pattern: [text](relative/path/to/file.md)
    # Match any relative link ending in .md
    link_pattern = re.compile(r'\]\(([^)]*\.md)\)')

    file_dir = filepath.parent
    changes = []

    def replace_link(match):
        old_link = match.group(1)

        # Skip absolute URLs
        if old_link.startswith('http'):
            return match.group(0)

        # Resolve the target filename
        target_filename = os.path.basename(old_link)

        # Look up where this file actually is now
        if target_filename not in file_map:
            return match.group(0)  # Leave as-is if we can't find it

        # Compute correct relative path from current file's directory
        new_abs = PROTOCOLS_DIR / file_map[target_filename]
        try:
            new_rel = os.path.relpath(new_abs, file_dir)
        except ValueError:
            return match.group(0)

        if old_link != new_rel:
            changes.append((old_link, new_rel))

        return f']({new_rel})'

    new_content = link_pattern.sub(replace_link, content)

    if changes:
        with open(filepath, 'w') as f:
            f.write(new_content)
        return changes
    return []

def main():
    file_map = build_file_map()
    print(f"Found {len(file_map)} protocol files")

    total_fixes = 0
    for md_file in sorted(PROTOCOLS_DIR.rglob("*.md")):
        if md_file.name == "_template.md":
            continue
        changes = fix_links_in_file(md_file, file_map)
        if changes:
            print(f"\n{md_file}:")
            for old, new in changes:
                print(f"  {old} -> {new}")
            total_fixes += len(changes)

    print(f"\nTotal link fixes: {total_fixes}")

if __name__ == "__main__":
    main()
