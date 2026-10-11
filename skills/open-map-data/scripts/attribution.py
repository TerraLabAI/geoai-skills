#!/usr/bin/env python3
"""Print the attribution line and license duty for open map data sources.

Matches references/attribution.md. Keep the two in sync.

Example: python3 attribution.py osm overture:places sentinel-2 --year 2026
List keys: python3 attribution.py --list
"""
import argparse
import sys

ODBL = ("ODbL 1.0", "https://opendatacommons.org/licenses/odbl/1-0/",
        "Credit the source and say the data is under ODbL. Share a publicly used derived database "
        "under ODbL. A produced work (rendered map, image) needs the credit; if it comes from a derived "
        "database, also offer that database or a way to rebuild it.")
CCBY = ("CC BY 4.0", "https://creativecommons.org/licenses/by/4.0/",
        "Credit the source, link the license, say if you changed the data.")

SOURCES = {
    "osm": ("© OpenStreetMap contributors",) + ODBL,
    "overture:places": ("© Overture Maps Foundation",
                        "CDLA Permissive 2.0", "https://cdla.dev/permissive-2-0/",
                        "Keep the license text with redistributed data. Results of analysis carry no duty."),
    "ign-bdtopo": ("Source: IGN, BD TOPO, [update date]",
                   "Licence Ouverte 2.0 (Etalab)",
                   "https://www.etalab.gouv.fr/wp-content/uploads/2017/04/ETALAB-Licence-Ouverte-v2.0.pdf",
                   "Credit the source (at least the licensor name) and the date of last update."),
    "os-openmap": ("Contains OS data © Crown copyright and database right [year]",
                   "Open Government Licence v3.0",
                   "https://www.nationalarchives.gov.uk/doc/open-government-license/version/3/",
                   "Include the provider's attribution statement and, where possible, link the license."),
    "google-open-buildings": ("Google Open Buildings",
                              "CC BY 4.0 or ODbL 1.0 (your choice)",
                              "https://sites.research.google/gr/open-buildings/",
                              "Pick one license and follow its duty (CC BY: credit + link; ODbL: see osm)."),
    "microsoft-buildings": ("Microsoft Global ML Building Footprints",
                            "CDLA Permissive 2.0 (repo license; Overture lists it as ODbL)",
                            "https://github.com/microsoft/GlobalMLBuildingFootprints",
                            "Keep the license text with redistributed data; when taken through Overture, "
                            "follow the ODbL duty of that theme."),
    "copernicus-dem": ("© DLR e.V. 2010-2014 and © Airbus Defence and Space GmbH 2014-2018 provided "
                       "under COPERNICUS by the European Union and ESA; all rights reserved",
                       "Copernicus DEM license (GLO-30/GLO-90 free)",
                       "https://dataspace.copernicus.eu/explore-data/data-collections/copernicus-contributing-missions/collections-description/COP-DEM",
                       "Show the notice when distributing; if modified, prefix 'produced using Copernicus "
                       "WorldDEM-30' (or -90). EEA-10 is restricted to eligible users."),
    "sentinel-2": ("Contains modified Copernicus Sentinel data [year]",
                   "Copernicus Sentinel data legal notice (free, full and open)",
                   "https://sentinels.copernicus.eu/documents/247904/690755/Sentinel_Data_Legal_Notice",
                   "Use 'Copernicus Sentinel data [year]' for unmodified data, the 'Contains modified' line otherwise."),
    "landsat": ("Landsat imagery courtesy of the U.S. Geological Survey",
                "Public domain (USGS)",
                "https://www.usgs.gov/information-policies-and-instructions/crediting-usgs",
                "No legal duty; USGS asks for credit."),
    "esa-worldcover": ("© ESA WorldCover project [year] / Contains modified Copernicus Sentinel data "
                       "([year]) processed by ESA WorldCover consortium",) + CCBY[:2] + (
                       "Credit as above (year 2020 or 2021 by map version) and cite the dataset in publications.",),
}
OVERTURE_ODBL = ("buildings", "transportation", "divisions", "base")
for theme in OVERTURE_ODBL:
    SOURCES["overture:" + theme] = ("© OpenStreetMap contributors, Overture Maps Foundation",) + ODBL
SOURCES["overture:addresses"] = ("Overture Maps Foundation, plus each country's credit from "
                                 "docs.overturemaps.org/attribution",
                                 "Mixed per source country", "https://docs.overturemaps.org/attribution/",
                                 "Read the attribution page for every country you use.")


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("sources", nargs="*", help="source keys, e.g. osm overture:places sentinel-2")
    p.add_argument("--year", help="fill [year] in the attribution lines")
    p.add_argument("--list", action="store_true", help="list known source keys")
    a = p.parse_args()
    if a.list or not a.sources:
        print("\n".join(sorted(SOURCES)))
        return 0 if a.list else 2
    unknown = [s for s in a.sources if s.lower() not in SOURCES]
    if unknown:
        print("error: unknown source(s): %s (see --list)" % ", ".join(unknown), file=sys.stderr)
        return 2
    lines = []
    for s in a.sources:
        text, lic, url, duty = SOURCES[s.lower()]
        if a.year:
            text = text.replace("[year]", a.year)
        lines.append(text)
        print("%s\n  attribution: %s\n  license: %s <%s>\n  duty: %s" % (s, text, lic, url, duty))
    print("\nCombined credit line: " + "; ".join(dict.fromkeys(lines)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
