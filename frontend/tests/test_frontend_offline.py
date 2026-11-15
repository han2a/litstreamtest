"""Offline checks (no network, no Streamlit/Plotly):  python3 tests/test_frontend_offline.py"""
import pathlib, sys
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

from api_client import ApiError
from catalog import TABS
from catalog.base import Option, bbox_overlaps, estimate_files, match_variable
import chat_context, workflow

# --- catalog matching ----------------------------------------------------------
listing = [{"variable": "TSKINWTR", "long_name": "open_water_skin_temperature", "units": "K"},
           {"variable": "TSKINICE", "long_name": "sea_ice_skin_temperature", "units": "K"},
           {"variable": "TAUX", "long_name": "eastward_surface_stress", "units": "N m-2"}]
oc = TABS["Oceans"][0]
assert match_variable(oc.option("open_water"), listing)[0]["variable"] == "TSKINWTR"
assert match_variable(oc.option("sea_ice"), listing)[0]["variable"] == "TSKINICE"
m, c = match_variable(Option("x", "x", hints=("skin",)), listing)
assert m is None and len(c) == 2                     # ambiguous -> user chooses
assert match_variable(Option("x", "x", variable="SLP"), [])[0] == {"variable": "SLP"}   # unverifiable
assert match_variable(Option("x", "x", variable="SLP"), listing) == (None, [])           # known absent
air = TABS["Atmosphere"][3]
al = [{"variable": "Temperature_A"}, {"variable": "Temperature_D"}, {"variable": "Temperature_A_Err"}]
assert match_variable(air.option("temp_night"), al)[0]["variable"] == "Temperature_D"
assert match_variable(air.option("temp_day"), al)[0]["variable"] == "Temperature_A"

# --- limits ---------------------------------------------------------------------
precip = [g for g in TABS["Atmosphere"] if g.key == "precip"][0]
assert estimate_files(precip, 36) > 1500 and estimate_files(precip, 2) <= 1500
conus = (25.0, 53.0, -125.0, -67.0)
assert bbox_overlaps({"lat_min": 30, "lat_max": 40, "lon_min": 235, "lon_max": 290}, conus)   # 0-360 box
assert not bbox_overlaps({"lat_min": 4, "lat_max": 22, "lon_min": 116, "lon_max": 128}, conus)

# --- workflow with fake backend ------------------------------------------------------
def fake_listing(short):
    return {"needs_variable": True,
            "collection": {"collection": "C1-GES_DISC", "short_name": short, "version": "5.12.4"},
            "variables": listing if short == "M2TMNXOCN" else []}
added = []
def fake_add(body):
    added.append(body)
    return {"id": "x", "label": body["label"], "collection": body["collection"]}

prep = workflow.prepare(TABS["Oceans"], {"skin_temp": {"options": ["open_water", "sea_ice"]}},
                        fake_listing, fake_add)
assert not prep.errors and len(prep.products) == 2
assert added[0]["variable"] == "TSKINWTR" and "level" not in added[0]

# geopotential height needs no listing (exact names), no level
added.clear()
prep = workflow.prepare(TABS["Atmosphere"], {"geopotential": {"options": ["h500", "h250"]}},
                        fake_listing, fake_add)
assert [b["variable"] for b in added] == ["H500", "H250"] and len(prep.warnings) == 1

# wind needs the variable list: without a token it must say so, not guess
prep = workflow.prepare(TABS["Atmosphere"], {"wind10m": {"options": ["wind_speed"]}}, fake_listing, fake_add)
assert prep.errors and not prep.products

# derived wind speed once the list exists
wind_listing = [{"variable": "UGRD10m", "long_name": "10-meter above ground Zonal wind speed"},
                {"variable": "VGRD10m", "long_name": "10-meter above ground Meridional wind speed"}]
def listing_w(short):
    r = fake_listing(short); r["variables"] = wind_listing; return r
added.clear()
prep = workflow.prepare(TABS["Atmosphere"], {"wind10m": {"options": ["wind_speed"]}}, listing_w, fake_add)
assert added[0]["variables"] == ["UGRD10m", "VGRD10m"] and added[0]["derive"] == "magnitude", added

# AIRS: a listing with no vertical dimension is reported, levels expand to products
def listing_air(short):
    r = fake_listing(short)
    r["variables"] = [{"variable": "Temperature_A", "has_levels": True},
                      {"variable": "Temperature_D", "has_levels": True}]
    return r
added.clear()
prep = workflow.prepare(TABS["Atmosphere"], {"air_temperature": {
    "options": ["temp_day", "temp_night"], "levels": [500, 850]}}, listing_air, fake_add)
assert len(added) == 4 and {b["level"] for b in added} == {500, 850}
def listing_air_flat(short):
    r = listing_air(short)
    r["variables"] = [{"variable": "Temperature_A", "has_levels": False}]
    return r
prep = workflow.prepare(TABS["Atmosphere"], {"air_temperature": {"options": ["temp_day"], "levels": [500]}},
                        listing_air_flat, fake_add)
assert prep.errors and "vertical dimension" in prep.errors[0]

# backend error on one product is reported, others continue
def flaky_add(body):
    if body["variable"] == "H250":
        raise ApiError("boom")
    return fake_add(body)
prep = workflow.prepare(TABS["Atmosphere"], {"geopotential": {"options": ["h500", "h250"]}},
                        fake_listing, flaky_add)
assert len(prep.products) == 1 and "boom" in prep.errors[0]

# --- batching ----------------------------------------------------------------------------
class FakeClient:
    def __init__(self): self.calls = []
    def analyze(self, payload):
        self.calls.append(len(payload["products"]))
        if len(self.calls) == 2:
            raise ApiError("second batch failed")
        return {"products": [{"product": d["label"]} for d in payload["products"]],
                "cross_product_correlation": []}
prods = [{"descriptor": {"label": f"p{i}"}} for i in range(7)]
fc = FakeClient()
merged, errs = workflow.run_analysis(fc, prods, {}, "2017-01", "2019-12", 0.05, max_products=3)
assert fc.calls == [3, 3, 1] and len(merged["products"]) == 4 and len(errs) == 1

# --- chat context ------------------------------------------------------------------------
product = {"product": "p", "title": "SLP", "units": "Pa", "n_months": 36, "resampled_to_monthly": True,
           "descriptor": {"collection": "C1-GES_DISC", "variables": ["SLP"], "derive": None, "level": None},
           "area_mean": {"time": ["2017-01", "2017-02", "2017-03"], "value": [1.0, None, 3.0], "anomaly": [0, 0, 0]},
           "statistics": {"mean": {"mean": 2.0, "ci": [1.0, 3.0], "std": 1.0},
                          "trend_ols": {"slope_per_decade": 0.5, "ci_per_decade": [0.1, 0.9], "p_value": 0.03, "significant": True},
                          "trend_mann_kendall": {"sens_slope_per_decade": 0.4, "p_value": 0.04, "significant": True}},
           "trend_map": {"fraction_significant_fdr": 0.2}}
analysis = {"results": {"request": {"start": "2017-01"}, "products": [product], "cross_product_correlation": []},
            "errors": []}
ctx = chat_context.build_context("Atmosphere", [{"dataset": "M2T1NXSLV"}], {"start": "2017-01"}, analysis, True)
assert ctx["analysis_stale"] and ctx["latest_analysis"]["products"][0]["series"]["min"]["value"] == 1.0
assert ctx["latest_analysis"]["products"][0]["ols_trend_per_decade"]["slope"] == 0.5
assert not chat_context.build_context("Oceans", [], {}, None, False)["analysis_available"]
lit = chat_context.literature_context(
    analysis["results"] | {"request": {}}, {"bbox": {"lat_min": 0, "lat_max": 1, "lon_min": 2, "lon_max": 3},
                                            "start": "2017-01", "end": "2019-12"})
assert lit["findings"][0]["mean"] == 2.0

print("all frontend offline checks passed")
