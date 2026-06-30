#!/bin/bash
# check-blog-listing.sh — verifica que blog/index.html liste TODOS los articulos del fs
# Uso: ./check-blog-listing.sh
# Exit code 0 si OK, 1 si falta algun articulo en el listing.
#
# Roberto pidio "que no se repita" — agregar artículos sin actualizar listing
# ya genero el bug de 6 cards faltantes en jun-2026.

set -e
cd "$(dirname "$0")"

REAL=$(mktemp); LISTED=$(mktemp); MISSING=$(mktemp)
trap "rm -f $REAL $LISTED $MISSING" EXIT

# Articulos reales: carpetas con index.html que NO sean redirect (meta refresh)
for d in blog/*/; do
    name=$(basename "$d")
    [ -f "$d/index.html" ] || continue
    grep -q 'meta http-equiv="refresh"' "$d/index.html" 2>/dev/null && continue
    echo "$name" >> "$REAL"
done

# Articulos listados en blog/index.html
grep -oE 'href="/blog/[^"]+/"' blog/index.html | sed 's|href="/blog/||;s|/"||' | sort -u > "$LISTED"

# Falta?
sort -u "$REAL" -o "$REAL"
comm -23 "$REAL" "$LISTED" > "$MISSING"

if [ -s "$MISSING" ]; then
    echo "❌ Articulos en disco pero NO en blog/index.html listing:"
    cat "$MISSING" | sed 's/^/  - /'
    exit 1
else
    echo "✓ Todos los articulos del fs estan en el listing."
    exit 0
fi
