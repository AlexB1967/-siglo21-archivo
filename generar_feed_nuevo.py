import requests
import json

URL = "https://api.rtve.es/api/programas/2082/audios.json"

r = requests.get(
    URL,
    params={"size": 1, "page": 1},
    timeout=30
)
r.raise_for_status()

datos = r.json()
page = datos.get("page", {})
items = page.get("items", [])

print("TOTAL:", page.get("total"))
print("TOTAL PAGES:", page.get("totalPages"))
print("ELEMENTOS RECIBIDOS:", len(items))

if not items:
    print("NO HAY ITEMS")
else:
    item = items[0]

    print("\n--- CLAVES DEL PRIMER ITEM ---")
    print(sorted(item.keys()))

    print("\n--- PRIMER ITEM COMPLETO ---")
    print(json.dumps(item, ensure_ascii=False, indent=2))
