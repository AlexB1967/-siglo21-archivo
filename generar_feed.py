import requests
import xml.etree.ElementTree as ET
from email.utils import format_datetime
from datetime import datetime
from html import escape
import time

PROGRAMA_ID = 2082
BASE_API = f"https://api.rtve.es/api/programas/{PROGRAMA_ID}/audios.json"
SALIDA = "feed.xml"

def buscar_valor(obj, claves):
    if isinstance(obj, dict):
        for clave in claves:
            if clave in obj and obj[clave]:
                return obj[clave]

        for valor in obj.values():
            encontrado = buscar_valor(valor, claves)
            if encontrado:
                return encontrado

    elif isinstance(obj, list):
        for elemento in obj:
            encontrado = buscar_valor(elemento, claves)
            if encontrado:
                return encontrado

    return None


def extraer_items(datos):
    if isinstance(datos, dict):
        if "page" in datos and isinstance(datos["page"], dict):
            if "items" in datos["page"]:
                return datos["page"]["items"]

        if "items" in datos and isinstance(datos["items"], list):
            return datos["items"]

        for valor in datos.values():
            resultado = extraer_items(valor)
            if resultado:
                return resultado

    return []


def parsear_fecha(texto):
    if texto is None:
        return None

    # Si RTVE devuelve un objeto, buscamos la fecha dentro
    if isinstance(texto, dict):
        for clave in ["pubDate", "date", "publicationDate", "dateOfEmission"]:
            if clave in texto:
                texto = texto[clave]
                break
        else:
            return None

    # Timestamp Unix, en segundos o milisegundos
    if isinstance(texto, (int, float)):
        try:
            valor = float(texto)
            if valor > 10_000_000_000:
                valor /= 1000
            return datetime.fromtimestamp(valor)
        except (ValueError, TypeError, OSError):
            return None

    texto = str(texto).strip()

    # Timestamp recibido como texto
    if texto.isdigit():
        try:
            valor = float(texto)
            if valor > 10_000_000_000:
                valor /= 1000
            return datetime.fromtimestamp(valor)
        except (ValueError, TypeError, OSError):
            pass

    texto = texto.replace("Z", "+00:00")

    # Primero intentamos ISO
    try:
        return datetime.fromisoformat(texto)
    except ValueError:
        pass

    formatos = [
    "%d-%m-%Y %H:%M:%S",
    "%Y-%m-%dT%H:%M:%S%z",
    "%Y-%m-%dT%H:%M:%S",
    "%Y-%m-%d",
    "%d/%m/%Y",
]

    for formato in formatos:
        try:
            return datetime.strptime(texto, formato)
        except ValueError:
            pass

    formatos = [
        "%Y-%m-%dT%H:%M:%S%z",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%d",
        "%d/%m/%Y",
    ]

    texto = str(texto).replace("Z", "+00:00")

    for formato in formatos:
        try:
            return datetime.strptime(texto, formato)
        except ValueError:
            pass

    return None


print("Recuperando archivo de Siglo 21 desde RTVE...")

todos = []
pagina = 1

while True:
    print(f"Leyendo página {pagina}...")

    respuesta = requests.get(
        BASE_API,
        params={
            "size": 60,
            "page": pagina
        },
        timeout=30
    )

    respuesta.raise_for_status()
    datos = respuesta.json()

    items = extraer_items(datos)

    if not items:
        break

    todos.extend(items)

    pagina += 1
time.sleep(0.3)

print(f"Encontrados {len(todos)} registros.")

print("PRIMER REGISTRO COMPLETO:")
print(todos[0])

print("AUDIO ENCONTRADO:", buscar_valor(
    todos[0],
    ["file", "audioUrl", "downloadUrl", "mediaUrl", "url"]
))

primer_id = buscar_valor(todos[0], ["id"])
print("ID PRIMER AUDIO:", primer_id)

detalle_url = f"https://api.rtve.es/api/audios/{primer_id}.json"
detalle = requests.get(detalle_url, timeout=30)
print("DETALLE STATUS:", detalle.status_code)
print("DETALLE AUDIO:", detalle.json())
    

episodios = []
for incice, item in enumerate(todos):

    titulo = buscar_valor(
        item,
        ["title", "titulo", "name"]
    )

    fecha_texto = buscar_valor(
    item,
    ["publicationDate", "pubDate", "dateOfEmission", "fecha", "pubState"]
)

    pagina_web = buscar_valor(
        item,
        ["htmlUrl", "url", "webUrl"]
    )

    identificador = buscar_valor(
    item,
    ["id"]
)

audio = (
    f"https://ztnr.rtve.es/ztnr/{identificador}.mp3"
    if identificador
    else ""
)

descripcion = buscar_valor(
        item,
        ["description", "shortDescription", "summary"]
)

fecha = parsear_fecha(fecha_texto)


if titulo and fecha:
            episodios.append({
                "titulo": str(titulo),
                "fecha": fecha,
                "pagina": str(pagina_web or ""),
                "audio": str(audio or ""),
                "id": str(identificador or titulo),
                "descripcion": str(descripcion or "")
            })

print("TOTAL TODOS:", len(todos))
print("FECHAS VALIDAS:", sum(1 for x in todos if parsear_fecha(buscar_valor(x, ["publicationDate", "pubDate", "dateOfEmission", "fecha", "pubState"]))))

# El más antiguo primero
episodios.sort(key=lambda x: x["fecha"])

rss = ET.Element(
    "rss",
    {
        "version": "2.0",
        "xmlns:itunes": "http://www.itunes.com/dtds/podcast-1.0.dtd"
    }
)

channel = ET.SubElement(rss, "channel")

ET.SubElement(channel, "title").text = "Siglo 21 - Archivo completo 2008-2021"
ET.SubElement(channel, "description").text = (
    "Archivo histórico de Siglo 21, Radio 3. "
    "Audios alojados originalmente por RTVE."
)
ET.SubElement(channel, "language").text = "es"
ET.SubElement(channel, "link").text = "https://www.rtve.es/play/audios/siglo-21/"

for ep in episodios:

    item = ET.SubElement(channel, "item")

    ET.SubElement(item, "title").text = ep["titulo"]

    ET.SubElement(item, "guid", {"isPermaLink": "false"}).text = ep["id"]

    ET.SubElement(item, "pubDate").text = format_datetime(ep["fecha"])

    ET.SubElement(item, "description").text = ep["descripcion"]

    if ep["pagina"]:
        ET.SubElement(item, "link").text = ep["pagina"]

    if ep["audio"]:
        ET.SubElement(
            item,
            "enclosure",
            {
                "url": ep["audio"],
                "type": "audio/mpeg",
                "length": "0"
            }
        )


arbol = ET.ElementTree(rss)

ET.indent(arbol, space="  ")

arbol.write(
    SALIDA,
    encoding="utf-8",
    xml_declaration=True
)

print(f"Feed generado correctamente: {SALIDA}")
print(f"Episodios incluidos: {len(episodios)}")
