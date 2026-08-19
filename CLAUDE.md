# CLAUDE.md — caprichosdelili.com

Sitio comercial de comida sin gluten (dark kitchen, Asunción PY). HTML estático + Tailwind CDN, sin build step. Dueños: Roberto Rodas + Dra. Norma Borja.

## Reglas editoriales (NO negociables)

- **NUNCA mencionar marcas, locales ni precios de competidores.** Críticas al mercado solo generalizadas.
- **NUNCA inventar datos**: ni reviews, ni ratings, ni información nutricional, ni precios sin fuente real. Los únicos precios concretos publicables son los propios (fuente: /pack-semanal/).
- **Sin drama personal** de los fundadores (nada de temas médicos personales) — es un sitio de comidas.
- Naming: "Pizzeta XL" (no "pre-pizza"), milanesas sin el adjetivo "grandes".
- Es dark kitchen: SIN dirección pública, horario WhatsApp L-V 8:00-19:00, pedidos con 3 días de anticipación, todo congelado al vacío. No es restaurante.
- Autora médica de los posts: "Dra. Norma Liliana Borja". Tono: español paraguayo (vos), cálido y honesto.

## Pipeline de publicación de un post

1. Investigar con agente (todo dato con fuente; lo no verificable NO se publica)
2. Escribir siguiendo el template de `blog/harinas-sin-gluten-guia-completa/` (head completo: title <60, description <155, OG + Twitter cards, schema Article + FAQPage + BreadcrumbList, `?plugins=typography` en el CDN de Tailwind)
3. Imagen hero: Gemini API → WebP 1200×630 en `assets/img/blog/{slug}.webp`, sin texto ni logos, verificada por agente revisor
4. Verificación adversarial por segundo agente ANTES de publicar
5. Agregar al listado de `blog/index.html` + `sitemap.xml` (con lastmod)
6. Commit + push a main → GitHub Actions deploya solo (~40 s)
7. Ping IndexNow (key en `19c7fca3d44a433d9b73767c6a4d5322.txt` del root)

## Deploy

Auto-deploy en push a main (Cloudflare Workers Static Assets, cuenta corporativa robertorodas@caprichosdelili.com). Archivos grandes nuevos: agregarlos a `.assetsignore` además de `.gitignore`.
