#!/bin/bash
# check-sitemap.sh — verifica que sitemap.xml liste TODOS los articulos blog tracked
# Uso: ./check-sitemap.sh
# Exit code 0 si OK, 1 si falta alguna URL.
#
# Roberto pidio "que no se repita" — el bug ya ocurrio (5 artículos faltantes,
# detectado el 30-jun-2026).

set -e
cd "$(dirname "$0")"

REAL=$(mktemp); LISTED=$(mktemp); MISSING=$(mktemp)
trap "rm -f $REAL $LISTED $MISSING" EXIT

# Articulos blog tracked en git (excluyendo redirects con meta refresh)
for d in blog/*/; do
    name=$(basename "$d")
    [ -f "$d/index.html" ] || continue
    git ls-files --error-unmatch "$d/index.html" >/dev/null 2>&1 || continue
    grep -q 'meta http-equiv="refresh"' "$d/index.html" 2>/dev/null && continue
    echo "https://caprichosdelili.com/blog/$name/" >> "$REAL"
done

# URLs en sitemap.xml
grep -oE '<loc>https://caprichosdelili.com/blog/[^<]+</loc>' sitemap.xml | sed 's|</loc>||;s|<loc>||' | sort -u > "$LISTED"

sort -u "$REAL" -o "$REAL"
comm -23 "$REAL" "$LISTED" > "$MISSING"

if [ -s "$MISSING" ]; then
    echo "❌ Articulos tracked pero NO en sitemap.xml:"
    cat "$MISSING" | sed 's/^/  - /'
    exit 1
else
    echo "✓ Todos los articulos blog tracked estan en sitemap.xml"
    exit 0
fi
