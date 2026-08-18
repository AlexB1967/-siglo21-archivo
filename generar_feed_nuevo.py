import requests

URL = "https://api.rtve.es/api/programas/2002/audios.json"

for pagina in [1, 2]:
    print("\n==============================")
    print(f"PROBANDO PAGINA {pagina}")
    print("==============================")

    r = requests.get(
        URL,
        params={
            "size": 1,
            "page": pagina
        },
        timeout=30
    )

    print("URL REAL:", r.url)
    print("STATUS:", r.status_code)

    r.raise_for_status()

    data = r.json()
    page = data.get("page", {})

    print("number:", page.get("number"))
    print("size:", page.get("size"))
    print("offset:", page.get("offset"))
    print("total:", page.get("total"))
    print("totalPages:", page.get("totalPages"))
    print("numElements:", page.get("numElements"))

    items = page.get("items", [])
    print("items recibidos:", len(items))

    if items:
        primero = items[0]
        print("id:", primero.get("id"))
        print("titulo:", primero.get("longTitle") or primero.get("title"))
        print("htmlUrl:", primero.get("htmlUrl"))
