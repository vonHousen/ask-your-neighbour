from io import BytesIO

from agents import function_tool
from owslib.wms import WebMapService
from PIL import Image

WMS_OSM_URL = " https://ows.terrestris.de/osm/service?VERSION=1.3.0&REQUEST=GetCapabilities"
LAYERS_OSM = ["OSM-WMS"]

WMS_GEOPORTAL_URL = "https://mapy.geoportal.gov.pl/wss/ext/KrajowaIntegracjaNumeracjiAdresowej?SERVICE=WMS&REQUEST=GetCapabilities"

LAYERS_GEOPORTAL = (
    "prg-ulice",
    "prg-adresy",
    "prg-place",
)


def _fetch_wms_map(xmin: float, ymin: float, xmax: float, ymax: float, wms_url: str, wms_layers: list[str]) -> Image:
    wms = WebMapService(wms_url, version="1.3.0")

    height = 720

    width = int(height * (xmax - xmin) * 0.75 / (ymax - ymin))  # 0.75 - correction for Poland latitude

    return Image.open(BytesIO(wms.getmap(
        layers=wms_layers,
        size=[width, height],
        srs="EPSG:4326",
        bbox=[xmin, ymin, xmax, ymax],
        format="image/png",
        transparent=True).read()))


@function_tool
async def fetch_map(xmin: float,  # EPSG:4326
                    ymin: float,  # EPSG:4326
                    xmax: float,  # EPSG:4326
                    ymax: float  # EPSG:4326
                    ) -> Image:
    """
    Fetch a map for a box defined by the coordinates (xmin, ymin, xmax, ymax) in  EPSG:4326 stabdard.

    Args:
        xmin (float): Minimum x coordinate (longitude).
        ymin (float): Minimum y coordinate (latitude).
        xmax (float): Maximum x coordinate (longitude).
        ymax (float): Maximum y coordinate (latitude).
    """
    image_osm = _fetch_wms_map(xmin, ymin, xmax, ymax, WMS_OSM_URL, LAYERS_OSM)
    image_geoportal = _fetch_wms_map(xmin, ymin, xmax, ymax, WMS_GEOPORTAL_URL, LAYERS_GEOPORTAL)

    combined_image = Image.new("RGBA", image_osm.size)
    combined_image.paste(image_osm)

    combined_image.paste(image_geoportal, mask=image_geoportal)  # Using overlay_image as mask for transparency

    return combined_image
