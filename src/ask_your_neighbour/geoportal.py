from typing import Any

from agents import RunContextWrapper
from openai import BaseModel
from owslib.wms import WebMapService
from PIL import Image

from ask_your_neighbour.conversation_state import ConversationState
from ask_your_neighbour.utils import LOGGER

WMS_OSM_URL = " https://ows.terrestris.de/osm/service?VERSION=1.3.0&REQUEST=GetCapabilities"
LAYERS_OSM = ["OSM-WMS"]

WMS_GEOPORTAL_URL = "https://mapy.geoportal.gov.pl/wss/ext/KrajowaIntegracjaMiejscowychPlanowZagospodarowaniaPrzestrzennego?SERVICE=WMS&REQUEST=GetCapabilities"

LAYERS_GEOPORTAL = (
    "plany",
    "plany_granice",
    "raster",
    "wektor-str",
    "wektor-lzb",
    "wektor-pow",
    "wektor-lin",
    "wektor-pkt",
    "granice"
)


def _fetch_wms_map(xmin: float, ymin: float, xmax: float, ymax: float, wms_url: str, wms_layers: list[str]) -> Image:
    wms = WebMapService(wms_url, version="1.3.0")

    height = 720

    width = int(height * (xmax - xmin) * 0.75 / (ymax - ymin))  # 0.75 - correction for Poland latitude

    result = wms.getmap(
        layers=wms_layers,
        size=[width, height],
        srs="EPSG:4326",
        bbox=[xmin, ymin, xmax, ymax],
        format="image/png",
        transparent=True).read()

    return Image.open(result)


class VisualizationRequest(BaseModel):
    xmin: float  # EPSG:4326 coordinates
    ymin: float  # EPSG:4326 coordinates
    xmax: float  # EPSG:4326 coordinates
    ymax: float  # EPSG:4326 coordinates

    class Config:
        extra = "forbid"


def visualize_data_to_user(conversation_state: ConversationState):
    async def visualize_to_user(ctx: RunContextWrapper[Any],
                                args: str
                                ) -> str:
        """
        Visualize to user map of a place of interested limited by the box defined by the coordinates
          (xmin, ymin, xmax, ymax) in  EPSG:4326 stabdard.
        """

        parsed = VisualizationRequest.model_validate_json(args)
        try:
            image_osm = _fetch_wms_map(parsed.xmin,
                                    parsed.ymin,
                                    parsed.xmax,
                                    parsed.ymax,
                                    WMS_OSM_URL,
                                    LAYERS_OSM)
        except Exception as e:
            LOGGER.error(f"Error fetching OSM map: {e}")
            return  "Error fetching OSM map"

        try:
            image_geoportal = _fetch_wms_map(parsed.xmin,
                                         parsed.ymin,
                                         parsed.xmax,
                                         parsed.ymax,
                                         WMS_GEOPORTAL_URL,
                                         LAYERS_GEOPORTAL)
        except Exception as e:
            LOGGER.error(f"Error fetching OSM map: {e}")
            return  "Error fetching Geoportal map"

        combined_image = Image.new("RGBA", image_osm.size)
        combined_image.paste(image_osm)

        combined_image.paste(image_geoportal, mask=image_geoportal)  # Using overlay_image as mask for transparency
        conversation_state.image = combined_image
        return "Successfully fetched map data"

    return visualize_to_user


def visualize_spatial_development_plan_to_user(conversation_state: ConversationState):
    async def visualize_to_user(ctx: RunContextWrapper[Any],
                                args: str
                                ) -> str:
        """
        Visualize to user map of a place of interested limited by the box defined by the coordinates
          (xmin, ymin, xmax, ymax) in  EPSG:4326 stabdard.
        """

        parsed = VisualizationRequest.model_validate_json(args)

        try:
            image_osm = _fetch_wms_map(parsed.xmin,
                                   parsed.ymin,
                                   parsed.xmax,
                                   parsed.ymax,
                                   WMS_OSM_URL,
                                   LAYERS_OSM)
        except Exception as e:
            LOGGER.error(f"Error fetching OSM map: {e}")
            return "Error fetching OSM map"

        conversation_state.image = image_osm
        return "Successfully fetched map data"

    return visualize_to_user
