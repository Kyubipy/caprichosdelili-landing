"""
Scraper de precios sin gluten - Caprichos de Lili
Corre cada día via GitHub Actions cron
Output: data/canasta.json

Estrategia:
1. Fallback con productos verificados manualmente (siempre funcionan)
2. Intenta scrapear Los Jardines, Casa Rica, Artesanales
3. Si scrapeo falla, mantiene fallback
4. Si scrapeo funciona, mergea productos nuevos
"""

import json
import re
import sys
from datetime import datetime
from pathlib import Path

import requests
from bs4 import BeautifulSoup

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36"
TIMEOUT = 15

# Productos verificados manualmente (5-may-2026)
# Estos siempre se incluyen aunque el scraper falle
FALLBACK_PRODUCTS = [
    # === PANIFICADOS ===
    {"category": "panificados", "name": "Pan para Hamburguesa", "brand": "Artesanales Gluten Free", "size": "unidad", "price": 8000, "provider": "Artesanales Gluten Free", "source": "manual"},
    {"category": "panificados", "name": "Pan de Molde Lactal", "brand": "Artesanales Gluten Free", "size": "entero", "price": 32000, "provider": "Artesanales Gluten Free", "source": "manual"},
    {"category": "panificados", "name": "Pan para Pancho", "brand": "Artesanales Gluten Free", "size": "pack 6 unid.", "price": 28000, "provider": "Artesanales Gluten Free", "source": "manual"},
    {"category": "panificados", "name": "Pan Árabe con leche", "brand": "Artesanales Gluten Free", "size": "pack 6 unid.", "price": 28000, "provider": "Artesanales Gluten Free", "source": "manual"},
    {"category": "panificados", "name": "Pan de Molde Caprichos de Lili", "brand": "Caprichos de Lili", "size": "entero rebanado", "price": 35000, "provider": "Caprichos de Lili", "source": "manual", "highlight": True},
    {"category": "panificados", "name": "Pan de Hamburguesa Caprichos", "brand": "Caprichos de Lili", "size": "pack x4", "price": 36000, "provider": "Caprichos de Lili", "source": "manual", "highlight": True},
    {"category": "panificados", "name": "Pre-pizza Caprichos", "brand": "Caprichos de Lili", "size": "grande", "price": 25000, "provider": "Caprichos de Lili", "source": "manual", "highlight": True},

    # === PASTAS ===
    {"category": "pastas", "name": "Gnocchi di Patate sin gluten", "brand": "La Molisana", "size": "500g", "price": 31000, "provider": "Casa Rica", "source": "manual"},
    {"category": "pastas", "name": "Ñoquis de papa Caprichos", "brand": "Caprichos de Lili", "size": "200g (al vacío)", "price": 20000, "provider": "Caprichos de Lili", "source": "manual", "highlight": True},
    {"category": "pastas", "name": "Lasaña Caprichos (Chica)", "brand": "Caprichos de Lili", "size": "1 unidad", "price": 45000, "provider": "Caprichos de Lili", "source": "manual", "highlight": True},

    # === GALLETITAS Y SNACKS ===
    {"category": "galletitas", "name": "Kukitas Lievito Banana Split", "brand": "Lievito", "size": "100g", "price": 8500, "provider": "Los Jardines", "source": "manual"},
    {"category": "galletitas", "name": "Rosquita El Almacén del Celíaco", "brand": "El Almacén del Celíaco", "size": "120g", "price": 25000, "provider": "Los Jardines", "source": "manual"},
    {"category": "galletitas", "name": "Pepas con dulce de guayaba", "brand": "Artesanales Gluten Free", "size": "unidad", "price": 11000, "provider": "Artesanales Gluten Free", "source": "manual"},

    # === BEBIDAS ===
    {"category": "bebidas", "name": "Leche de avena Nude original", "brand": "Nude", "size": "1 litro", "price": 33000, "provider": "Los Jardines", "source": "manual"},
]


def scrape_los_jardines() -> list:
    """Scrape losjardinesonline.com.py/Glutenfree.2 - 23 productos esperados"""
    products = []
    base_url = "https://losjardinesonline.com.py/Glutenfree.2"
    try:
        for page in range(1, 5):
            url = f"{base_url}?page={page}" if page > 1 else base_url
            r = requests.get(url, headers={"User-Agent": UA}, timeout=TIMEOUT)
            if r.status_code != 200:
                continue
            soup = BeautifulSoup(r.text, "html.parser")

            # Buscar items de producto - estructura típica de Magento/Prestashop
            items = soup.select(".product-item, .product, [class*='product-card'], .item-product")
            if not items:
                items = soup.select("article")

            for item in items:
                name_el = item.select_one(".product-name, .product-title, h3, h2, .name, a[title]")
                price_el = item.select_one(".price, .product-price, [class*='price']")
                if not name_el or not price_el:
                    continue

                name = name_el.get("title") or name_el.get_text(strip=True)
                price_text = price_el.get_text(strip=True)
                price_match = re.search(r"[\d.]+", price_text.replace(".", ""))
                if not price_match:
                    continue
                try:
                    price = int(price_match.group().replace(".", ""))
                except ValueError:
                    continue

                if price < 1000 or price > 500000:  # filtro sanidad
                    continue

                products.append({
                    "category": _infer_category(name),
                    "name": name[:120],
                    "brand": "",
                    "size": "",
                    "price": price,
                    "provider": "Los Jardines",
                    "source": "scrape",
                })

        print(f"  Los Jardines: {len(products)} productos scrapeados", file=sys.stderr)
    except Exception as e:
        print(f"  Los Jardines ERROR: {e}", file=sys.stderr)
    return products


def scrape_artesanales() -> list:
    """Scrape artesanalesglutenfree.com - tiene HTML simple"""
    products = []
    try:
        r = requests.get("https://artesanalesglutenfree.com/", headers={"User-Agent": UA}, timeout=TIMEOUT)
        if r.status_code != 200:
            return products
        soup = BeautifulSoup(r.text, "html.parser")
        # WooCommerce typical structure
        for item in soup.select("li.product, .woocommerce-loop-product__title, .product"):
            name_el = item.select_one(".woocommerce-loop-product__title, h2, h3, .name")
            price_el = item.select_one(".price, .woocommerce-Price-amount, bdi")
            if not name_el or not price_el:
                continue
            name = name_el.get_text(strip=True)
            price_text = price_el.get_text(strip=True)
            price_match = re.search(r"[\d.]+", price_text.replace(".", ""))
            if not price_match:
                continue
            try:
                price = int(price_match.group().replace(".", ""))
            except ValueError:
                continue
            if price < 1000 or price > 500000:
                continue
            products.append({
                "category": _infer_category(name),
                "name": name[:120],
                "brand": "Artesanales Gluten Free",
                "size": "",
                "price": price,
                "provider": "Artesanales Gluten Free",
                "source": "scrape",
            })
        print(f"  Artesanales: {len(products)} productos scrapeados", file=sys.stderr)
    except Exception as e:
        print(f"  Artesanales ERROR: {e}", file=sys.stderr)
    return products


def _infer_category(name: str) -> str:
    n = name.lower()
    if any(w in n for w in ["pan ", "pre-pizza", "prepizza", "tortilla"]):
        return "panificados"
    if any(w in n for w in ["fideo", "pasta", "ñoqui", "lasaña", "gnocchi", "spaghetti", "ravioli"]):
        return "pastas"
    if any(w in n for w in ["galletit", "cookie", "rosquit", "snack", "kukitas", "pepas", "alfajor"]):
        return "galletitas"
    if any(w in n for w in ["leche", "bebida", "jugo", "agua", "yerba", "cafe"]):
        return "bebidas"
    if any(w in n for w in ["harina", "almidón", "fécula", "premezcla"]):
        return "harinas"
    if any(w in n for w in ["salsa", "aderezo", "mayonesa", "ketchup", "mostaza"]):
        return "salsas"
    return "otros"


def merge_products(fallback: list, scraped: list) -> list:
    """Merge fallback con scraped. Si hay duplicado (mismo name+provider), prefiere scraped."""
    seen = set()
    merged = []
    # Scraped primero (datos frescos)
    for p in scraped:
        key = (p["name"].lower().strip(), p["provider"].lower())
        if key in seen:
            continue
        seen.add(key)
        merged.append(p)
    # Fallback después si no estaba ya
    for p in fallback:
        key = (p["name"].lower().strip(), p["provider"].lower())
        if key in seen:
            continue
        seen.add(key)
        merged.append(p)
    return merged


def main():
    print("Scraping canasta sin gluten Paraguay...", file=sys.stderr)
    scraped = []
    scraped += scrape_los_jardines()
    scraped += scrape_artesanales()

    products = merge_products(FALLBACK_PRODUCTS, scraped)

    # Ordenar: highlight Caprichos primero, después por categoría y precio
    products.sort(key=lambda p: (
        not p.get("highlight", False),
        p["category"],
        p["price"],
    ))

    output = {
        "updated_at": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
        "updated_at_human": datetime.utcnow().strftime("%d de %B de %Y"),
        "total_products": len(products),
        "scraped_count": len([p for p in products if p["source"] == "scrape"]),
        "manual_count": len([p for p in products if p["source"] == "manual"]),
        "products": products,
    }

    out_path = Path("data/canasta.json")
    out_path.parent.mkdir(exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"OK {len(products)} productos guardados en {out_path}", file=sys.stderr)
    print(f"  - {output['scraped_count']} scrapeados (frescos)", file=sys.stderr)
    print(f"  - {output['manual_count']} manuales (fallback)", file=sys.stderr)


if __name__ == "__main__":
    main()
