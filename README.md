# ReturnRoute Optimizer

ReturnRoute Optimizer is a Streamlit dashboard for a managerial analytics final project. It helps a warehouse analyst plan outbound delivery routes over a 3-day horizon and decide which reverse-logistics pickups should be added as backhaul instead of sending trucks back empty.

## Business Problem

The warehouse has a small fleet and may lose capacity on some days because of maintenance. Deliveries are mandatory, while return pickups are optional and should only be added when they fit remaining truck capacity, driver shift limits, route detour limits, and business priority.

The app is designed to help a planner:

- complete as many required deliveries as possible,
- improve truck utilization,
- reduce miles and transportation cost,
- prioritize important returns,
- explain why some returns were deferred,
- compare an optimized heuristic plan to a manual baseline.

## Run the App

1. Install dependencies:

```bash
pip install -r requirements.txt
```

2. Start Streamlit:

```bash
streamlit run app.py
```

If no workbook is uploaded, the app automatically runs using built-in sample data.

## Expected Excel Format

Upload one `.xlsx` workbook with these worksheets:

1. `Warehouse_Inputs`
2. `Truck_Inputs`
3. `Delivery_Return_Inputs`

The app also includes a sidebar button to download a sample upload template in the expected format.

### Warehouse_Inputs

Required columns:

- `scenario_id`
- `warehouse_id`
- `warehouse_name`
- `planning_start_date`
- `planning_days`
- `warehouse_latitude`
- `warehouse_longitude`
- `daily_dispatch_start_time`
- `default_driver_shift_hours`
- `default_service_time_delivery_min`
- `default_service_time_return_min`
- `default_cost_per_mile`
- `default_driver_cost_per_hour`
- `default_co2_kg_per_mile`
- `manual_baseline_total_miles`
- `manual_baseline_total_cost`
- `manual_baseline_notes`

### Truck_Inputs

Required columns:

- `scenario_id`
- `planning_day`
- `truck_id`
- `truck_status`
- `maintenance_reason`
- `vehicle_type`
- `max_weight_lbs`
- `max_volume_cuft`
- `start_time`
- `shift_limit_hours`
- `cost_per_mile`
- `driver_cost_per_hour`
- `co2_kg_per_mile`
- `notes`

### Delivery_Return_Inputs

Required columns:

- `scenario_id`
- `planning_day`
- `stop_id`
- `stop_type`
- `customer_id`
- `customer_name`
- `latitude`
- `longitude`
- `quantity_units`
- `weight_lbs`
- `volume_cuft`
- `ready_time`
- `due_time`
- `service_minutes`
- `priority_level`
- `days_waiting`
- `return_value_usd`
- `customer_requirement`
- `preferred_truck_id`
- `notes`

## Optimization Method

The app uses a practical heuristic that is easy to explain in class:

1. Validates sheets and required columns.
2. Cleans numeric and time fields.
3. Fills missing service times from warehouse defaults.
4. Excludes trucks that are not marked `Available`.
5. Calculates straight-line distances with the Haversine formula.
6. Assigns mandatory deliveries first using a feasible greedy heuristic.
7. Scores return pickups using:
   - priority level,
   - days waiting,
   - return value,
   - distance fit.
8. Adds returns as backhaul only when remaining capacity, detour, time windows, and shift limits still work.
9. Sequences stops with nearest-neighbor logic and a simple 2-opt improvement inside delivery and return segments.
10. Calculates arrival times, route miles, route hours, cost, and comparison KPIs.

## KPI Definitions

The dashboard highlights:

- Delivery completion rate
- On-time delivery rate
- High-priority return pickup rate
- Deferred return count
- Total transportation cost
- Cost savings vs manual baseline
- Total miles traveled
- Return capacity utilization

Manual baseline cost and miles come from `Warehouse_Inputs`. If they are missing, the app estimates them as `optimized x 1.18` and clearly notes that fallback assumption.

Manual baseline high-priority returns picked and return capacity utilization are classroom comparison assumptions:

- Manual high-priority returns picked = `min(total high-priority returns, floor(60% of total high-priority returns))`
- Manual return capacity utilization = `45%`

## Output Download

The app can export results to Excel with these sheets:

- `KPI_Summary`
- `Truck_Routes`
- `Deferred_Returns`
- `Stop_Level_Schedule`
- `Return_Priority_Scores`
- `Input_Data_Summary`

## Limitations

- Distances are straight-line estimates rather than real road miles.
- No live traffic or dynamic travel times are included.
- Driver break rules are simplified to shift-hour limits.
- The heuristic is reliable for a prototype but does not guarantee a mathematical global optimum.
- Service times, weights, volumes, and return values are assumed to be reasonably accurate.
- A production deployment would require integration with WMS, TMS, or ERP systems.
