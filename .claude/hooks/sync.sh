#!/bin/sh
# Auto-sync this repo with origin at session start (Leo works from multiple Macs).
# No-ops in non-git dirs / no upstream / already current; never touches a dirty or
# diverged tree (just warns). Committed so it travels to every machine via git.
git rev-parse --is-inside-work-tree >/dev/null 2>&1 || exit 0
git fetch -q --no-tags 2>/dev/null || exit 0
ab=$(git rev-list --left-right --count '@{u}...HEAD' 2>/dev/null) || exit 0
behind=$(printf '%s' "$ab" | awk '{print $1}')
ahead=$(printf '%s' "$ab" | awk '{print $2}')
branch=$(git rev-parse --abbrev-ref HEAD 2>/dev/null)
[ "${behind:-0}" -gt 0 ] || exit 0
if [ "${ahead:-0}" -eq 0 ] && [ -z "$(git status --porcelain 2>/dev/null)" ]; then
  git merge --ff-only -q '@{u}' 2>/dev/null \
    && printf '{"systemMessage":"git: fast-forwarded %s +%s from origin"}\n' "$branch" "$behind"
else
  printf '{"systemMessage":"git: %s is %s behind origin, not fast-forwarded (dirty/diverged) — reconcile"}\n' "$branch" "$behind"
fi
exit 0
