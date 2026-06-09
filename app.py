import io
import math
from datetime import date, datetime, time, timedelta

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st


REQUIRED_SHEETS = [
    "Warehouse_Inputs",
    "Truck_Inputs",
    "Delivery_Return_Inputs",
]

REQUIRED_COLUMNS = {
    "Warehouse_Inputs": [
        "scenario_id",
        "warehouse_id",
        "warehouse_name",
        "planning_start_date",
        "planning_days",
        "warehouse_latitude",
        "warehouse_longitude",
        "daily_dispatch_start_time",
        "default_driver_shift_hours",
        "default_service_time_delivery_min",
        "default_service_time_return_min",
        "default_cost_per_mile",
        "default_driver_cost_per_hour",
        "default_co2_kg_per_mile",
        "manual_baseline_total_miles",
        "manual_baseline_total_cost",
        "manual_baseline_notes",
    ],
    "Truck_Inputs": [
        "scenario_id",
        "planning_day",
        "truck_id",
        "truck_status",
        "maintenance_reason",
        "vehicle_type",
        "max_weight_lbs",
        "max_volume_cuft",
        "start_time",
        "shift_limit_hours",
        "cost_per_mile",
        "driver_cost_per_hour",
        "co2_kg_per_mile",
        "notes",
    ],
    "Delivery_Return_Inputs": [
        "scenario_id",
        "planning_day",
        "stop_id",
        "stop_type",
        "customer_id",
        "customer_name",
        "latitude",
        "longitude",
        "quantity_units",
        "weight_lbs",
        "volume_cuft",
        "ready_time",
        "due_time",
        "service_minutes",
        "priority_level",
        "days_waiting",
        "return_value_usd",
        "customer_requirement",
        "preferred_truck_id",
        "notes",
    ],
}

NAVY = "#102A43"
GREEN = "#1F9D55"
ORANGE = "#F08C00"
RED = "#D64545"
LIGHT_BG = "#F7F9FC"


def haversine_distance(lat1, lon1, lat2, lon2):
    radius_miles = 3958.8
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    )
    c = 2 * math.asin(math.sqrt(a))
    return radius_miles * c


def ensure_time(value, fallback="08:00"):
    if pd.isna(value):
        value = fallback
    if isinstance(value, time):
        return value
    if isinstance(value, datetime):
        return value.time()
    if isinstance(value, pd.Timestamp):
        return value.to_pydatetime().time()
    if isinstance(value, (int, float)) and 0 <= float(value) < 1:
        total_seconds = int(float(value) * 24 * 3600)
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        return time(hours, minutes)
    return pd.to_datetime(str(value)).time()


def normalize_numeric(series):
    return pd.to_numeric(series, errors="coerce")


def create_sample_data():
    warehouse = pd.DataFrame(
        [
            {
                "scenario_id": "SAMPLE_A",
                "warehouse_id": "WH1",
                "warehouse_name": "Central Distribution Hub",
                "planning_start_date": date(2026, 6, 8),
                "planning_days": 3,
                "warehouse_latitude": 41.8781,
                "warehouse_longitude": -87.6298,
                "daily_dispatch_start_time": "07:00",
                "default_driver_shift_hours": 10,
                "default_service_time_delivery_min": 20,
                "default_service_time_return_min": 15,
                "default_cost_per_mile": 2.15,
                "default_driver_cost_per_hour": 31.0,
                "default_co2_kg_per_mile": 1.65,
                "manual_baseline_total_miles": 670,
                "manual_baseline_total_cost": 2635,
                "manual_baseline_notes": "Manual baseline assumes several empty return legs.",
            }
        ]
    )

    trucks = []
    truck_templates = [
        ("T001", "Available", "", "Box Truck", 8500, 1400),
        ("T002", "Available", "", "Box Truck", 9000, 1500),
        ("T003", "Available", "", "Straight Truck", 12000, 1800),
        ("T004", "Maintenance", "Brake inspection", "Box Truck", 8000, 1300),
        ("T005", "Available", "", "Sprinter", 4500, 700),
    ]
    for day in [1, 2, 3]:
        for truck_id, status, reason, vehicle_type, max_weight, max_volume in truck_templates:
            trucks.append(
                {
                    "scenario_id": "SAMPLE_A",
                    "planning_day": day,
                    "truck_id": truck_id,
                    "truck_status": status,
                    "maintenance_reason": reason,
                    "vehicle_type": vehicle_type,
                    "max_weight_lbs": max_weight,
                    "max_volume_cuft": max_volume,
                    "start_time": "07:00" if truck_id != "T005" else "07:30",
                    "shift_limit_hours": 10 if truck_id != "T005" else 8,
                    "cost_per_mile": 2.1 if truck_id != "T003" else 2.45,
                    "driver_cost_per_hour": 30 if truck_id != "T003" else 34,
                    "co2_kg_per_mile": 1.5 if truck_id == "T005" else 1.75,
                    "notes": "",
                }
            )
    trucks = pd.DataFrame(trucks)

    rng = np.random.default_rng(7)
    day_centers = {
        1: (41.92, -87.76),
        2: (41.79, -87.68),
        3: (41.86, -87.54),
    }
    deliveries_returns = []
    delivery_counter = 1
    return_counter = 1
    priorities = ["High", "Medium", "Low"]

    for day in [1, 2, 3]:
        center_lat, center_lon = day_centers[day]
        delivery_count = 5 if day != 2 else 6
        return_count = 3 if day != 3 else 4

        for idx in range(delivery_count):
            lat = center_lat + rng.uniform(-0.09, 0.09)
            lon = center_lon + rng.uniform(-0.09, 0.09)
            ready_hour = 8 + (idx % 3)
            due_hour = 11 + idx
            deliveries_returns.append(
                {
                    "scenario_id": "SAMPLE_A",
                    "planning_day": day,
                    "stop_id": f"D{delivery_counter:03d}",
                    "stop_type": "Delivery",
                    "customer_id": f"C{delivery_counter:03d}",
                    "customer_name": f"Delivery Customer {delivery_counter}",
                    "latitude": round(lat, 6),
                    "longitude": round(lon, 6),
                    "quantity_units": int(rng.integers(8, 22)),
                    "weight_lbs": int(rng.integers(500, 2400)),
                    "volume_cuft": int(rng.integers(70, 260)),
                    "ready_time": f"{ready_hour:02d}:00",
                    "due_time": f"{due_hour:02d}:30",
                    "service_minutes": int(rng.integers(15, 31)),
                    "priority_level": priorities[idx % 3],
                    "days_waiting": 0,
                    "return_value_usd": 0,
                    "customer_requirement": "Dock appointment preferred",
                    "preferred_truck_id": "",
                    "notes": "",
                }
            )
            delivery_counter += 1

        for idx in range(return_count):
            lat_offset = rng.uniform(-0.12, 0.12)
            lon_offset = rng.uniform(-0.12, 0.12)
            weight_lbs = int(rng.integers(250, 1800))
            volume_cuft = int(rng.integers(40, 220))
            priority_level = priorities[(idx + day) % 3]
            days_waiting = int(rng.integers(1, 8))
            return_value_usd = int(rng.integers(200, 2400))

            if day == 3 and idx == return_count - 1:
                lat_offset = 0.34
                lon_offset = -0.28
                weight_lbs = 3200
                volume_cuft = 360
                priority_level = "Low"
                days_waiting = 1
                return_value_usd = 350

            lat = center_lat + lat_offset
            lon = center_lon + lon_offset
            deliveries_returns.append(
                {
                    "scenario_id": "SAMPLE_A",
                    "planning_day": day,
                    "stop_id": f"R{return_counter:03d}",
                    "stop_type": "Return",
                    "customer_id": f"RC{return_counter:03d}",
                    "customer_name": f"Return Customer {return_counter}",
                    "latitude": round(lat, 6),
                    "longitude": round(lon, 6),
                    "quantity_units": int(rng.integers(2, 12)),
                    "weight_lbs": weight_lbs,
                    "volume_cuft": volume_cuft,
                    "ready_time": f"{9 + (idx % 4):02d}:00",
                    "due_time": f"{15 + (idx % 3):02d}:30",
                    "service_minutes": int(rng.integers(10, 21)),
                    "priority_level": priority_level,
                    "days_waiting": days_waiting,
                    "return_value_usd": return_value_usd,
                    "customer_requirement": "Call before pickup",
                    "preferred_truck_id": "" if idx % 2 else "T003",
                    "notes": "",
                }
            )
            return_counter += 1

    delivery_return = pd.DataFrame(deliveries_returns)
    return {
        "Warehouse_Inputs": warehouse,
        "Truck_Inputs": trucks,
        "Delivery_Return_Inputs": delivery_return,
    }


def validate_data(data):
    errors = []
    warnings = []

    for sheet_name in REQUIRED_SHEETS:
        if sheet_name not in data:
            errors.append(f"Missing required worksheet: {sheet_name}")
            continue
        missing_cols = [
            col for col in REQUIRED_COLUMNS[sheet_name] if col not in data[sheet_name].columns
        ]
        if missing_cols:
            errors.append(
                f"{sheet_name} is missing required columns: {', '.join(missing_cols)}"
            )

    if errors:
        return False, errors, warnings, data

    warehouse = data["Warehouse_Inputs"].copy()
    trucks = data["Truck_Inputs"].copy()
    stops = data["Delivery_Return_Inputs"].copy()

    for col in [
        "planning_days",
        "warehouse_latitude",
        "warehouse_longitude",
        "default_driver_shift_hours",
        "default_service_time_delivery_min",
        "default_service_time_return_min",
        "default_cost_per_mile",
        "default_driver_cost_per_hour",
        "default_co2_kg_per_mile",
        "manual_baseline_total_miles",
        "manual_baseline_total_cost",
    ]:
        warehouse[col] = normalize_numeric(warehouse[col])

    warehouse["planning_start_date"] = pd.to_datetime(
        warehouse["planning_start_date"], errors="coerce"
    ).dt.date
    warehouse["daily_dispatch_start_time"] = warehouse["daily_dispatch_start_time"].apply(
        ensure_time
    )

    for col in [
        "planning_day",
        "max_weight_lbs",
        "max_volume_cuft",
        "shift_limit_hours",
        "cost_per_mile",
        "driver_cost_per_hour",
        "co2_kg_per_mile",
    ]:
        trucks[col] = normalize_numeric(trucks[col])
    trucks["start_time"] = trucks["start_time"].apply(ensure_time)
    trucks["truck_status"] = trucks["truck_status"].fillna("Available").astype(str)
    trucks["maintenance_reason"] = trucks["maintenance_reason"].fillna("")

    for col in [
        "planning_day",
        "latitude",
        "longitude",
        "quantity_units",
        "weight_lbs",
        "volume_cuft",
        "service_minutes",
        "days_waiting",
        "return_value_usd",
    ]:
        stops[col] = normalize_numeric(stops[col])

    stops["stop_type"] = stops["stop_type"].fillna("").astype(str).str.title()
    stops["priority_level"] = stops["priority_level"].fillna("Medium").astype(str).str.title()
    stops["ready_time"] = stops["ready_time"].apply(ensure_time)
    stops["due_time"] = stops["due_time"].apply(ensure_time)

    if not set(stops["stop_type"].unique()).issubset({"Delivery", "Return"}):
        warnings.append("Some stop_type values were not Delivery/Return and may be excluded.")

    if warehouse["scenario_id"].nunique() == 0:
        errors.append("No scenario_id found in Warehouse_Inputs.")

    default_delivery_service = warehouse["default_service_time_delivery_min"].dropna()
    default_return_service = warehouse["default_service_time_return_min"].dropna()

    stops.loc[
        (stops["stop_type"] == "Delivery") & (stops["service_minutes"].isna()),
        "service_minutes",
    ] = default_delivery_service.iloc[0] if not default_delivery_service.empty else 20
    stops.loc[
        (stops["stop_type"] == "Return") & (stops["service_minutes"].isna()),
        "service_minutes",
    ] = default_return_service.iloc[0] if not default_return_service.empty else 15

    for col in ["weight_lbs", "volume_cuft", "days_waiting", "return_value_usd"]:
        stops[col] = stops[col].fillna(0)

    data = {
        "Warehouse_Inputs": warehouse,
        "Truck_Inputs": trucks,
        "Delivery_Return_Inputs": stops,
    }
    return len(errors) == 0, errors, warnings, data


def load_data(uploaded_file):
    source_label = "Built-in sample data"
    if uploaded_file is None:
        data = create_sample_data()
    else:
        workbook = pd.ExcelFile(uploaded_file)
        missing_sheets = [sheet for sheet in REQUIRED_SHEETS if sheet not in workbook.sheet_names]
        if missing_sheets:
            raise ValueError(f"Uploaded workbook is missing sheets: {', '.join(missing_sheets)}")
        data = {sheet: pd.read_excel(uploaded_file, sheet_name=sheet) for sheet in REQUIRED_SHEETS}
        source_label = uploaded_file.name

    valid, errors, warnings, cleaned_data = validate_data(data)
    if not valid:
        raise ValueError("\n".join(errors))
    return cleaned_data, warnings, source_label


def sequence_stops(start_lat, start_lon, stops_df):
    if stops_df.empty:
        return stops_df.copy()
    remaining = stops_df.copy()
    ordered_rows = []
    curr_lat, curr_lon = start_lat, start_lon
    while not remaining.empty:
        distances = remaining.apply(
            lambda row: haversine_distance(curr_lat, curr_lon, row["latitude"], row["longitude"]),
            axis=1,
        )
        next_idx = distances.idxmin()
        chosen = remaining.loc[[next_idx]]
        ordered_rows.append(chosen)
        curr_lat = chosen.iloc[0]["latitude"]
        curr_lon = chosen.iloc[0]["longitude"]
        remaining = remaining.drop(index=next_idx)
    return pd.concat(ordered_rows, ignore_index=True)


def two_opt_segment(start_lat, start_lon, end_lat, end_lon, stops_df):
    if len(stops_df) < 4:
        return stops_df.copy()

    def path_distance(df):
        pts = [(start_lat, start_lon)] + list(df[["latitude", "longitude"]].itertuples(index=False, name=None)) + [
            (end_lat, end_lon)
        ]
        total = 0
        for i in range(len(pts) - 1):
            total += haversine_distance(pts[i][0], pts[i][1], pts[i + 1][0], pts[i + 1][1])
        return total

    best = stops_df.copy().reset_index(drop=True)
    improved = True
    while improved:
        improved = False
        best_distance = path_distance(best)
        for i in range(1, len(best) - 1):
            for j in range(i + 1, len(best)):
                candidate = best.copy()
                candidate.iloc[i : j + 1] = candidate.iloc[i : j + 1].iloc[::-1].values
                candidate_distance = path_distance(candidate)
                if candidate_distance + 0.01 < best_distance:
                    best = candidate.reset_index(drop=True)
                    improved = True
                    break
            if improved:
                break
    return best


def calculate_priority_scores(returns_df, warehouse_row, controls):
    returns = returns_df.copy()
    if returns.empty:
        returns["priority_score"] = pd.Series(dtype=float)
        returns["distance_fit_score"] = pd.Series(dtype=float)
        return returns

    weight_priority = controls["high_priority_weight"]
    cost_distance_weight = controls["distance_cost_weight"]
    remaining_weight = max(0.0, 1.0 - weight_priority - cost_distance_weight)
    days_weight = remaining_weight * 0.55
    value_weight = remaining_weight * 0.45
    distance_weight = cost_distance_weight

    score_map = {"High": 100, "Medium": 60, "Low": 25}
    returns["priority_level_score"] = returns["priority_level"].map(score_map).fillna(60)

    max_days = max(returns["days_waiting"].max(), 1)
    max_value = max(returns["return_value_usd"].max(), 1)

    returns["days_score"] = (returns["days_waiting"] / max_days) * 100
    returns["value_score"] = (returns["return_value_usd"] / max_value) * 100
    returns["distance_to_warehouse"] = returns.apply(
        lambda row: haversine_distance(
            warehouse_row["warehouse_latitude"],
            warehouse_row["warehouse_longitude"],
            row["latitude"],
            row["longitude"],
        ),
        axis=1,
    )
    max_distance = max(returns["distance_to_warehouse"].max(), 1)
    returns["distance_fit_score"] = (1 - (returns["distance_to_warehouse"] / max_distance)).clip(0, 1) * 100

    returns["priority_score"] = (
        returns["priority_level_score"] * weight_priority
        + returns["days_score"] * days_weight
        + returns["value_score"] * value_weight
        + returns["distance_fit_score"] * distance_weight
    )
    returns["priority_score"] = returns["priority_score"].clip(0, 100).round(1)
    return returns


def combine_day_time(base_date, planning_day, value_time):
    plan_date = pd.to_datetime(base_date) + timedelta(days=int(planning_day) - 1)
    return datetime.combine(plan_date.date(), ensure_time(value_time))


def compute_schedule_for_route(route_state, warehouse_row, average_speed_mph):
    start_dt = route_state["start_datetime"]
    records = []
    current_dt = start_dt
    current_lat = warehouse_row["warehouse_latitude"]
    current_lon = warehouse_row["warehouse_longitude"]
    total_travel_miles = 0.0
    total_wait_minutes = 0.0

    ordered_stops = []
    if route_state["deliveries"]:
        deliveries_df = pd.DataFrame(route_state["deliveries"])
        deliveries_df = sequence_stops(current_lat, current_lon, deliveries_df)
        deliveries_df = two_opt_segment(
            current_lat,
            current_lon,
            warehouse_row["warehouse_latitude"],
            warehouse_row["warehouse_longitude"],
            deliveries_df,
        )
        ordered_stops.extend(deliveries_df.to_dict("records"))
        if not deliveries_df.empty:
            current_lat = deliveries_df.iloc[-1]["latitude"]
            current_lon = deliveries_df.iloc[-1]["longitude"]

    if route_state["returns"]:
        returns_df = pd.DataFrame(route_state["returns"])
        returns_df = sequence_stops(current_lat, current_lon, returns_df)
        returns_df = two_opt_segment(
            current_lat,
            current_lon,
            warehouse_row["warehouse_latitude"],
            warehouse_row["warehouse_longitude"],
            returns_df,
        )
        ordered_stops.extend(returns_df.to_dict("records"))

    for seq, stop in enumerate(ordered_stops, start=1):
        travel_miles = haversine_distance(current_lat, current_lon, stop["latitude"], stop["longitude"])
        travel_minutes = travel_miles / max(average_speed_mph, 1) * 60
        arrival_dt = current_dt + timedelta(minutes=travel_minutes)
        ready_dt = combine_day_time(warehouse_row["planning_start_date"], stop["planning_day"], stop["ready_time"])
        due_dt = combine_day_time(warehouse_row["planning_start_date"], stop["planning_day"], stop["due_time"])
        wait_minutes = max(0.0, (ready_dt - arrival_dt).total_seconds() / 60)
        service_start_dt = arrival_dt + timedelta(minutes=wait_minutes)
        departure_dt = service_start_dt + timedelta(minutes=float(stop["service_minutes"]))
        total_travel_miles += travel_miles
        total_wait_minutes += wait_minutes
        records.append(
            {
                "planning_day": stop["planning_day"],
                "truck_id": route_state["truck_id"],
                "sequence": seq,
                "stop_id": stop["stop_id"],
                "stop_type": stop["stop_type"],
                "customer_name": stop["customer_name"],
                "arrival_time": arrival_dt,
                "service_start_time": service_start_dt,
                "departure_time": departure_dt,
                "due_time": due_dt,
                "on_time": arrival_dt <= due_dt,
                "travel_miles_from_previous": round(travel_miles, 2),
                "wait_minutes": round(wait_minutes, 1),
                "service_minutes": float(stop["service_minutes"]),
                "weight_lbs": float(stop["weight_lbs"]),
                "volume_cuft": float(stop["volume_cuft"]),
                "priority_level": stop["priority_level"],
            }
        )
        current_dt = departure_dt
        current_lat = stop["latitude"]
        current_lon = stop["longitude"]

    final_leg = haversine_distance(
        current_lat,
        current_lon,
        warehouse_row["warehouse_latitude"],
        warehouse_row["warehouse_longitude"],
    )
    current_dt = current_dt + timedelta(minutes=(final_leg / max(average_speed_mph, 1) * 60))
    total_travel_miles += final_leg

    route_hours = (current_dt - start_dt).total_seconds() / 3600
    return {
        "schedule_records": records,
        "route_miles": round(total_travel_miles, 2),
        "route_hours": round(route_hours, 2),
        "return_to_warehouse_time": current_dt,
        "wait_minutes": round(total_wait_minutes, 1),
    }


def get_capacity_metric(stop_row):
    weight = float(stop_row.get("weight_lbs", 0) or 0)
    volume = float(stop_row.get("volume_cuft", 0) or 0)
    return weight if weight > 0 else volume


def estimate_incremental_return(route_state, return_stop, warehouse_row):
    if route_state["returns"]:
        last_stop = route_state["returns"][-1]
    elif route_state["deliveries"]:
        last_stop = route_state["deliveries"][-1]
    else:
        last_stop = {
            "latitude": warehouse_row["warehouse_latitude"],
            "longitude": warehouse_row["warehouse_longitude"],
        }
    outbound = haversine_distance(
        last_stop["latitude"], last_stop["longitude"], return_stop["latitude"], return_stop["longitude"]
    )
    home_from_last = haversine_distance(
        last_stop["latitude"],
        last_stop["longitude"],
        warehouse_row["warehouse_latitude"],
        warehouse_row["warehouse_longitude"],
    )
    home_from_return = haversine_distance(
        return_stop["latitude"],
        return_stop["longitude"],
        warehouse_row["warehouse_latitude"],
        warehouse_row["warehouse_longitude"],
    )
    return outbound + home_from_return - home_from_last


def choose_deferred_reason(reasons):
    priority_order = [
        "Truck unavailable due to maintenance",
        "Not enough remaining capacity",
        "Exceeds driver shift limit",
        "Too far from return route",
        "Time window conflict",
        "Low priority and can wait",
        "Lower benefit than other returns",
    ]
    for item in priority_order:
        if item in reasons:
            return item
    return "Lower benefit than other returns"


def optimize_routes(warehouse_row, trucks_df, stops_df, controls):
    average_speed_mph = controls["average_speed_mph"]
    planning_days = sorted(stops_df["planning_day"].dropna().astype(int).unique().tolist())

    route_rows = []
    deferred_rows = []
    schedule_rows = []
    unassigned_delivery_rows = []
    all_priority_scores = []

    for planning_day in planning_days:
        day_trucks = trucks_df[trucks_df["planning_day"] == planning_day].copy()
        day_stops = stops_df[stops_df["planning_day"] == planning_day].copy()
        day_deliveries = day_stops[day_stops["stop_type"] == "Delivery"].copy()
        day_returns = day_stops[day_stops["stop_type"] == "Return"].copy()
        day_returns = calculate_priority_scores(day_returns, warehouse_row, controls)
        all_priority_scores.append(day_returns.copy())

        available_trucks = day_trucks[
            day_trucks["truck_status"].astype(str).str.lower() == "available"
        ].copy()
        unavailable_trucks = day_trucks[
            day_trucks["truck_status"].astype(str).str.lower() != "available"
        ].copy()

        route_states = {}
        for _, truck in available_trucks.iterrows():
            shift_limit = truck["shift_limit_hours"]
            if pd.isna(shift_limit):
                shift_limit = warehouse_row["default_driver_shift_hours"]
            route_states[truck["truck_id"]] = {
                "planning_day": planning_day,
                "truck_id": truck["truck_id"],
                "truck_status": truck["truck_status"],
                "deliveries": [],
                "returns": [],
                "max_weight_lbs": truck["max_weight_lbs"] if not pd.isna(truck["max_weight_lbs"]) else 0,
                "max_volume_cuft": truck["max_volume_cuft"] if not pd.isna(truck["max_volume_cuft"]) else 0,
                "delivery_weight_lbs": 0.0,
                "delivery_volume_cuft": 0.0,
                "return_weight_lbs": 0.0,
                "return_volume_cuft": 0.0,
                "cost_per_mile": truck["cost_per_mile"]
                if not pd.isna(truck["cost_per_mile"])
                else warehouse_row["default_cost_per_mile"],
                "driver_cost_per_hour": truck["driver_cost_per_hour"]
                if not pd.isna(truck["driver_cost_per_hour"])
                else warehouse_row["default_driver_cost_per_hour"],
                "co2_kg_per_mile": truck["co2_kg_per_mile"]
                if not pd.isna(truck["co2_kg_per_mile"])
                else warehouse_row["default_co2_kg_per_mile"],
                "shift_limit_hours": shift_limit,
                "start_datetime": combine_day_time(
                    warehouse_row["planning_start_date"],
                    planning_day,
                    truck["start_time"] if not pd.isna(truck["start_time"]) else warehouse_row["daily_dispatch_start_time"],
                ),
                "projected_delivery_miles": 0.0,
                "feasibility_notes": [],
            }

        sorted_deliveries = day_deliveries.sort_values(
            by=["due_time", "priority_level", "weight_lbs"], ascending=[True, True, False]
        )

        for _, delivery in sorted_deliveries.iterrows():
            best_truck_id = None
            best_score = float("inf")
            preferred = str(delivery.get("preferred_truck_id", "") or "").strip()
            for truck_id, route_state in route_states.items():
                remaining_weight = route_state["max_weight_lbs"] - route_state["delivery_weight_lbs"]
                remaining_volume = route_state["max_volume_cuft"] - route_state["delivery_volume_cuft"]
                delivery_weight = float(delivery["weight_lbs"] or 0)
                delivery_volume = float(delivery["volume_cuft"] or 0)
                if remaining_weight < delivery_weight or remaining_volume < delivery_volume:
                    continue

                if route_state["deliveries"]:
                    origin = route_state["deliveries"][-1]
                else:
                    origin = {
                        "latitude": warehouse_row["warehouse_latitude"],
                        "longitude": warehouse_row["warehouse_longitude"],
                    }
                added_miles = haversine_distance(
                    origin["latitude"], origin["longitude"], delivery["latitude"], delivery["longitude"]
                )
                projected_service_minutes = sum(
                    float(item["service_minutes"]) for item in route_state["deliveries"]
                ) + float(delivery["service_minutes"])
                projected_travel_minutes = (
                    (route_state.get("projected_delivery_miles", 0) + added_miles) / max(average_speed_mph, 1) * 60
                )
                projected_hours = (projected_service_minutes + projected_travel_minutes) / 60
                if projected_hours > route_state["shift_limit_hours"]:
                    continue

                load_balance_penalty = len(route_state["deliveries"]) * 4
                preferred_penalty = -12 if preferred and preferred == truck_id else 0
                objective_adjustment = {
                    "Balanced plan": added_miles + load_balance_penalty,
                    "Lowest cost": added_miles * route_state["cost_per_mile"] + projected_hours * route_state["driver_cost_per_hour"] * 0.05,
                    "Shortest distance": added_miles,
                    "Highest priority returns": added_miles + load_balance_penalty,
                    "Highest return capacity utilization": added_miles + load_balance_penalty - (remaining_weight / max(route_state["max_weight_lbs"], 1)) * 5,
                }.get(controls["objective"], added_miles)
                score = objective_adjustment + preferred_penalty
                if score < best_score:
                    best_score = score
                    best_truck_id = truck_id
                    best_added_miles = added_miles

            if best_truck_id is None:
                unassigned_delivery_rows.append(
                    {
                        "planning_day": planning_day,
                        "stop_id": delivery["stop_id"],
                        "customer_name": delivery["customer_name"],
                        "reason": "No feasible truck capacity or shift availability.",
                    }
                )
                continue

            route_states[best_truck_id]["deliveries"].append(delivery.to_dict())
            route_states[best_truck_id]["delivery_weight_lbs"] += float(delivery["weight_lbs"] or 0)
            route_states[best_truck_id]["delivery_volume_cuft"] += float(delivery["volume_cuft"] or 0)
            route_states[best_truck_id]["projected_delivery_miles"] = (
                route_states[best_truck_id].get("projected_delivery_miles", 0) + best_added_miles
            )

        assigned_return_ids = set()
        sorted_returns = day_returns.sort_values(by=["priority_score", "days_waiting"], ascending=[False, False])

        for _, return_stop in sorted_returns.iterrows():
            candidate_scores = []
            candidate_failures = []
            for truck_id, route_state in route_states.items():
                reasons = []
                remaining_weight = (
                    route_state["max_weight_lbs"]
                    - route_state["delivery_weight_lbs"]
                    - route_state["return_weight_lbs"]
                )
                remaining_volume = (
                    route_state["max_volume_cuft"]
                    - route_state["delivery_volume_cuft"]
                    - route_state["return_volume_cuft"]
                )
                return_weight = float(return_stop["weight_lbs"] or 0)
                return_volume = float(return_stop["volume_cuft"] or 0)
                if remaining_weight < return_weight or remaining_volume < return_volume:
                    reasons.append("Not enough remaining capacity")

                detour_miles = estimate_incremental_return(route_state, return_stop, warehouse_row)
                if return_stop["priority_level"] != "High" and detour_miles > controls["max_detour_miles"]:
                    reasons.append("Too far from return route")

                provisional_state = {
                    **route_state,
                    "deliveries": list(route_state["deliveries"]),
                    "returns": list(route_state["returns"]) + [return_stop.to_dict()],
                }
                schedule_summary = compute_schedule_for_route(
                    provisional_state, warehouse_row, average_speed_mph
                )
                if schedule_summary["route_hours"] > (
                    route_state["shift_limit_hours"] - controls["shift_buffer_minutes"] / 60
                ):
                    reasons.append("Exceeds driver shift limit")

                return_due_dt = combine_day_time(
                    warehouse_row["planning_start_date"], planning_day, return_stop["due_time"]
                )
                last_return_record = next(
                    (r for r in schedule_summary["schedule_records"] if r["stop_id"] == return_stop["stop_id"]),
                    None,
                )
                if last_return_record and last_return_record["arrival_time"] > return_due_dt:
                    reasons.append("Time window conflict")

                if (
                    controls["allow_defer_low_medium"]
                    and return_stop["priority_level"] in {"Low", "Medium"}
                    and return_stop["days_waiting"] <= 2
                    and detour_miles > controls["max_detour_miles"] * 0.65
                ):
                    reasons.append("Low priority and can wait")

                if reasons:
                    candidate_failures.extend(reasons)
                    continue

                fill_rate = return_weight / max(remaining_weight, 1)
                score = (
                    float(return_stop["priority_score"])
                    + fill_rate * 25
                    - detour_miles * controls["distance_cost_weight"] * 3
                )
                if controls["objective"] == "Lowest cost":
                    score -= detour_miles * route_state["cost_per_mile"] * 0.7
                elif controls["objective"] == "Shortest distance":
                    score -= detour_miles * 1.1
                elif controls["objective"] == "Highest return capacity utilization":
                    score += fill_rate * 30
                candidate_scores.append((score, truck_id, detour_miles, schedule_summary))

            if candidate_scores:
                candidate_scores.sort(key=lambda item: item[0], reverse=True)
                _, best_truck_id, _, best_schedule = candidate_scores[0]
                route_states[best_truck_id]["returns"].append(return_stop.to_dict())
                route_states[best_truck_id]["return_weight_lbs"] += float(return_stop["weight_lbs"] or 0)
                route_states[best_truck_id]["return_volume_cuft"] += float(return_stop["volume_cuft"] or 0)
                route_states[best_truck_id]["latest_schedule_preview"] = best_schedule
                assigned_return_ids.add(return_stop["stop_id"])
            else:
                nearest_route_distance = None
                if route_states:
                    distances = []
                    for route_state in route_states.values():
                        last_anchor = route_state["deliveries"][-1] if route_state["deliveries"] else {
                            "latitude": warehouse_row["warehouse_latitude"],
                            "longitude": warehouse_row["warehouse_longitude"],
                        }
                        distances.append(
                            haversine_distance(
                                last_anchor["latitude"],
                                last_anchor["longitude"],
                                return_stop["latitude"],
                                return_stop["longitude"],
                            )
                        )
                    nearest_route_distance = round(min(distances), 2) if distances else None
                deferred_rows.append(
                    {
                        "planning_day": planning_day,
                        "return_id": return_stop["stop_id"],
                        "customer_name": return_stop["customer_name"],
                        "priority_level": return_stop["priority_level"],
                        "days_waiting": return_stop["days_waiting"],
                        "return_value_usd": return_stop["return_value_usd"],
                        "weight_lbs": return_stop["weight_lbs"],
                        "nearest_route_distance_miles": nearest_route_distance,
                        "reason_deferred": choose_deferred_reason(candidate_failures),
                    }
                )

        for _, truck in unavailable_trucks.iterrows():
            route_rows.append(
                {
                    "planning_day": planning_day,
                    "truck_id": truck["truck_id"],
                    "truck_status": truck["truck_status"],
                    "route_sequence": "Warehouse -> Warehouse",
                    "delivery_stops": 0,
                    "return_stops": 0,
                    "route_miles": 0.0,
                    "route_hours": 0.0,
                    "delivery_weight_lbs": 0.0,
                    "return_weight_lbs": 0.0,
                    "available_return_capacity_lbs": 0.0,
                    "return_capacity_utilization_%": 0.0,
                    "on_time_deliveries": 0,
                    "late_deliveries": 0,
                    "feasible": False,
                    "feasibility_notes": truck["maintenance_reason"] or "Truck unavailable due to maintenance",
                    "transport_cost": 0.0,
                    "co2_kg": 0.0,
                }
            )

        for truck_id, route_state in route_states.items():
            schedule_summary = compute_schedule_for_route(route_state, warehouse_row, average_speed_mph)
            stop_ids = [row["stop_id"] for row in schedule_summary["schedule_records"]]
            route_sequence = "Warehouse -> " + " -> ".join(stop_ids) + " -> Warehouse" if stop_ids else "Warehouse -> Warehouse"
            delivery_records = [row for row in schedule_summary["schedule_records"] if row["stop_type"] == "Delivery"]
            return_records = [row for row in schedule_summary["schedule_records"] if row["stop_type"] == "Return"]
            on_time_deliveries = sum(1 for row in delivery_records if row["on_time"])
            late_deliveries = len(delivery_records) - on_time_deliveries
            transport_cost = (
                schedule_summary["route_miles"] * route_state["cost_per_mile"]
                + schedule_summary["route_hours"] * route_state["driver_cost_per_hour"]
            )
            available_return_capacity = max(
                route_state["max_weight_lbs"] - route_state["delivery_weight_lbs"], 0
            )
            utilization = (
                route_state["return_weight_lbs"] / available_return_capacity * 100
                if available_return_capacity > 0
                else 0
            )
            feasible = schedule_summary["route_hours"] <= route_state["shift_limit_hours"]
            if late_deliveries > 0:
                route_state["feasibility_notes"].append(f"{late_deliveries} late deliveries")
            if not feasible:
                route_state["feasibility_notes"].append("Shift limit exceeded after sequencing")

            route_rows.append(
                {
                    "planning_day": planning_day,
                    "truck_id": truck_id,
                    "truck_status": route_state["truck_status"],
                    "route_sequence": route_sequence,
                    "delivery_stops": len(delivery_records),
                    "return_stops": len(return_records),
                    "route_miles": round(schedule_summary["route_miles"], 2),
                    "route_hours": round(schedule_summary["route_hours"], 2),
                    "delivery_weight_lbs": round(route_state["delivery_weight_lbs"], 1),
                    "return_weight_lbs": round(route_state["return_weight_lbs"], 1),
                    "available_return_capacity_lbs": round(available_return_capacity, 1),
                    "return_capacity_utilization_%": round(utilization, 1),
                    "on_time_deliveries": on_time_deliveries,
                    "late_deliveries": late_deliveries,
                    "feasible": feasible,
                    "feasibility_notes": "; ".join(route_state["feasibility_notes"]) if route_state["feasibility_notes"] else "Feasible",
                    "transport_cost": round(transport_cost, 2),
                    "co2_kg": round(schedule_summary["route_miles"] * route_state["co2_kg_per_mile"], 2),
                }
            )
            schedule_rows.extend(schedule_summary["schedule_records"])

    priority_scores_df = (
        pd.concat(all_priority_scores, ignore_index=True)
        if all_priority_scores
        else pd.DataFrame(columns=["planning_day", "stop_id", "priority_score"])
    )
    return {
        "truck_routes": pd.DataFrame(route_rows),
        "deferred_returns": pd.DataFrame(deferred_rows),
        "stop_schedule": pd.DataFrame(schedule_rows),
        "priority_scores": priority_scores_df,
        "unassigned_deliveries": pd.DataFrame(unassigned_delivery_rows),
    }


def calculate_kpis(warehouse_row, scenario_stops, optimization_results):
    routes = optimization_results["truck_routes"].copy()
    schedule = optimization_results["stop_schedule"].copy()
    unassigned = optimization_results["unassigned_deliveries"].copy()
    deferred = optimization_results["deferred_returns"].copy()

    total_deliveries = int((scenario_stops["stop_type"] == "Delivery").sum())
    completed_deliveries = int(len(schedule[schedule["stop_type"] == "Delivery"]))
    total_high_priority_returns = int(
        ((scenario_stops["stop_type"] == "Return") & (scenario_stops["priority_level"] == "High")).sum()
    )
    picked_high_priority_returns = int(
        len(
            schedule[
                (schedule["stop_type"] == "Return") & (schedule["priority_level"] == "High")
            ]
        )
    )
    on_time_deliveries = int(
        len(schedule[(schedule["stop_type"] == "Delivery") & (schedule["on_time"] == True)])
    )
    total_returns = int((scenario_stops["stop_type"] == "Return").sum())
    total_return_weight_picked = float(schedule[schedule["stop_type"] == "Return"]["weight_lbs"].sum())

    used_routes = routes[routes["delivery_stops"] + routes["return_stops"] > 0]
    total_capacity_after_deliveries = float(used_routes["available_return_capacity_lbs"].sum())
    if total_capacity_after_deliveries == 0:
        total_capacity_after_deliveries = max(total_return_weight_picked, 1.0)

    optimized_total_cost = float(routes["transport_cost"].sum())
    optimized_total_miles = float(routes["route_miles"].sum())

    baseline_cost = warehouse_row["manual_baseline_total_cost"]
    baseline_miles = warehouse_row["manual_baseline_total_miles"]
    baseline_note = ""
    if pd.isna(baseline_cost) or baseline_cost <= 0:
        baseline_cost = round(optimized_total_cost * 1.18, 2)
        baseline_note = "Manual baseline cost missing; estimated at optimized cost x 1.18."
    if pd.isna(baseline_miles) or baseline_miles <= 0:
        baseline_miles = round(optimized_total_miles * 1.18, 2)
        baseline_note = (baseline_note + " " if baseline_note else "") + "Manual baseline miles missing; estimated at optimized miles x 1.18."

    manual_high_priority_returns = math.floor(min(total_high_priority_returns, total_high_priority_returns * 0.6))
    manual_return_capacity_utilization = 45.0

    kpis = {
        "delivery_completion_rate": completed_deliveries / total_deliveries if total_deliveries else 0,
        "on_time_delivery_rate": on_time_deliveries / total_deliveries if total_deliveries else 0,
        "high_priority_return_pickup_rate": picked_high_priority_returns / total_high_priority_returns
        if total_high_priority_returns
        else 0,
        "deferred_return_count": int(len(deferred)),
        "total_transportation_cost": round(optimized_total_cost, 2),
        "cost_savings_vs_manual": round(baseline_cost - optimized_total_cost, 2),
        "total_miles_traveled": round(optimized_total_miles, 2),
        "return_capacity_utilization": total_return_weight_picked / total_capacity_after_deliveries
        if total_capacity_after_deliveries
        else 0,
        "baseline_total_cost": round(float(baseline_cost), 2),
        "baseline_total_miles": round(float(baseline_miles), 2),
        "manual_high_priority_returns": manual_high_priority_returns,
        "manual_return_capacity_utilization": manual_return_capacity_utilization,
        "unassigned_delivery_count": int(len(unassigned)),
        "baseline_note": baseline_note,
        "high_priority_return_count": total_high_priority_returns,
        "picked_high_priority_returns": picked_high_priority_returns,
        "completed_deliveries": completed_deliveries,
        "total_deliveries": total_deliveries,
        "on_time_deliveries": on_time_deliveries,
        "total_returns": total_returns,
    }
    return kpis


def build_kpi_cards(kpis):
    metrics = [
        ("Delivery completion rate", f"{kpis['delivery_completion_rate']:.1%}", f"{kpis['completed_deliveries']} / {kpis['total_deliveries']}"),
        ("On-time delivery rate", f"{kpis['on_time_delivery_rate']:.1%}", f"{kpis['on_time_deliveries']} on time"),
        ("High-priority return pickup rate", f"{kpis['high_priority_return_pickup_rate']:.1%}", f"{kpis['picked_high_priority_returns']} / {kpis['high_priority_return_count']}"),
        ("Deferred return count", f"{kpis['deferred_return_count']}", "Returns not picked up"),
        ("Total transportation cost", f"${kpis['total_transportation_cost']:,.0f}", "Optimized plan"),
        ("Cost savings vs manual baseline", f"${kpis['cost_savings_vs_manual']:,.0f}", "Positive is better"),
        ("Total miles traveled", f"{kpis['total_miles_traveled']:,.1f}", "Across all trucks"),
        ("Return capacity utilization", f"{kpis['return_capacity_utilization']:.1%}", "Picked return weight / available return capacity"),
    ]

    cols = st.columns(4)
    for idx, (label, value, subtext) in enumerate(metrics):
        color = GREEN if label in {"Cost savings vs manual baseline"} and kpis["cost_savings_vs_manual"] >= 0 else NAVY
        if label == "Deferred return count" and kpis["deferred_return_count"] > 0:
            color = ORANGE
        if label == "Delivery completion rate" and kpis["delivery_completion_rate"] < 1:
            color = RED
        with cols[idx % 4]:
            st.markdown(
                f"""
                <div style="background:{LIGHT_BG}; border-left:4px solid {color}; padding:14px 16px; border-radius:10px; min-height:118px;">
                    <div style="font-size:0.9rem; color:#486581;">{label}</div>
                    <div style="font-size:1.7rem; color:{NAVY}; font-weight:700; margin-top:6px;">{value}</div>
                    <div style="font-size:0.8rem; color:#7B8794; margin-top:8px;">{subtext}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )


def build_comparison_chart(kpis):
    categories = [
        "Total cost",
        "Total miles",
        "High-priority returns picked",
        "Return capacity utilization %",
    ]
    manual_values = [
        kpis["baseline_total_cost"],
        kpis["baseline_total_miles"],
        kpis["manual_high_priority_returns"],
        kpis["manual_return_capacity_utilization"],
    ]
    optimized_values = [
        kpis["total_transportation_cost"],
        kpis["total_miles_traveled"],
        kpis["picked_high_priority_returns"],
        kpis["return_capacity_utilization"] * 100,
    ]

    fig = go.Figure()
    fig.add_bar(name="Manual baseline", x=categories, y=manual_values, marker_color="#9FB3C8")
    fig.add_bar(name="Optimized plan", x=categories, y=optimized_values, marker_color=NAVY)
    fig.update_layout(
        barmode="group",
        paper_bgcolor="white",
        plot_bgcolor="white",
        margin=dict(l=10, r=10, t=10, b=10),
        legend=dict(orientation="h", y=1.08),
        yaxis_title="Value",
    )
    return fig


def build_capacity_chart(routes_df):
    active_routes = routes_df.copy()
    active_routes["label"] = active_routes["truck_id"] + " | Day " + active_routes["planning_day"].astype(str)
    fig = go.Figure()
    fig.add_bar(
        x=active_routes["label"],
        y=active_routes["return_capacity_utilization_%"],
        marker_color=np.where(active_routes["truck_status"].str.lower() == "available", GREEN, "#CBD2D9"),
        text=active_routes["return_capacity_utilization_%"].round(1).astype(str) + "%",
        textposition="outside",
    )
    fig.update_layout(
        title="Return Capacity Utilization by Truck and Day",
        paper_bgcolor="white",
        plot_bgcolor="white",
        margin=dict(l=10, r=10, t=45, b=10),
        yaxis_title="Utilization %",
        xaxis_title="Truck / Day",
    )
    return fig


def create_output_excel(kpis, optimization_results, inputs_summary):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        pd.DataFrame([kpis]).to_excel(writer, sheet_name="KPI_Summary", index=False)
        optimization_results["truck_routes"].to_excel(writer, sheet_name="Truck_Routes", index=False)
        optimization_results["deferred_returns"].to_excel(writer, sheet_name="Deferred_Returns", index=False)
        optimization_results["stop_schedule"].to_excel(writer, sheet_name="Stop_Level_Schedule", index=False)
        optimization_results["priority_scores"].to_excel(writer, sheet_name="Return_Priority_Scores", index=False)
        inputs_summary.to_excel(writer, sheet_name="Input_Data_Summary", index=False)
    output.seek(0)
    return output.getvalue()


def create_template_workbook_bytes():
    sample_data = create_sample_data()
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        for sheet_name, df in sample_data.items():
            df.to_excel(writer, sheet_name=sheet_name, index=False)
    output.seek(0)
    return output.getvalue()


def save_sample_template_file():
    template_path = "sample_upload_template.xlsx"
    try:
        with open(template_path, "wb") as file_handle:
            file_handle.write(create_template_workbook_bytes())
    except OSError:
        return None
    return template_path


def summarize_inputs(warehouse_row, trucks_df, stops_df):
    return pd.DataFrame(
        [
            {"metric": "Scenario ID", "value": warehouse_row["scenario_id"]},
            {"metric": "Warehouse", "value": warehouse_row["warehouse_name"]},
            {"metric": "Planning days", "value": int(warehouse_row["planning_days"])},
            {"metric": "Total trucks", "value": trucks_df["truck_id"].nunique()},
            {
                "metric": "Available trucks",
                "value": int((trucks_df["truck_status"].str.lower() == "available").sum()),
            },
            {
                "metric": "Maintenance trucks",
                "value": int((trucks_df["truck_status"].str.lower() != "available").sum()),
            },
            {"metric": "Delivery stops", "value": int((stops_df["stop_type"] == "Delivery").sum())},
            {"metric": "Return candidates", "value": int((stops_df["stop_type"] == "Return").sum())},
        ]
    )


def render_route_expanders(schedule_df):
    if schedule_df.empty:
        st.info("No route schedule records available.")
        return
    for truck_id in schedule_df["truck_id"].dropna().unique():
        truck_schedule = schedule_df[schedule_df["truck_id"] == truck_id].copy()
        with st.expander(f"Truck {truck_id} detailed stop schedule", expanded=False):
            truck_schedule["arrival_time"] = pd.to_datetime(truck_schedule["arrival_time"]).dt.strftime("%Y-%m-%d %H:%M")
            truck_schedule["service_start_time"] = pd.to_datetime(truck_schedule["service_start_time"]).dt.strftime("%Y-%m-%d %H:%M")
            truck_schedule["departure_time"] = pd.to_datetime(truck_schedule["departure_time"]).dt.strftime("%Y-%m-%d %H:%M")
            st.dataframe(
                truck_schedule[
                    [
                        "planning_day",
                        "sequence",
                        "stop_id",
                        "stop_type",
                        "customer_name",
                        "arrival_time",
                        "service_start_time",
                        "departure_time",
                        "travel_miles_from_previous",
                        "wait_minutes",
                        "service_minutes",
                        "on_time",
                    ]
                ],
                use_container_width=True,
                hide_index=True,
            )


def main():
    st.set_page_config(
        page_title="ReturnRoute Optimizer",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    st.markdown(
        f"""
        <style>
        .stApp {{
            background: linear-gradient(180deg, #FFFFFF 0%, #F8FAFC 100%);
        }}
        h1, h2, h3 {{
            color: {NAVY};
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )

    st.title("ReturnRoute Optimizer")
    st.caption("Delivery Backhaul + Reverse Logistics Decision Tool")

    save_sample_template_file()

    st.sidebar.header("Scenario Controls")
    uploaded_file = st.sidebar.file_uploader("Upload Excel workbook", type=["xlsx"])
    objective = st.sidebar.selectbox(
        "Optimization objective",
        [
            "Balanced plan",
            "Lowest cost",
            "Shortest distance",
            "Highest priority returns",
            "Highest return capacity utilization",
        ],
    )
    max_detour_miles = st.sidebar.slider("Max detour miles per return pickup", 5, 60, 18)
    shift_buffer_minutes = st.sidebar.slider("Driver shift buffer minutes", 0, 120, 30)
    high_priority_weight = st.sidebar.slider("High-priority return weight", 0.20, 0.60, 0.35, 0.05)
    distance_cost_weight = st.sidebar.slider("Distance / cost weight", 0.05, 0.35, 0.20, 0.05)
    allow_defer_low_medium = st.sidebar.checkbox("Allow medium/low priority returns to be deferred", value=True)
    average_speed_mph = st.sidebar.slider("Average travel speed (mph)", 20, 50, 30)
    run_clicked = st.sidebar.button("Run Optimization", type="primary", use_container_width=True)
    sample_template_bytes = create_template_workbook_bytes()
    st.sidebar.download_button(
        "Download sample upload template",
        data=sample_template_bytes,
        file_name="sample_upload_template.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True,
    )

    try:
        data, warnings, source_label = load_data(uploaded_file)
    except Exception as exc:
        st.error(f"Unable to load data: {exc}")
        st.stop()

    for warning in warnings:
        st.warning(warning)

    scenario_ids = data["Warehouse_Inputs"]["scenario_id"].dropna().astype(str).unique().tolist()
    scenario_id = (
        st.sidebar.selectbox("Scenario selector", scenario_ids)
        if len(scenario_ids) > 1
        else scenario_ids[0]
    )

    controls = {
        "objective": objective,
        "max_detour_miles": max_detour_miles,
        "shift_buffer_minutes": shift_buffer_minutes,
        "high_priority_weight": high_priority_weight,
        "distance_cost_weight": distance_cost_weight,
        "allow_defer_low_medium": allow_defer_low_medium,
        "average_speed_mph": average_speed_mph,
    }

    scenario_warehouse = data["Warehouse_Inputs"][
        data["Warehouse_Inputs"]["scenario_id"].astype(str) == str(scenario_id)
    ].copy()
    scenario_trucks = data["Truck_Inputs"][
        data["Truck_Inputs"]["scenario_id"].astype(str) == str(scenario_id)
    ].copy()
    scenario_stops = data["Delivery_Return_Inputs"][
        data["Delivery_Return_Inputs"]["scenario_id"].astype(str) == str(scenario_id)
    ].copy()

    if scenario_warehouse.empty:
        st.error("The selected scenario_id does not exist in Warehouse_Inputs.")
        st.stop()

    warehouse_row = scenario_warehouse.iloc[0]

    if run_clicked or "optimization_results" not in st.session_state or st.session_state.get("active_scenario") != scenario_id:
        optimization_results = optimize_routes(warehouse_row, scenario_trucks, scenario_stops, controls)
        kpis = calculate_kpis(warehouse_row, scenario_stops, optimization_results)
        st.session_state["optimization_results"] = optimization_results
        st.session_state["kpis"] = kpis
        st.session_state["active_scenario"] = scenario_id
        st.session_state["active_controls"] = controls
    else:
        optimization_results = st.session_state["optimization_results"]
        kpis = st.session_state["kpis"]

    if kpis["delivery_completion_rate"] < 1:
        st.warning(
            f"Only {kpis['completed_deliveries']} of {kpis['total_deliveries']} deliveries were assigned. Review truck capacity, shift limits, or maintenance availability."
        )
    if kpis["baseline_note"]:
        st.info(kpis["baseline_note"])

    tabs = st.tabs(
        [
            "Overview",
            "Optimization Results",
            "Route Details",
            "Deferred Returns",
            "Data Preview",
            "Method & Limitations",
        ]
    )

    with tabs[0]:
        st.subheader("Business Context")
        st.write(
            "Deliveries are mandatory. Returns are optional and added as backhaul pickups when capacity, time, and priority make sense."
        )
        st.write(
            "This prototype helps a warehouse analyst compare a manual transportation plan to a practical routing heuristic across a three-day planning horizon."
        )
        input_summary = summarize_inputs(warehouse_row, scenario_trucks, scenario_stops)
        summary_cols = st.columns(3)
        summary_items = input_summary.to_dict("records")
        for idx, item in enumerate(summary_items):
            with summary_cols[idx % 3]:
                st.metric(item["metric"], item["value"])
        st.caption(f"Data source: {source_label}")

    with tabs[1]:
        st.subheader("Optimization Results")
        build_kpi_cards(kpis)
        st.markdown(" ")
        left_col, right_col = st.columns([1.25, 1])
        with left_col:
            st.plotly_chart(build_comparison_chart(kpis), use_container_width=True)
            st.caption(
                "Manual high-priority returns picked and manual return capacity utilization are baseline assumptions for classroom comparison."
            )
        with right_col:
            st.plotly_chart(
                build_capacity_chart(optimization_results["truck_routes"]),
                use_container_width=True,
            )
        available_trucks_count = int(
            scenario_trucks["truck_status"].astype(str).str.lower().eq("available").sum()
        )
        picked_returns = int(len(optimization_results["stop_schedule"][optimization_results["stop_schedule"]["stop_type"] == "Return"]))
        total_returns = int((scenario_stops["stop_type"] == "Return").sum())
        st.success(
            f"Recommended plan uses {available_trucks_count} available trucks, completes {kpis['delivery_completion_rate']:.0%} of deliveries, picks up {picked_returns} of {total_returns} returns, and changes cost by ${kpis['cost_savings_vs_manual']:,.0f} versus the manual baseline."
        )

    with tabs[2]:
        st.subheader("Truck Route Table")
        st.dataframe(
            optimization_results["truck_routes"][
                [
                    "planning_day",
                    "truck_id",
                    "truck_status",
                    "route_sequence",
                    "delivery_stops",
                    "return_stops",
                    "route_miles",
                    "route_hours",
                    "delivery_weight_lbs",
                    "return_weight_lbs",
                    "return_capacity_utilization_%",
                    "on_time_deliveries",
                    "late_deliveries",
                    "feasible",
                    "feasibility_notes",
                ]
            ],
            use_container_width=True,
            hide_index=True,
        )
        render_route_expanders(optimization_results["stop_schedule"])

    with tabs[3]:
        st.subheader("Deferred Returns")
        deferred_df = optimization_results["deferred_returns"]
        if deferred_df.empty:
            st.success("No returns were deferred in the current scenario.")
        else:
            st.dataframe(deferred_df, use_container_width=True, hide_index=True)
            reason_counts = deferred_df["reason_deferred"].value_counts().reset_index()
            reason_counts.columns = ["reason_deferred", "count"]
            fig = go.Figure()
            fig.add_bar(
                x=reason_counts["reason_deferred"],
                y=reason_counts["count"],
                marker_color=ORANGE,
            )
            fig.update_layout(
                paper_bgcolor="white",
                plot_bgcolor="white",
                margin=dict(l=10, r=10, t=10, b=10),
                yaxis_title="Deferred returns",
                xaxis_title="Reason",
            )
            st.plotly_chart(fig, use_container_width=True)

    with tabs[4]:
        st.subheader("Data Preview")
        priority_preview = optimization_results["priority_scores"][
            [
                "planning_day",
                "stop_id",
                "customer_name",
                "priority_level",
                "days_waiting",
                "return_value_usd",
                "distance_fit_score",
                "priority_score",
            ]
        ] if not optimization_results["priority_scores"].empty else pd.DataFrame()

        st.write("Warehouse data")
        st.dataframe(scenario_warehouse, use_container_width=True, hide_index=True)
        st.write("Truck data")
        st.dataframe(scenario_trucks, use_container_width=True, hide_index=True)
        st.write("Delivery and return data")
        st.dataframe(scenario_stops, use_container_width=True, hide_index=True)
        st.write("Return priority scores")
        st.dataframe(priority_preview, use_container_width=True, hide_index=True)

    with tabs[5]:
        st.subheader("Method")
        st.write(
            "The model validates the workbook, fills missing defaults, estimates miles with the Haversine formula, assigns mandatory deliveries first, scores return pickups, and then adds feasible backhaul returns while respecting capacity, shift time, and detour rules."
        )
        st.write(
            "Route sequencing uses nearest-neighbor ordering with a lightweight 2-opt improvement inside the delivery and return segments. Arrival times include travel, waiting, and service minutes."
        )
        st.subheader("Limitations")
        st.write(
            "This prototype uses straight-line distance rather than road-network travel, excludes live traffic and formal break-rule optimization, and relies on a practical heuristic rather than a guaranteed global optimum."
        )
        st.write(
            "Real deployment would need cleaner master data, better service-time estimates, and integration with WMS, TMS, or ERP systems."
        )

    input_summary = summarize_inputs(warehouse_row, scenario_trucks, scenario_stops)
    output_bytes = create_output_excel(kpis, optimization_results, input_summary)
    st.download_button(
        "Download optimization results as Excel",
        data=output_bytes,
        file_name=f"returnroute_optimizer_{scenario_id}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )


if __name__ == "__main__":
    main()
