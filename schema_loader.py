# schema_loader.py
import os
import requests
from lxml import etree
from dotenv import load_dotenv
from loguru import logger

from dataverse_client import get_dataverse_token

load_dotenv()

DATAVERSE_URL = os.getenv("DATAVERSE_URL")
CUSTOM_PREFIX = "crca6_"


def get_metadata_xml() -> str:
    """Télécharge le XML complet du $metadata Dataverse."""
    token = get_dataverse_token()

    url = f"{DATAVERSE_URL}/api/data/v9.2/$metadata"
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/xml"
    }

    logger.info("📥 Téléchargement du metadata Dataverse...")
    r = requests.get(url, headers=headers, timeout=60)
    r.raise_for_status()

    return r.text


def extract_entitysets_from_metadata() -> dict:
    """
    Renvoie un dict : logicalname → entitysetname + entityset → entityset.
    Permet d'accepter les deux formes dans le plan LLM.
    """
    xml = get_metadata_xml()
    tree = etree.fromstring(xml.encode("utf-8"))

    ns = {"edm": "http://docs.oasis-open.org/odata/ns/edm"}

    mapping = {}

    for es in tree.findall(".//edm:EntitySet", ns):
        entityset = es.attrib.get("Name")
        entitytype = es.attrib.get("EntityType")

        if not entityset or not entitytype:
            continue

        # exemple: entitytype = "Microsoft.Dynamics.CRM.crca6_opportunity"
        logical = entitytype.split(".")[-1]

        # On ne garde que les tables custom (prefix crca6_)
        if not logical.startswith(CUSTOM_PREFIX):
            continue

        # logical → entityset
        mapping[logical] = entityset

        # entityset → entityset (IMPORTANT)
        mapping[entityset] = entityset

    logger.info("📄 Mapping logical/entityset → entityset construit (%d entrées).", len(mapping))
    return mapping


def load_schema_summary() -> dict:
    """
    Construit un résumé lisible du schéma Dataverse + la liste des EntitySet custom.
    Retour:
      {
        "schema_text": "...",
        "allowed_tables": ["crca6_account1s", "crca6_opportunities", ...]
      }
    """
    xml = get_metadata_xml()
    root = etree.fromstring(xml.encode("utf-8"))

    ns = {"edm": "http://docs.oasis-open.org/odata/ns/edm"}

    summary_lines = []
    allowed_tables = []

    # On prépare un mapping logical → entityset pour les tables custom
    entityset_map = extract_entitysets_from_metadata()

    # Lecture des EntityType
    for entity in root.xpath("//edm:EntityType", namespaces=ns):
        logical_name = entity.attrib.get("Name")

        if not logical_name or not logical_name.startswith(CUSTOM_PREFIX):
            continue

        entityset = entityset_map.get(logical_name)

        # Entête table
        header = f"Table: {logical_name}"
        if entityset:
            header += f" (EntitySet: {entityset})"
            allowed_tables.append(entityset)

        summary_lines.append(header)

        # Colonnes
        for prop in entity.xpath("edm:Property", namespaces=ns):
            pname = prop.attrib.get("Name")
            ptype = prop.attrib.get("Type")
            summary_lines.append(f"  - {pname} ({ptype})")

        summary_lines.append("")  # ligne vide

    schema_text = "\n".join(summary_lines)
    logger.info("📄 Schéma Dataverse résumé généré (tables custom: %d)", len(allowed_tables))

    return {
        "schema_text": schema_text,
        "allowed_tables": sorted(set(allowed_tables)),
    }
