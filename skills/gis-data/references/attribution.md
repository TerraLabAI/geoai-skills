# Attribution blocks

Verified on 2026-10-11.

Copy the attribution line onto the map, the dataset README or the app's credits. `scripts/attribution.py` prints the same lines; keep the two in sync. Replace `[year]` and `[update date]`.

## OpenStreetMap

- Attribution: `© OpenStreetMap contributors`
- License: Open Database License 1.0 (ODbL), https://opendatacommons.org/licenses/odbl/1-0/
- Duty: credit OpenStreetMap and make clear the data is under ODbL (link https://www.openstreetmap.org/copyright). A derived database used publicly must be shared under ODbL. A produced work (rendered map, image) needs the credit; if it was made from a derived database, also offer that database, or a file of the changes, or a way to rebuild it.
- Source: https://www.openstreetmap.org/copyright

## Overture Maps

- Citation for publications: `Overture Maps Foundation, overturemaps.org` (with the access date).
- Buildings, transportation, divisions, base: ODbL (they contain OSM). Attribution: `© OpenStreetMap contributors, Overture Maps Foundation`. Duty: as OpenStreetMap. Each theme also lists extra sources (Esri Community Maps CC BY 4.0, geoBoundaries CC BY 4.0, TomTom, Microsoft buildings, ESA WorldCover in base): copy those credits when you use the theme.
- Places: CDLA Permissive 2.0, https://cdla.dev/permissive-2-0/. Attribution: `© Overture Maps Foundation`. Duty: keep the license text with redistributed data; results of analysis carry no duty.
- Addresses: mixed licenses per country (Etalab 2.0 in France, DL-DE BY 2.0 in Germany, PDDL and CC BY in US counties, and others). Copy the credit of every country you use.
- Source: https://docs.overturemaps.org/attribution/

## IGN (France)

- Attribution: `Source: IGN, BD TOPO, [update date]`
- License: Licence Ouverte 2.0 (Etalab), https://www.etalab.gouv.fr/wp-content/uploads/2017/04/ETALAB-License-Ouverte-v2.0.pdf
- Duty: credit the source (at least the licensor name) and the date of the last update of the data. No share-alike. Compatible with OGL, CC BY and ODC-BY.

## Ordnance Survey OS OpenData (Great Britain)

- Attribution: `Contains OS data © Crown copyright and database right [year]`
- License: Open Government Licence v3.0, https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/
- Duty: include the provider's attribution statement and, where possible, link the license. Without a provider statement the OGL default is `Contains public sector information licensed under the Open Government Licence v3.0.` No share-alike.

## Google Open Buildings

- Attribution: `Google Open Buildings`
- License: your choice of CC BY 4.0 (https://creativecommons.org/licenses/by/4.0/) or ODbL 1.0 (https://opendatacommons.org/licenses/odbl/1-0/)
- Duty: follow the license you picked. CC BY: credit, link the license, say if changed. ODbL: as OpenStreetMap.
- Source: https://sites.research.google/gr/open-buildings/

## Microsoft Global ML Building Footprints

- Attribution: `Microsoft Global ML Building Footprints`
- License: the repository now states CDLA Permissive 2.0 (https://cdla.dev/permissive-2-0/). Overture's attribution page still lists it under ODbL inside its buildings theme.
- Duty: downloaded from Microsoft, keep the CDLA text with redistributed data. Taken through Overture buildings, follow the ODbL duty of that theme.
- Source: https://github.com/microsoft/GlobalMLBuildingFootprints

## Copernicus DEM

- Attribution (GLO-30, distributing or showing to the public): `© DLR e.V. 2010-2014 and © Airbus Defence and Space GmbH 2014-2018 provided under COPERNICUS by the European Union and ESA; all rights reserved`
- When modified: `produced using Copernicus WorldDEM-30 © DLR e.V. 2010-2014 and © Airbus Defence and Space GmbH 2014-2018 provided under COPERNICUS by the European Union and ESA; all rights reserved` (WorldDEM-90 for GLO-90).
- License: Copernicus DEM license; GLO-30 and GLO-90 are free worldwide, EEA-10 is restricted to eligible users.
- Duty: show the notice above. Cite the dataset DOI in research.
- Source: https://dataspace.copernicus.eu/explore-data/data-collections/copernicus-contributing-missions/collections-description/COP-DEM

## Copernicus Sentinel data (Sentinel-1, Sentinel-2)

- Attribution: `Contains modified Copernicus Sentinel data [year]` when you processed or changed the data; `Copernicus Sentinel data [year]` when unmodified.
- License: free, full and open access under EU law (Regulation 1159/2013), https://sentinels.copernicus.eu/documents/247904/690755/Sentinel_Data_Legal_Notice
- Duty: give the notice. No share-alike.

## Landsat (USGS)

- Attribution: `Landsat imagery courtesy of the U.S. Geological Survey`
- License: public domain.
- Duty: none by law; USGS asks for credit, for example `Source of (data name): U.S. Geological Survey`.
- Source: https://www.usgs.gov/information-policies-and-instructions/crediting-usgs

## ESA WorldCover

- Attribution on a map: `© ESA WorldCover project [year] / Contains modified Copernicus Sentinel data ([year]) processed by ESA WorldCover consortium` (year 2020 or 2021 by map version).
- License: CC BY 4.0, https://creativecommons.org/licenses/by/4.0/
- Duty: credit as above, and cite the dataset in publications, models and data products.
- Source: https://esa-worldcover.org/en/data-access
