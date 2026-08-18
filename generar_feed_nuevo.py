import requests
import xml.etree.ElementTree as ET
from email.utils import formatdate
from datetime import datetime
import time
import re

URL = "https://api.rtve.es/api/programas/2002/audios.json"

# Pedimos muchos episodios por página para reducir el número de consultas
PAGE_SIZE = 1

todos = []
page = 0

print("Descargando archivo de Siglo 21...")

while True:
    print(f"Página {page}...")

    r = requests.get(
        URL,
        params={"size": PAGE_SIZE, "page": page},
        timeout=30
    )
    r.raise_for_status()

    data = r.json()
    
    print("CLAVES DATA:", data.keys())
    print("TIPO PAGE:", type(data.get("page")))
    print("CONTENIDO PAGE:", data.get("page"))
    break
    pagina = data.get("page", {})
    items = pagina.get("items", [])

    if not items:
        break

    todos.extend(items)

    total = pagina.get("total", len(todos))

    if len(todos) >= total:
        break

    page += 1
    time.sleep(0.1)

print(f"Total recuperados: {len(todos)}")


def fecha_item(item):
    fecha = item.get("pubState", {}).get("pubDate")
    if not fecha:
        fecha = item.get("publicationDate")
    if not fecha:
        fecha = item.get("dateOfEmission")

    if isinstance(fecha, dict):
        fecha = fecha.get("date")

    return fecha or ""


# Ordenamos del más antiguo al más reciente
todos.sort(key=fecha_item)


rss = ET.Element(
    "rss",
    {
        "version": "2.0",
        "xmlns:itunes": "http://www.itunes.com/dtds/podcast-1.0.dtd"
    }
)

channel = ET.SubElement(rss, "channel")

ET.SubElement(channel, "title").text = "Siglo 21 - Archivo histórico"
ET.SubElement(channel, "link").text = "https://www.rtve.es/play/audios/siglo-21/"
ET.SubElement(channel, "description").text = (
    "Archivo histórico de Siglo 21 - Radio 3 (RTVE), "
    "ordenado del más antiguo al más reciente."
)
ET.SubElement(channel, "language").text = "es"


incluidos = 0

for episodio in todos:

    titulo = (
        episodio.get("longTitle")
        or episodio.get("title")
        or episodio.get("shortTitle")
        or "Siglo 21"
    )

    enlace = episodio.get("htmlUrl") or episodio.get("url") or ""

    descripcion = (
        episodio.get("description")
        or episodio.get("shortDescription")
        or ""
    )

    # Quitamos etiquetas HTML de la descripción
    descripcion = re.sub("<[^>]+>", "", descripcion)

    fecha = fecha_item(episodio)

    item_xml = ET.SubElement(channel, "item")

    ET.SubElement(item_xml, "title").text = titulo
    ET.SubElement(item_xml, "link").text = enlace
    ET.SubElement(item_xml, "description").text = descripcion

    guid = ET.SubElement(item_xml, "guid")
    guid.text = str(episodio.get("id", enlace))
    guid.set("isPermaLink", "false")

    # Intentamos convertir la fecha al formato RSS
    if fecha:
        try:
            timestamp = int(fecha) / 1000
            ET.SubElement(item_xml, "pubDate").text = formatdate(
                timestamp,
                usegmt=True
            )
        except (ValueError, TypeError):
            pass

    incluidos += 1


tree = ET.ElementTree(rss)
ET.indent(tree, space="  ")

tree.write(
    "feed.xml",
    encoding="utf-8",
    xml_declaration=True
)

print(f"Feed creado correctamente: feed.xml")
print(f"Episodios incluidos: {incluidos}")
