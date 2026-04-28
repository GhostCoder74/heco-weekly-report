#!/usr/bin/env python3
# geaCal – XML Generator Module (robust version)

import os
import datetime
import xml.etree.ElementTree as ET
from geaCal_holidays_mod import list_holidays_for_year


def ensure_dir(path: str):
    if not os.path.exists(path):
        os.makedirs(path, exist_ok=True)


def normalize_holiday(h):
    """
    Normalize holiday objects into a dict with:
      date, name, region, movable
    Supports dicts, tuples, objects.
    """

    if isinstance(h, dict):
        # Try common dictionary keys
        return {
            "date": h.get("date") or h.get("datum") or h.get("d") or "",
            "name": h.get("name") or h.get("title") or h.get("n") or "",
            "region": h.get("region") or h.get("r") or "",
            "movable": bool(h.get("movable") or h.get("ist_beweglich") or False)
        }

    # Tuple format fallback
    if isinstance(h, (list, tuple)):
        # Most common form: (date, name, region, movable)
        if len(h) >= 4:
            return {
                "date": h[0],
                "name": h[1],
                "region": h[2],
                "movable": bool(h[3])
            }

        # Unknown tuple formats
        return {
            "date": h[0] if len(h) > 0 else "",
            "name": h[1] if len(h) > 1 else "",
            "region": "",
            "movable": False
        }

    # Object-based format
    if hasattr(h, "__dict__"):
        d = h.__dict__
        return {
            "date": d.get("date", ""),
            "name": d.get("name", ""),
            "region": d.get("region", ""),
            "movable": bool(d.get("movable", False))
        }

    # Final fallback – avoid crash
    return {
        "date": str(h),
        "name": "",
        "region": "",
        "movable": False
    }


def generate_xml_for_year(base_dir: str, year: int):
    year_dir = os.path.join(base_dir, str(year))
    ensure_dir(year_dir)

    xml_file = os.path.join(year_dir, "holidays.xml")

    # do not overwrite
    if os.path.isfile(xml_file):
        return xml_file

    holidays = list_holidays_for_year(year)

    root = ET.Element("holidays", attrib={"year": str(year)})

    for h in holidays:
        hdata = normalize_holiday(h)
        date_str = datetime.datetime.strptime(hdata["date"], "%Y-%m-%d").strftime("%d.%m.%Y")
        print("date_str = ", date_str)
        node = ET.SubElement(root, "holiday")
        ET.SubElement(node, "Feiertage").text = hdata["name"]
        ET.SubElement(node, "Datum").text = str(date_str)
        #ET.SubElement(node, "region").text = hdata["region"]
        #ET.SubElement(node, "movable").text = "true" if hdata["movable"] else "false"

    tree = ET.ElementTree(root)
    tree.write(xml_file, encoding="utf-8", xml_declaration=True)

    return xml_file


def generate_all(base_dir: str):
    now = datetime.date.today()
    years = [now.year, now.year + 1]

    results = []
    for y in years:
        results.append((y, generate_xml_for_year(base_dir, y)))
    return results
