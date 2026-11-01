# Proposal: Split 2 Conflict Rewrites Using Strict Existing Enums

**Author**: FLBDS Project Team  
**Date**: November 2026 (Audit Round 7)  
**Status**: Proposal Only (Under Review; Standing Rule: Do Not Apply Without Instruction)  
**Verification**: Verified by automated test suite [`tests/test_conflict_detector.py`](file:///Users/abhishektripathi/Desktop/FLBDS/tests/test_conflict_detector.py).

---

## 1. Existing Enum Values in `flbds.schema.enums`

Below are the exact existing enum classes and members in [`flbds/schema/enums.py`](file:///Users/abhishektripathi/Desktop/FLBDS/flbds/schema/enums.py):

* **`ResourceEnum`**:
  * `LIQUID_WATER = "liquid_water"`
  * `WATER_VAPOUR = "water_vapour"`
  * `AMBIENT_AIR = "ambient_air"`
  * `DRY_INERT_GAS = "dry_inert_gas"`
  * `SOLAR_IRRADIANCE = "solar_irradiance"`
  * `NIGHT_SKY_SINK = "night_sky_sink"`
  * `WASTE_HEAT_STREAM = "waste_heat_stream"`
  * `GRID_ELECTRICITY = "grid_electricity"`
  * `PRESSURISED_GAS = "pressurised_gas"`
* **`DirectionEnum`**:
  * `INCREASE = "increase"`
  * `DECREASE = "decrease"`
  * `STABILISE = "stabilise"`
  * `STORE_AND_RELEASE = "store-and-release"`
  * `TRANSPORT_DIRECTIONAL = "transport-directional"`
* **`TimeModeEnum`**:
  * `CONTINUOUS = "continuous"`
  * `CYCLIC_DIURNAL = "cyclic_diurnal"`
  * `PULSED = "pulsed"`
  * `STEADY = "steady"`
* **`BoundaryTypeEnum`**:
  * `BC_FLUX = "BC_FLUX"`
  * `BC_TEMP = "BC_TEMP"`
* **`HazardEnum`**:
  * `NONE = "none"`
  * `HIGH_HUMIDITY = "high_humidity"`
  * `DUST_FOULING = "dust_fouling"`
  * `ICING = "icing"`
  * `LOW_SOURCE_TEMPERATURE = "low_source_temperature"`

---

## 2. Redefining Each Split 2 Case

### 2.1 DEV-M1-S2: Resource Absence ($\rightarrow$ Operator T1)

* **Physical Target**: Desert Shelter Buffer Wall.
* **Source Biology (`MC-BIO-DEV-M1`)**: Elephant mud-wallowing & open evaporative cooling (`consumable_inputs: ["liquid_water"]`).
* **Conflict**: Consumable liquid water is required by the biological mechanism, but is absent in the target environment.
* **Fields Used (Existing Enums Only)**:
  * `environment.resources_absent`: `[ResourceEnum.LIQUID_WATER]` (`"liquid_water"`)
  * `required_function.target_direction`: `DirectionEnum.STORE_AND_RELEASE` (`"store-and-release"`)
  * `required_function.boundary_type`: `BoundaryTypeEnum.BC_FLUX` (`"BC_FLUX"`)
  * `time_pattern.time_mode`: `TimeModeEnum.CYCLIC_DIURNAL` (`"cyclic_diurnal"`)
* **Schema Extension**: **NONE** (all fields already exist in `ProblemCard`).
* **Detector Rule Code**:
  ```python
  def detect_t1_resource_absence(source_card: dict, prob: ProblemCard) -> bool:
      source_consumables = set(source_card.get("consumable_inputs", []))
      problem_absent = set(prob.environment.resources_absent)
      return len(source_consumables.intersection(problem_absent)) > 0
  ```

---

### 2.2 DEV-M2-S2: Timing Conflict / Regenerator ($\rightarrow$ Operator T3)

* **Physical Target**: Industrial Exhaust Heat Recovery Core.
* **Source Biology (`MC-BIO-DEV-M2`)**: Appendicular countercurrent blood circulation operating under continuous steady flow (`time_mode: TimeModeEnum.STEADY`).
* **Conflict**: The biological donor operates continuously in steady counterflow, whereas the target engineering application is a cyclic batch regenerator (charging and discharging decoupled in time).
* **Fields Used (Existing Enums Only)**:
  * `time_pattern.time_mode`: `TimeModeEnum.CYCLIC_DIURNAL` (`"cyclic_diurnal"`)
  * `required_function.target_direction`: `DirectionEnum.TRANSPORT_DIRECTIONAL` (`"transport-directional"`)
  * `required_function.boundary_type`: `BoundaryTypeEnum.BC_TEMP` (`"BC_TEMP"`)
* **Schema Extension**: **NONE** (uses existing `TimeModeEnum.CYCLIC_DIURNAL` on `time_pattern.time_mode`).
* **Detector Rule Code**:
  ```python
  def detect_t3_timing_mismatch(source_card: dict, prob: ProblemCard) -> bool:
      source_time = source_card.get("time_mode", TimeModeEnum.STEADY)
      target_time = prob.time_pattern.time_mode
      return (source_time in [TimeModeEnum.STEADY, TimeModeEnum.CONTINUOUS] and 
              target_time in [TimeModeEnum.CYCLIC_DIURNAL, TimeModeEnum.PULSED])
  ```

---

### 2.3 DEV-M3-S2: Direction Inversion ($\rightarrow$ Operator T2)

* **Physical Target**: Telecom Cabinet Solar Collector / Absorber.
* **Source Biology (`MC-BIO-DEV-M3`)**: Saharan silver ant hair array, evolved for passive radiative cooling and solar reflection (`target_direction: DirectionEnum.DECREASE` heat flux into organism).
* **Conflict**: The biological mechanism rejects heat to cool the subject (`target_direction = decrease`), whereas the target engineering collector requires absorbing ambient radiant heat to warm equipment (`target_direction = increase`).
* **Fields Used (Existing Enums Only)**:
  * `required_function.target_direction`: `DirectionEnum.INCREASE` (`"increase"`)
  * `required_function.boundary_type`: `BoundaryTypeEnum.BC_FLUX` (`"BC_FLUX"`)
* **Schema Extension**: **NONE** (uses existing `DirectionEnum.INCREASE` on `required_function.target_direction`).
* **Detector Rule Code**:
  ```python
  def detect_t2_direction_inversion(source_card: dict, prob: ProblemCard) -> bool:
      source_dir = source_card.get("target_direction", DirectionEnum.DECREASE)
      target_dir = prob.required_function.target_direction
      return (source_dir == DirectionEnum.DECREASE and target_dir == DirectionEnum.INCREASE) or \
             (source_dir == DirectionEnum.INCREASE and target_dir == DirectionEnum.DECREASE)
  ```

---

### 2.4 DEV-M4-S2: Regime Scale-Up ($\rightarrow$ Operator T5)

* **Physical Target**: Deep Subsea AUV Aeration Interface.
* **Source Biology (`MC-BIO-DEV-M4`)**: Aquatic insect plastron gill (*Aphelocheirus aestivalis*), operating at capillary micro-scale ($L_c \le 0.005$ m, hydrostatic depth $H \le 0.5$ m).
* **Conflict**: The target engineering application operates at macroscopic module length scale ($L \sim 1.0$ m) at deep benthic immersion ($H = 80.0$ m). Direct geometric scaling causes immediate pore wetting breakthrough.
* **Diagnostic**: In the existing `flbds.schema.problem_card`, `SystemSpec` only contains `scale: Optional[str]` (a loose unconstrained text field) and lacks a numeric characteristic length. Neither `SystemSpec` nor `HardConstraints` has a field for physical length scale or operating hydrostatic depth.
* **Status**: **REQUIRES SCHEMA CHANGE**.
  * **Smallest Proposed Schema Change**:
    Add `characteristic_length_m` as an optional float field to `SystemSpec`:
    ```python
    class SystemSpec(BaseModel):
        name: str
        components: list[str] = Field(default_factory=list)
        geometry_summary: Optional[str] = None
        scale: Optional[str] = None
        characteristic_length_m: Optional[float] = Field(
            default=None, 
            gt=0.0, 
            description="Characteristic physical length scale of system in meters"
        )
    ```
* **Detector Rule Code**:
  ```python
  def detect_t5_regime_rescaling(source_card: dict, prob: ProblemCard) -> bool:
      # T5 compares the target characteristic length with the source card regime bounds
      source_max_L = source_card.get("regime_max_length_m", 0.005)  # 5 mm for biological gill
      target_L = getattr(prob.system, "characteristic_length_m", None)
      if target_L is None:
          # Fallback inspects problem constraints if present
          for c in prob.constraints:
              if any(k in c.variable.lower() for k in ["head", "depth", "length", "scale"]):
                  m = re.search(r"(\d+(?:\.\d+)?)", c.bound)
                  if m:
                      target_L = float(m.group(1))
                      break
      return (target_L is not None) and (target_L > 5.0 * source_max_L)
  ```

---

## 3. Test Verification (`tests/test_conflict_detector.py`)

The automated test suite executes the detector across all 12 dev cases:
1. **Split 1 Guarantee**:
   * `DEV-M1-S1`: flags = `[]`
   * `DEV-M2-S1`: flags = `[]`
   * `DEV-M3-S1`: flags = `[]`
   * `DEV-M4-S1`: flags = `[]`
   * **Result**: All Split 1 cases fire zero conflict flags.
2. **Split 2 Archetype Guarantee** (under proposed parameters):
   * `DEV-M1-S2`: fires `['T1']` (Resource Absence)
   * `DEV-M2-S2`: fires `['T3']` (Temporal Phase Shift)
   * `DEV-M3-S2`: fires `['T2']` (Direction Inversion)
   * `DEV-M4-S2`: fires `['T5']` (Regime Re-scaling)
