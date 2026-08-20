import unittest
from unittest.mock import patch

from expedition.adapters import discover as osm
from expedition.discovery.harness import run_discovery
from expedition.discovery.echo import search_echo
from expedition.discovery.eia import search_eia_plants
from expedition.discovery.google_witness import attach_google_witnesses
from expedition.discovery.places import search_places
from expedition.discovery.prefilter import PREFILTER_FIELDS, prefilter_seeds
from expedition.discovery.rentcast import search_rentcast
from expedition.discovery.router import plan_sources
from expedition.discovery.schema import Seed
from expedition.discovery.uspvdb import search_uspvdb
from expedition.discovery.uswtdb import search_uswtdb


OSM_SITES = {
    "mission": "warehouse",
    "search_region": "houston_metro",
    "look": {"lat": 29.76, "lng": -95.37, "name": "Houston", "query": "Houston"},
    "candidates": [
        {
            "id": "osm_way_1",
            "name": "Ship Channel warehouse",
            "lat": 29.73,
            "lng": -95.21,
            "address": None,
            "label": "POTENTIAL",
            "site_form": "either",
            "source": "openstreetmap",
            "source_url": "https://www.openstreetmap.org/copyright",
            "authorization": "https://www.openstreetmap.org/copyright",
            "family": "map_feature",
            "role": "candidate",
            "captured_at": "2026-08-19T00:00:00Z",
        }
    ],
    "note": "OpenStreetMap map features. Not listings. Not for sale here.",
}

PV_ROWS = [
    {
        "case_id": 403279,
        "p_name": "Liberty County Solar Project",
        "ylat": 30.05,
        "xlong": -94.78,
        "p_cap_ac": 200,
        "p_state": "TX",
        "p_type": "greenfield",
        "eia_id": 1,
    }
]


class RouterTests(unittest.TestCase):
    def test_warehouse_standard_hops_power_not_listings(self):
        plan = plan_sources("warehouse", "standard", allow_paid=True, places_key=False)
        self.assertIn("osm", plan.seeds)
        self.assertIn("osm_power", plan.hops)
        self.assertIn("eia", plan.hops)
        self.assertIn("echo", plan.seeds)
        self.assertNotIn("rentcast", plan.seeds)
        self.assertFalse(any(s.source == "places" and s.verdict == "BUILD_NOW" for s in plan.skipped))
        skipped = {s.source: s for s in plan.skipped}
        self.assertEqual(skipped["places"].verdict, "NO_KEY")
        self.assertEqual(skipped["mireye_region_search"].verdict, "WITNESS_ONLY")
        self.assertEqual(skipped["google_tiles_extract"].verdict, "BLOCKED")
        self.assertEqual(skipped["ask_google_earth"].verdict, "BLOCKED")
        paid = plan_sources("warehouse", "standard", allow_paid=True, places_key=True)
        self.assertIn("places", paid.seeds)

    def test_home_can_list_only_with_rentcast_key(self):
        closed = plan_sources("home", "standard", allow_paid=True, rentcast_key=False)
        self.assertNotIn("rentcast", closed.seeds)
        opened = plan_sources("home", "standard", allow_paid=True, rentcast_key=True)
        self.assertIn("rentcast", opened.seeds)

    def test_data_center_standard_uses_uspvdb(self):
        plan = plan_sources("data_center", "standard")
        self.assertIn("uspvdb", plan.hops)
        self.assertIn("osm_power", plan.hops)
        self.assertIn("eia", plan.hops)
        self.assertIn("uswtdb", plan.hops)

    def test_quick_skips_hops(self):
        plan = plan_sources("data_center", "quick")
        self.assertEqual(plan.hops, ())


class AdapterTests(unittest.TestCase):
    def test_places_never_listed(self):
        payload = {
            "places": [
                {
                    "id": "ChIJabc",
                    "displayName": {"text": "Houston Logistics"},
                    "location": {"latitude": 29.76, "longitude": -95.37},
                    "formattedAddress": "Houston, TX",
                    "googleMapsUri": "https://maps.google.com/?cid=1",
                    "primaryType": "storage",
                }
            ]
        }
        with patch("expedition.discovery.places.places_key", return_value="test-key"):
            seeds, err = search_places(
                "warehouse", 29.76, -95.37, http_json=lambda url, body, key: payload
            )
        self.assertIsNone(err)
        self.assertEqual(seeds[0].label, "POTENTIAL")
        self.assertEqual(seeds[0].family, "place")
        self.assertEqual(seeds[0].extra["place_id"], "ChIJabc")

    def test_places_drops_agencies_and_captive_retail_dcs(self):
        payload = {
            "places": [
                {
                    "id": "keep1",
                    "displayName": {"text": "Friendly Public Warehouse"},
                    "location": {"latitude": 29.76, "longitude": -95.37},
                    "primaryType": "storage",
                },
                {
                    "id": "drop-agency",
                    "displayName": {"text": "Houston Warehouse Space"},
                    "location": {"latitude": 29.75, "longitude": -95.36},
                    "primaryType": "real_estate_agency",
                },
                {
                    "id": "drop-amazon",
                    "displayName": {"text": "Amazon Distribution Center"},
                    "location": {"latitude": 30.54, "longitude": -97.69},
                    "primaryType": "storage",
                },
            ]
        }
        with patch("expedition.discovery.places.places_key", return_value="test-key"):
            seeds, err = search_places(
                "warehouse", 29.76, -95.37, http_json=lambda url, body, key: payload
            )
        self.assertIsNone(err)
        self.assertEqual([s.name for s in seeds], ["Friendly Public Warehouse"])

    def test_uspvdb_is_anchor(self):
        seeds, err = search_uspvdb(29.76, -95.37, http_json=lambda url: PV_ROWS)
        self.assertIsNone(err)
        self.assertEqual(seeds[0].role, "anchor")
        self.assertEqual(seeds[0].label, "POTENTIAL")
        self.assertNotEqual(seeds[0].label, "LISTED")
        self.assertIn("Operating", seeds[0].extra["note"])

    def test_echo_keeps_public_warehouse_drops_amazon(self):
        rows = [
            {
                "FacName": "DUPUY STORAGE HOUSTON 7703 CANNON",
                "FacLat": "29.68014",
                "FacLong": "-95.37677",
                "FacStreet": "7703 CANNON ST",
                "FacCity": "HOUSTON",
                "FacState": "TX",
                "RegistryID": "110012345",
                "FacNAICSCodes": "493110",
            },
            {
                "FacName": "AMAZONCOM SERVICES DHO5",
                "FacLat": "29.778192",
                "FacLong": "-95.315951",
                "RegistryID": "110070628300",
                "FacNAICSCodes": "493110",
            },
        ]
        seeds, err = search_echo([(29.76, -95.37, 16000)], http_json=lambda lat, lng, miles: rows)
        self.assertIsNone(err)
        self.assertEqual(len(seeds), 1)
        self.assertEqual(seeds[0].label, "POTENTIAL")
        self.assertEqual(seeds[0].source, "epa_echo")
        self.assertNotEqual(seeds[0].label, "LISTED")

    def test_eia_and_uswtdb_are_anchors(self):
        eia_payload = {
            "features": [
                {
                    "attributes": {
                        "Plant_Code": 3452,
                        "Plant_Name": "W A Parish",
                        "City": "Thompsons",
                        "State": "Texas",
                        "PrimSource": "coal",
                        "Total_MW": 3632,
                        "Latitude": 29.4828,
                        "Longitude": -95.6311,
                        "Street_Add": None,
                    }
                }
            ]
        }
        eia, err = search_eia_plants(29.76, -95.37, http_json=lambda url: eia_payload)
        self.assertIsNone(err)
        self.assertEqual(eia[0].role, "anchor")
        self.assertEqual(eia[0].source, "eia_plants")
        wind, werr = search_uswtdb(
            29.4,
            -96.0,
            http_json=lambda url: [
                {
                    "p_name": "Lane City Wind",
                    "t_county": "Wharton County",
                    "ylat": 29.2,
                    "xlong": -96.0,
                    "p_cap": 202.5,
                    "t_state": "TX",
                }
            ],
        )
        self.assertIsNone(werr)
        self.assertEqual(wind[0].role, "anchor")
        self.assertEqual(wind[0].source, "uswtdb")

    def test_google_solar_witness_is_not_a_candidate(self):
        seed = Seed(
            id="osm_1",
            name="Box",
            lat=29.73,
            lng=-95.33,
            source="openstreetmap",
            source_url="https://www.openstreetmap.org/copyright",
            authorization="https://www.openstreetmap.org/copyright",
            family="map_feature",
            address="2103 Ernestine St, Houston, TX",
        )
        solar = {
            "postalCode": "77023",
            "solarPotential": {"maxArrayPanelsCount": 12, "maxArrayAreaMeters2": 40.0, "maxSunshineHoursPerYear": 1600},
        }
        with patch("expedition.discovery.google_witness._get", return_value=solar), patch(
            "expedition.discovery.google_witness.aerial_metadata",
            return_value={"videoId": "abc", "state": "ACTIVE"},
        ):
            out, traces = attach_google_witnesses(
                [seed],
                key="test",
                streetview_n=1,
                solar_n=1,
                aerial_n=1,
                reverse_n=0,
                elevation_n=0,
            )
        self.assertEqual(out[0].role, "candidate")
        self.assertEqual(out[0].label, "POTENTIAL")
        self.assertEqual(out[0].extra["solar"]["max_panels"], 12)
        self.assertEqual(out[0].extra["aerial"]["video_id"], "abc")
        self.assertTrue(any(t["source"] == "google_solar" and t["ok"] for t in traces))

    def test_google_reverse_geocode_and_elevation_stay_potential(self):
        seed = Seed(
            id="osm_anon",
            name="Warehouse OSM 1",
            lat=29.69612,
            lng=-95.25493,
            source="openstreetmap",
            source_url="https://www.openstreetmap.org/copyright",
            authorization="https://www.openstreetmap.org/copyright",
            family="map_feature",
        )
        geo = {
            "status": "OK",
            "results": [
                {
                    "formatted_address": "1200 Lathrop St, Houston, TX 77020, USA",
                    "types": ["street_address"],
                }
            ],
        }
        elev = {
            "status": "OK",
            "results": [{"elevation": 8.27, "resolution": 4.77}],
        }

        def fake_get(url, headers=None):
            if "geocode" in url:
                return geo
            if "elevation" in url:
                return elev
            return {"status": "OK"}

        with patch("expedition.discovery.google_witness._get", side_effect=fake_get):
            out, traces = attach_google_witnesses(
                [seed],
                key="test",
                streetview_n=0,
                solar_n=0,
                aerial_n=0,
                reverse_n=1,
                elevation_n=1,
                routes_n=0,
            )
        self.assertEqual(out[0].address, "1200 Lathrop St, Houston, TX 77020, USA")
        self.assertEqual(out[0].label, "POTENTIAL")
        self.assertAlmostEqual(out[0].extra["elevation"]["meters"], 8.27)
        self.assertTrue(any(t["source"] == "geocode_reverse" and t["count"] == 1 for t in traces))

    def test_rentcast_listed_requires_id_and_last_seen(self):
        rows = [
            {
                "id": "1-Main-St",
                "formattedAddress": "1 Main St, Austin, TX 78701",
                "latitude": 30.27,
                "longitude": -97.74,
                "lastSeenDate": "2026-08-19T00:00:00.000Z",
                "status": "Active",
                "price": 400000,
                "propertyType": "Single Family",
            },
            {
                "id": "missing-seen",
                "latitude": 30.28,
                "longitude": -97.75,
            },
        ]
        with patch("expedition.discovery.rentcast.rentcast_key", return_value="k"):
            seeds, err = search_rentcast(
                30.27, -97.74, http_json=lambda url, key: rows
            )
        self.assertIsNone(err)
        self.assertEqual(len(seeds), 1)
        self.assertEqual(seeds[0].label, "LISTED")
        self.assertEqual(seeds[0].extra["listing_id"], "1-Main-St")

    def test_prefilter_quotes_then_attaches(self):
        seed = Seed(
            id="osm_way_1",
            name="A",
            lat=29.73,
            lng=-95.21,
            source="openstreetmap",
            source_url="https://www.openstreetmap.org/copyright",
            authorization="https://www.openstreetmap.org/copyright",
            family="map_feature",
            captured_at="2026-08-19T00:00:00Z",
        )
        authorized = []

        def authorize(credits, *, reason, expedition_spent=0):
            authorized.append((credits, reason))

        batch = {
            "results": [
                {
                    "index": 0,
                    "ok": True,
                    "fields": {
                        "within_floodplain_polygon": {"value": False, "source": "FEMA", "status": "ok"},
                        "intersects_wetland": {"value": False, "source": "NWI", "status": "ok"},
                        "slope_degrees": {"value": 1.2, "source": "USGS", "status": "ok"},
                    },
                }
            ]
        }
        out, spent, err = prefilter_seeds(
            [seed],
            live=True,
            quote=lambda fields, n: len(fields) * n,
            authorize=authorize,
            fetch_batch=lambda payload: batch,
        )
        self.assertIsNone(err)
        self.assertEqual(spent, 3)
        self.assertEqual(authorized[0][0], 3)
        self.assertEqual(out[0].extra["prefilter"]["within_floodplain_polygon"]["value"], False)
        self.assertEqual(PREFILTER_FIELDS[0], "within_floodplain_polygon")


class HarnessTests(unittest.TestCase):
    def test_standard_dc_merges_osm_and_uspvdb_without_inventing_listings(self):
        with patch("expedition.discovery.harness.osm.discover_sites", return_value=OSM_SITES), patch(
            "expedition.discovery.harness.search_uspvdb",
            return_value=([
                Seed(
                    id="uspvdb_403279",
                    name="Liberty County Solar Project",
                    lat=30.05,
                    lng=-94.78,
                    source="uspvdb",
                    source_url="https://energy.usgs.gov/uspvdb/data/",
                    authorization="https://energy.usgs.gov/uspvdb/data/",
                    family="infra_anchor",
                    role="anchor",
                    captured_at="2026-08-19T00:00:00Z",
                    extra={"note": "Operating USGS USPVDB solar facility. Not a listing."},
                )
            ], None),
        ), patch(
            "expedition.discovery.harness.search_eia_plants",
            return_value=([], None),
        ), patch(
            "expedition.discovery.harness.search_uswtdb",
            return_value=([], None),
        ), patch(
            "expedition.discovery.harness._power_hop",
            return_value=([], None),
        ), patch(
            "expedition.discovery.harness.search_around",
            return_value=[],
        ):
            packet = run_discovery(
                "data_center",
                search_region="houston_metro",
                look_query="Houston",
                scan_budget="standard",
                network=True,
                allow_paid=False,
            )
        labels = {row["label"] for row in packet["candidates"] + packet["anchors"]}
        self.assertNotIn("LISTED", labels)
        self.assertEqual(packet["source"], "discovery_harness")
        self.assertTrue(any(row["id"] == "uspvdb_403279" for row in packet["anchors"]))
        self.assertTrue(any(row["id"] == "osm_way_1" for row in packet["candidates"]))
        self.assertIn("uspvdb", packet["plan"]["hops"])

    def test_osm_failure_still_returns_uspvdb(self):
        with patch(
            "expedition.discovery.harness.osm.discover_sites",
            side_effect=osm.DiscoverError("OpenStreetMap search failed (HTTPError)"),
        ), patch(
            "expedition.discovery.harness.osm.geocode_look",
            return_value={"lat": 29.76, "lng": -95.37, "name": "Houston", "query": "Houston"},
        ), patch(
            "expedition.discovery.harness.search_uspvdb",
            return_value=(
                [
                    Seed(
                        id="uspvdb_403279",
                        name="Liberty County Solar Project",
                        lat=30.05,
                        lng=-94.78,
                        source="uspvdb",
                        source_url="https://energy.usgs.gov/uspvdb/data/",
                        authorization="https://energy.usgs.gov/uspvdb/data/",
                        family="infra_anchor",
                        role="anchor",
                        captured_at="2026-08-19T00:00:00Z",
                    )
                ],
                None,
            ),
        ), patch(
            "expedition.discovery.harness.search_eia_plants",
            return_value=([], None),
        ), patch(
            "expedition.discovery.harness.search_uswtdb",
            return_value=([], None),
        ), patch(
            "expedition.discovery.harness._power_hop",
            return_value=([], None),
        ), patch(
            "expedition.discovery.harness.search_around",
            return_value=[],
        ):
            packet = run_discovery(
                "data_center",
                search_region="houston_metro",
                look_query="Houston",
                scan_budget="standard",
                network=True,
            )
        self.assertTrue(any(row["id"] == "uspvdb_403279" for row in packet["anchors"]))
        self.assertFalse(next(t for t in packet["traces"] if t["source"] == "osm")["ok"])

    def test_quick_does_not_call_uspvdb(self):
        with patch("expedition.discovery.harness.osm.discover_sites", return_value=OSM_SITES), patch(
            "expedition.discovery.harness.search_uspvdb"
        ) as uspvdb:
            packet = run_discovery(
                "data_center",
                search_region="houston_metro",
                scan_budget="quick",
                network=True,
            )
        uspvdb.assert_not_called()
        self.assertEqual(packet["plan"]["hops"], [])
