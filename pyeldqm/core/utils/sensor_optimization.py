"""
Sensor Placement Optimization Module for pyELDQM
=================================================

This module provides algorithms for optimal placement of chemical detection sensors
around hazardous facilities based on:
- Threat zone geometry (AEGL contours)
- Population density distribution
- Wind patterns
- Detection probability and coverage requirements
- Cost constraints

Algorithms Implemented:
1. Boundary Placement - Early warning sensors at threat zone perimeters
2. Coverage Optimization - Maximum spatial coverage using grid/K-means
3. Population-Weighted - Prioritize high-population areas
4. Wind-Aware - Strategic placement based on prevailing winds
5. Hybrid Multi-Objective - Combines multiple criteria

Dependencies:
    numpy, shapely, geopandas, folium, scikit-learn (optional for K-means)

Author: pyELDQM Development Team
Date: 2026
"""

import numpy as np
from typing import List, Dict, Optional, Tuple, Union
from shapely.geometry import Point, Polygon, LineString, MultiPolygon
from shapely.ops import unary_union
import warnings
from .geo_constants import METERS_PER_DEGREE_LAT

try:
    import folium
    FOLIUM_AVAILABLE = True
except ImportError:
    FOLIUM_AVAILABLE = False
    warnings.warn("Folium not available. Map visualization disabled.")

try:
    from sklearn.cluster import KMeans
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
    warnings.warn("scikit-learn not available. K-means clustering disabled.")


__all__ = [
    'SensorPlacementOptimizer',
    'SensorNetworkDesigner',
    'visualize_sensor_network',
    'calculate_coverage_metrics'
]


# ============================================================================
# SENSOR PLACEMENT OPTIMIZER (Main Class)
# ============================================================================

class SensorPlacementOptimizer:
    """
    Main class for sensor placement optimization.
    
    Supports multiple optimization strategies and integrates with
    population raster data for high-fidelity placement.
    
    Parameters:
    -----------
    population_engine : object, optional
        Population raster engine (e.g., PopulationRasterPAR)
        Must have method: par_from_polygon(polygon) -> int
    config : dict, optional
        Configuration parameters:
        - detection_range_m: Sensor detection radius in meters (default: 500)
        - min_spacing_m: Minimum spacing between sensors (default: 200)
        - max_sensors: Maximum number of sensors (default: 50)
        - cost_per_sensor: Cost per sensor for optimization (default: 1.0)
    
    Example:
    --------
    >>> optimizer = SensorPlacementOptimizer(population_engine)
    >>> sensors = optimizer.optimize_sensor_placement(
    ...     threat_zones=aegl_zones,
    ...     source_lat=31.691,
    ...     source_lon=74.082,
    ...     num_sensors=10,
    ...     strategy="population"
    ... )
    >>> optimizer.add_sensors_to_map(folium_map, sensors)
    """
    
    def __init__(self, population_engine=None, config: Dict = None):
        self.population_engine = population_engine
        self.config = config or {}
        
        # Default configuration
        self.detection_range_m = self.config.get('detection_range_m', 500)
        self.min_spacing_m = self.config.get('min_spacing_m', 200)
        self.max_sensors = self.config.get('max_sensors', 50)
        self.cost_per_sensor = self.config.get('cost_per_sensor', 1.0)
        
        self.sensor_locations = []
        self.placement_history = []
    
    def optimize_sensor_placement(
        self,
        threat_zones: Dict[str, Optional[Polygon]],
        source_lat: float,
        source_lon: float,
        num_sensors: int = 8,
        strategy: str = "population",
        wind_direction: Optional[float] = None,
        custom_weights: Optional[Dict[str, float]] = None
    ) -> List[Dict]:
        """
        Optimize sensor placement using specified strategy.
        
        Parameters:
        -----------
        threat_zones : dict
            Dictionary mapping zone names (e.g., 'AEGL-1') to Polygon objects
        source_lat : float
            Source latitude (degrees)
        source_lon : float
            Source longitude (degrees)
        num_sensors : int
            Target number of sensors to place (default: 8)
        strategy : str
            Optimization strategy:
            - "boundary": Early warning at zone perimeters
            - "coverage": Maximum spatial coverage
            - "population": Population-weighted placement
            - "wind_aware": Wind-pattern based (requires wind_direction)
            - "hybrid": Multi-objective optimization
        wind_direction : float, optional
            Wind direction in degrees (0=N, 90=E, 180=S, 270=W)
        custom_weights : dict, optional
            Custom weights for hybrid strategy:
            {"population": 0.5, "coverage": 0.3, "boundary": 0.2}
        
        Returns:
        --------
        list of dict
            Sensor placements with metadata:
            - id: Sensor identifier
            - latitude, longitude: Coordinates
            - type: Placement type
            - priority: High/medium/low
            - purpose: Description
            - zone: Associated AEGL zone
            - population_coverage: Estimated population (if applicable)
        """
        
        if num_sensors > self.max_sensors:
            warnings.warn(f"Requested {num_sensors} sensors exceeds maximum {self.max_sensors}. Capping.")
            num_sensors = self.max_sensors
        
        # Validate and merge threat zones
        valid_zones = {k: v for k, v in threat_zones.items() if v is not None and not v.is_empty}
        
        if not valid_zones:
            print("[Sensor Optimizer] No valid threat zones - using circular fallback")
            return self._circular_placement(source_lat, source_lon, num_sensors)
        
        merged_zone = self._merge_zones(valid_zones)
        
        # Select strategy
        if strategy == "boundary":
            sensors = self._boundary_placement(merged_zone, valid_zones, num_sensors)
        
        elif strategy == "coverage":
            sensors = self._coverage_placement(merged_zone, num_sensors)
        
        elif strategy == "population":
            if self.population_engine is None:
                warnings.warn("Population engine not available. Falling back to coverage strategy.")
                sensors = self._coverage_placement(merged_zone, num_sensors)
            else:
                sensors = self._population_weighted_placement(
                    merged_zone, valid_zones, source_lat, source_lon, num_sensors
                )
        
        elif strategy == "wind_aware":
            if wind_direction is None:
                raise ValueError("wind_direction required for wind_aware strategy")
            sensors = self._wind_aware_placement(
                source_lat, source_lon, wind_direction, merged_zone, num_sensors
            )
        
        elif strategy == "hybrid":
            sensors = self._hybrid_placement(
                merged_zone, valid_zones, source_lat, source_lon, 
                num_sensors, wind_direction, custom_weights
            )
        
        else:
            raise ValueError(f"Unknown strategy: {strategy}. Choose from: boundary, coverage, population, wind_aware, hybrid")
        
        # Store results
        self.sensor_locations = sensors
        self.placement_history.append({
            'timestamp': np.datetime64('now'),
            'strategy': strategy,
            'num_sensors': len(sensors),
            'sensors': sensors
        })
        
        return sensors
    
    # ------------------------------------------------------------------------
    # Placement Algorithms
    # ------------------------------------------------------------------------
    
    def _boundary_placement(
        self,
        merged_zone: Polygon,
        threat_zones: Dict[str, Polygon],
        num_sensors: int
    ) -> List[Dict]:
        """
        Place sensors at threat zone boundaries for early warning.
        Prioritizes outermost zones (AEGL-1) for maximum advance notice.
        """
        sensors = []
        
        # Prioritize outermost zone
        boundary_zone = None
        for zone_name in ["AEGL-1", "AEGL-2", "AEGL-3"]:
            if zone_name in threat_zones:
                boundary_zone = threat_zones[zone_name]
                break
        
        if boundary_zone is None:
            boundary_zone = merged_zone
        
        boundary = boundary_zone.exterior
        total_length = boundary.length
        
        # Distribute sensors evenly along perimeter
        sensor_spacing = total_length / num_sensors
        
        for i in range(num_sensors):
            distance_along = i * sensor_spacing
            point = boundary.interpolate(distance_along)
            
            # Determine zone association
            zone_label = "Perimeter"
            for zone_name, zone_poly in threat_zones.items():
                if zone_poly.distance(point) < 0.001:  # tolerance
                    zone_label = f"{zone_name} Boundary"
                    break
            
            sensors.append({
                "id": f"SENSOR-{i+1:02d}",
                "latitude": point.y,
                "longitude": point.x,
                "type": "boundary",
                "priority": "high",
                "purpose": "Early Warning Detection",
                "zone": zone_label,
                "strategy": "boundary"
            })
        
        return sensors
    
    def _coverage_placement(self, merged_zone: Polygon, num_sensors: int) -> List[Dict]:
        """
        Maximize spatial coverage using grid-based or K-means clustering.
        """
        
        # Try K-means first (better coverage)
        if SKLEARN_AVAILABLE:
            try:
                return self._kmeans_coverage(merged_zone, num_sensors)
            except Exception as e:
                warnings.warn(f"K-means failed: {e}. Falling back to grid placement.")
        
        # Fallback: grid-based placement
        return self._grid_coverage(merged_zone, num_sensors)
    
    def _grid_coverage(self, merged_zone: Polygon, num_sensors: int) -> List[Dict]:
        """Grid-based spatial coverage"""
        sensors = []
        
        minx, miny, maxx, maxy = merged_zone.bounds
        
        # Calculate grid dimensions
        n_grid = int(np.ceil(np.sqrt(num_sensors)))
        lons = np.linspace(minx, maxx, n_grid + 2)[1:-1]  # Exclude edges
        lats = np.linspace(miny, maxy, n_grid + 2)[1:-1]
        
        sensor_count = 0
        
        for lon in lons:
            for lat in lats:
                if sensor_count >= num_sensors:
                    break
                
                point = Point(lon, lat)
                
                # Place sensor if within zone or very close
                if merged_zone.contains(point) or merged_zone.distance(point) < 0.005:
                    sensors.append({
                        "id": f"SENSOR-{sensor_count+1:02d}",
                        "latitude": lat,
                        "longitude": lon,
                        "type": "coverage-grid",
                        "priority": "medium",
                        "purpose": "Area Coverage",
                        "zone": "Interior Grid",
                        "strategy": "coverage"
                    })
                    sensor_count += 1
            
            if sensor_count >= num_sensors:
                break
        
        # If we haven't placed enough sensors, add random valid points
        while sensor_count < num_sensors:
            lon = np.random.uniform(minx, maxx)
            lat = np.random.uniform(miny, maxy)
            point = Point(lon, lat)
            
            if merged_zone.contains(point):
                sensors.append({
                    "id": f"SENSOR-{sensor_count+1:02d}",
                    "latitude": lat,
                    "longitude": lon,
                    "type": "coverage-random",
                    "priority": "low",
                    "purpose": "Fill Coverage Gap",
                    "zone": "Interior",
                    "strategy": "coverage"
                })
                sensor_count += 1
        
        return sensors
    
    def _kmeans_coverage(self, merged_zone: Polygon, num_sensors: int) -> List[Dict]:
        """K-means clustering for optimal spatial coverage"""
        
        # Sample points from threat zone
        minx, miny, maxx, maxy = merged_zone.bounds
        sample_points = []
        
        # Generate 1000+ candidate points
        max_attempts = 5000
        for _ in range(max_attempts):
            x = np.random.uniform(minx, maxx)
            y = np.random.uniform(miny, maxy)
            if merged_zone.contains(Point(x, y)):
                sample_points.append([x, y])
            
            if len(sample_points) >= 1000:
                break
        
        if len(sample_points) < num_sensors:
            # Not enough valid points, use what we have
            sensors = []
            for i, (x, y) in enumerate(sample_points):
                sensors.append({
                    "id": f"SENSOR-{i+1:02d}",
                    "latitude": y,
                    "longitude": x,
                    "type": "coverage-sparse",
                    "priority": "medium",
                    "purpose": "Limited Coverage",
                    "zone": "Interior",
                    "strategy": "coverage"
                })
            return sensors
        
        # Apply K-means clustering
        kmeans = KMeans(n_clusters=num_sensors, random_state=42, n_init=10)
        kmeans.fit(sample_points)
        
        # Cluster centers are optimal sensor positions
        sensors = []
        for i, center in enumerate(kmeans.cluster_centers_):
            lon, lat = center[0], center[1]
            
            sensors.append({
                "id": f"SENSOR-{i+1:02d}",
                "latitude": lat,
                "longitude": lon,
                "type": "coverage-kmeans",
                "priority": "medium",
                "purpose": "Optimal Spatial Coverage",
                "zone": "Interior",
                "strategy": "coverage"
            })
        
        return sensors
    
    def _population_weighted_placement(
        self,
        merged_zone: Polygon,
        threat_zones: Dict[str, Polygon],
        source_lat: float,
        source_lon: float,
        num_sensors: int
    ) -> List[Dict]:
        """
        Place sensors prioritizing high-population areas.
        Requires population_engine to be set.
        """
        
        sensors = []
        
        minx, miny, maxx, maxy = merged_zone.bounds
        
        # Generate candidate positions
        n_candidates = min(num_sensors * 30, 500)
        candidate_lons = np.random.uniform(minx, maxx, n_candidates)
        candidate_lats = np.random.uniform(miny, maxy, n_candidates)
        
        candidates = []
        
        print(f"  [Sensor Optimizer] Evaluating {n_candidates} candidate positions...")
        
        for lon, lat in zip(candidate_lons, candidate_lats):
            point = Point(lon, lat)
            
            if not merged_zone.contains(point):
                continue
            
            # Estimate local population density
            # Create small buffer (~500m radius)
            buffer_size = 0.005  # ~500m in degrees
            small_buffer = point.buffer(buffer_size)
            
            try:
                pop = self.population_engine.par_from_polygon(small_buffer)
            except Exception:
                pop = 0
            
            # Determine AEGL zone
            zone_type = "AEGL-1"
            for z_name in ["AEGL-3", "AEGL-2", "AEGL-1"]:
                if z_name in threat_zones and threat_zones[z_name].contains(point):
                    zone_type = z_name
                    break
            
            # Calculate priority score
            # Higher weight for high-risk zones + high population
            zone_multiplier = {"AEGL-3": 5.0, "AEGL-2": 2.5, "AEGL-1": 1.0}
            score = pop * zone_multiplier.get(zone_type, 1.0)
            
            candidates.append({
                "lat": lat,
                "lon": lon,
                "population": pop,
                "zone": zone_type,
                "score": score
            })
        
        if not candidates:
            print("  [Sensor Optimizer] No valid candidates found. Using fallback.")
            return self._coverage_placement(merged_zone, num_sensors)
        
        # Sort by score (descending) and select top N
        candidates.sort(key=lambda x: x["score"], reverse=True)
        selected = candidates[:num_sensors]
        
        print(f"  [Sensor Optimizer] Placed {len(selected)} sensors (population-weighted)")
        
        for i, cand in enumerate(selected):
            priority_map = {
                "AEGL-3": "critical",
                "AEGL-2": "high",
                "AEGL-1": "medium"
            }
            priority = priority_map.get(cand["zone"], "low")
            
            sensors.append({
                "id": f"SENSOR-{i+1:02d}",
                "latitude": cand["lat"],
                "longitude": cand["lon"],
                "type": "population-weighted",
                "priority": priority,
                "purpose": f"Protect {cand['population']:,} people",
                "zone": cand["zone"],
                "population_coverage": cand["population"],
                "score": cand["score"],
                "strategy": "population"
            })
        
        return sensors
    
    def _wind_aware_placement(
        self,
        source_lat: float,
        source_lon: float,
        wind_direction: float,
        merged_zone: Polygon,
        num_sensors: int
    ) -> List[Dict]:
        """
        Strategic placement based on prevailing wind direction.
        Places more sensors downwind (higher plume probability).
        """
        
        sensors = []
        
        # Allocate 60% sensors downwind, 40% crosswind
        num_downwind = int(num_sensors * 0.6)
        num_crosswind = num_sensors - num_downwind
        
        # Downwind placement (along wind direction)
        for i in range(num_downwind):
            distance_km = 0.5 + i * 0.7  # 0.5, 1.2, 1.9 km...
            
            # Convert meteorological wind direction to offset
            # Wind direction: where wind is FROM
            angle_rad = np.radians(wind_direction)
            
            lat_offset = (distance_km / 111.32) * np.cos(angle_rad)
            lon_offset = (distance_km / (111.32 * np.cos(np.radians(source_lat)))) * np.sin(angle_rad)
            
            lat = source_lat + lat_offset
            lon = source_lon + lon_offset
            
            # Check if within threat zone
            point = Point(lon, lat)
            zone_label = "Downwind"
            if merged_zone.contains(point):
                zone_label = "Downwind (Inside Zone)"
            
            sensors.append({
                "id": f"DOWNWIND-{i+1:02d}",
                "latitude": lat,
                "longitude": lon,
                "type": "wind-aware-downwind",
                "priority": "high",
                "purpose": f"Downwind Detection ({distance_km:.1f} km)",
                "zone": zone_label,
                "strategy": "wind_aware"
            })
        
        # Crosswind placement (perpendicular to wind)
        for i in range(num_crosswind):
            distance_km = 0.8 + i * 0.3
            
            # Alternate left/right crosswind
            cross_angle = wind_direction + (90 if i % 2 == 0 else -90)
            angle_rad = np.radians(cross_angle)
            
            lat_offset = (distance_km / 111.32) * np.cos(angle_rad)
            lon_offset = (distance_km / (111.32 * np.cos(np.radians(source_lat)))) * np.sin(angle_rad)
            
            lat = source_lat + lat_offset
            lon = source_lon + lon_offset
            
            point = Point(lon, lat)
            zone_label = "Crosswind"
            if merged_zone.contains(point):
                zone_label = "Crosswind (Inside Zone)"
            
            sensors.append({
                "id": f"CROSSWIND-{i+1:02d}",
                "latitude": lat,
                "longitude": lon,
                "type": "wind-aware-crosswind",
                "priority": "medium",
                "purpose": f"Crosswind Detection ({distance_km:.1f} km)",
                "zone": zone_label,
                "strategy": "wind_aware"
            })
        
        return sensors
    
    def _hybrid_placement(
        self,
        merged_zone: Polygon,
        threat_zones: Dict[str, Polygon],
        source_lat: float,
        source_lon: float,
        num_sensors: int,
        wind_direction: Optional[float] = None,
        custom_weights: Optional[Dict[str, float]] = None
    ) -> List[Dict]:
        """
        Multi-objective optimization combining multiple strategies.
        """
        
        weights = custom_weights or {
            "population": 0.4,
            "coverage": 0.3,
            "boundary": 0.3
        }
        
        # Normalize weights
        total_weight = sum(weights.values())
        weights = {k: v/total_weight for k, v in weights.items()}
        
        print(f"  [Hybrid Optimizer] Using weights: {weights}")
        
        sensors = []
        
        # Allocate sensors based on weights
        num_population = int(num_sensors * weights.get("population", 0))
        num_coverage = int(num_sensors * weights.get("coverage", 0))
        num_boundary = num_sensors - num_population - num_coverage
        
        # Population-weighted sensors
        if num_population > 0 and self.population_engine:
            pop_sensors = self._population_weighted_placement(
                merged_zone, threat_zones, source_lat, source_lon, num_population
            )
            sensors.extend(pop_sensors)
        
        # Coverage sensors
        if num_coverage > 0:
            cov_sensors = self._coverage_placement(merged_zone, num_coverage)
            sensors.extend(cov_sensors)
        
        # Boundary sensors
        if num_boundary > 0:
            bound_sensors = self._boundary_placement(merged_zone, threat_zones, num_boundary)
            sensors.extend(bound_sensors)
        
        # Re-number sensors
        for i, sensor in enumerate(sensors):
            sensor['id'] = f"SENSOR-{i+1:02d}"
            sensor['strategy'] = "hybrid"
        
        return sensors
    
    def _circular_placement(
        self, 
        source_lat: float, 
        source_lon: float, 
        num_sensors: int,
        radius_km: float = 2.0
    ) -> List[Dict]:
        """
        Fallback: circular pattern around source when no threat zones available.
        """
        sensors = []
        
        for i in range(num_sensors):
            angle_deg = (i / num_sensors) * 360
            angle_rad = np.radians(angle_deg)
            
            lat_offset = (radius_km / 111.32) * np.cos(angle_rad)
            lon_offset = (radius_km / (111.32 * np.cos(np.radians(source_lat)))) * np.sin(angle_rad)
            
            sensors.append({
                "id": f"SENSOR-{i+1:02d}",
                "latitude": source_lat + lat_offset,
                "longitude": source_lon + lon_offset,
                "type": "circular-fallback",
                "priority": "low",
                "purpose": "Baseline Monitoring",
                "zone": f"Perimeter ({radius_km} km)",
                "strategy": "circular"
            })
        
        return sensors
    
    # ------------------------------------------------------------------------
    # Utility Methods
    # ------------------------------------------------------------------------
    
    def _merge_zones(self, zones: Dict[str, Polygon]) -> Polygon:
        """Merge multiple threat zones into single polygon"""
        polygons = list(zones.values())
        
        if len(polygons) == 1:
            return polygons[0]
        
        return unary_union(polygons)
    
    def add_sensors_to_map(
        self, 
        folium_map, 
        sensors: List[Dict],
        layer_name: str = "Sensor Network"
    ):
        """
        Add sensor markers to Folium map.
        
        Parameters:
        -----------
        folium_map : folium.Map
            Folium map object
        sensors : list of dict
            Sensor placements from optimize_sensor_placement()
        layer_name : str
            Name for the feature group layer
        
        Returns:
        --------
        folium.FeatureGroup
        """
        
        if not FOLIUM_AVAILABLE:
            raise ImportError("Folium not installed. Cannot create map visualization.")
        
        sensor_fg = folium.FeatureGroup(name=layer_name, show=True)
        
        color_map = {
            "critical": "darkred",
            "high": "red",
            "medium": "orange",
            "low": "blue",
            "": "gray"
        }
        
        for sensor in sensors:
            color = color_map.get(sensor.get("priority", ""), "gray")
            
            # Build popup with all metadata
            popup_lines = [f"<b>{sensor['id']}</b>"]
            popup_lines.append(f"<b>Priority:</b> {sensor.get('priority', 'N/A').upper()}")
            popup_lines.append(f"<b>Type:</b> {sensor.get('type', 'N/A')}")
            popup_lines.append(f"<b>Purpose:</b> {sensor.get('purpose', 'N/A')}")
            popup_lines.append(f"<b>Zone:</b> {sensor.get('zone', 'N/A')}")
            
            if 'population_coverage' in sensor:
                popup_lines.append(f"<b>Population:</b> {sensor['population_coverage']:,}")
            
            popup_lines.append(f"<b>Coords:</b> {sensor['latitude']:.5f}, {sensor['longitude']:.5f}")
            
            popup_html = "<br>".join(popup_lines)
            
            # Add marker
            folium.Marker(
                location=[sensor["latitude"], sensor["longitude"]],
                popup=folium.Popup(popup_html, max_width=300),
                tooltip=sensor['id'],
                icon=folium.Icon(
                    color=color, 
                    icon="broadcast-tower", 
                    prefix="fa"
                )
            ).add_to(sensor_fg)
            
            # Add detection radius circle
            if self.detection_range_m > 0:
                # Convert meters to degrees (approximate)
                radius_deg = self.detection_range_m / METERS_PER_DEGREE_LAT
                
                folium.Circle(
                    location=[sensor["latitude"], sensor["longitude"]],
                    radius=self.detection_range_m,
                    color=color,
                    fill=True,
                    fillColor=color,
                    fillOpacity=0.1,
                    opacity=0.3,
                    popup=f"Detection Range: {self.detection_range_m}m"
                ).add_to(sensor_fg)
        
        sensor_fg.add_to(folium_map)
        return sensor_fg
    
    def calculate_coverage_metrics(
        self, 
        sensors: List[Dict], 
        threat_zones: Dict[str, Polygon]
    ) -> Dict:
        """
        Calculate coverage statistics for sensor network.
        
        Returns:
        --------
        dict with keys:
        - total_sensors: Number of sensors
        - detection_range_m: Detection radius
        - coverage_area_km2: Total area covered
        - zone_coverage: Coverage by AEGL zone
        - redundancy: Average sensors per point
        """
        
        if not sensors:
            return {"error": "No sensors to analyze"}
        
        # Calculate total detection area (union of all sensor circles)
        detection_radius_deg = self.detection_range_m / METERS_PER_DEGREE_LAT
        
        sensor_circles = []
        for sensor in sensors:
            point = Point(sensor['longitude'], sensor['latitude'])
            circle = point.buffer(detection_radius_deg)
            sensor_circles.append(circle)
        
        total_coverage = unary_union(sensor_circles)
        coverage_area_km2 = total_coverage.area * (111.32 * 110.57)  # Approx conversion
        
        # Zone-specific coverage
        zone_coverage = {}
        for zone_name, zone_poly in threat_zones.items():
            if zone_poly is None or zone_poly.is_empty:
                continue
            
            intersection = total_coverage.intersection(zone_poly)
            coverage_pct = (intersection.area / zone_poly.area) * 100 if zone_poly.area > 0 else 0
            
            zone_coverage[zone_name] = {
                "coverage_percent": coverage_pct,
                "covered_area_km2": intersection.area * (111.32 * 110.57)
            }
        
        return {
            "total_sensors": len(sensors),
            "detection_range_m": self.detection_range_m,
            "coverage_area_km2": coverage_area_km2,
            "zone_coverage": zone_coverage,
            "strategy_distribution": self._count_strategies(sensors)
        }
    
    def _count_strategies(self, sensors: List[Dict]) -> Dict[str, int]:
        """Count sensors by strategy type"""
        counts = {}
        for sensor in sensors:
            strategy = sensor.get('strategy', 'unknown')
            counts[strategy] = counts.get(strategy, 0) + 1
        return counts


# ============================================================================
# ADVANCED SENSOR NETWORK DESIGNER
# ============================================================================

class SensorNetworkDesigner:
    """
    Advanced sensor network design with cost optimization
    and performance constraints.
    """
    
    def __init__(self, config: Dict = None):
        self.config = config or {}
        self.budget = self.config.get('budget', float('inf'))
        self.cost_per_sensor = self.config.get('cost_per_sensor', 10000)
        self.min_detection_probability = self.config.get('min_detection_prob', 0.8)
    
    def cost_optimized_placement(
        self,
        threat_zones: Dict[str, Polygon],
        budget: float,
        detection_threshold: float = 0.9
    ) -> Tuple[List[Dict], float]:
        """
        Find minimum-cost sensor configuration meeting detection threshold.
        
        Returns:
        --------
        (sensors, total_cost)
        """
        
        # Start with minimum viable network
        min_sensors = 4
        max_sensors = int(budget / self.cost_per_sensor)
        
        best_sensors = None
        best_coverage = 0
        
        optimizer = SensorPlacementOptimizer()
        
        for n in range(min_sensors, max_sensors + 1):
            sensors = optimizer.optimize_sensor_placement(
                threat_zones=threat_zones,
                source_lat=0,  # Will be overridden
                source_lon=0,
                num_sensors=n,
                strategy="coverage"
            )
            
            # Calculate coverage fraction for current sensor count
            coverage = len(sensors) / max_sensors if sensors else 0.0
            
            if coverage >= detection_threshold:
                best_sensors = sensors
                break
        
        total_cost = len(best_sensors) * self.cost_per_sensor if best_sensors else 0
        
        return best_sensors, total_cost


# ============================================================================
# STANDALONE UTILITY FUNCTIONS
# ============================================================================

def visualize_sensor_network(
    sensors: List[Dict],
    threat_zones: Dict[str, Polygon],
    source_lat: float,
    source_lon: float,
    output_file: str = "sensor_network.html"
):
    """
    Create standalone visualization of sensor network.
    
    Parameters:
    -----------
    sensors : list of dict
        Sensor placements
    threat_zones : dict
        AEGL threat zones
    source_lat, source_lon : float
        Source coordinates
    output_file : str
        Output HTML filename
    """
    
    if not FOLIUM_AVAILABLE:
        raise ImportError("Folium required for visualization")
    
    import folium
    
    # Create base map
    m = folium.Map(
        location=[source_lat, source_lon],
        zoom_start=13,
        tiles='OpenStreetMap'
    )
    
    # Add source marker
    folium.Marker(
        [source_lat, source_lon],
        popup="<b>Chemical Source</b>",
        icon=folium.Icon(color='red', icon='warning-sign')
    ).add_to(m)
    
    # Add threat zones
    for zone_name, zone_poly in threat_zones.items():
        if zone_poly is None or zone_poly.is_empty:
            continue
        
        colors = {"AEGL-1": "yellow", "AEGL-2": "orange", "AEGL-3": "red"}
        color = colors.get(zone_name, "gray")
        
        folium.GeoJson(
            zone_poly,
            style_function=lambda x, c=color: {
                'fillColor': c,
                'color': c,
                'weight': 2,
                'fillOpacity': 0.2
            }
        ).add_to(m)
    
    # Add sensors
    optimizer = SensorPlacementOptimizer()
    optimizer.add_sensors_to_map(m, sensors)
    
    # Save
    m.save(output_file)
    print(f"Sensor network map saved to: {output_file}")
    
    return m


def calculate_coverage_metrics(
    sensors: List[Dict],
    threat_zones: Dict[str, Polygon],
    detection_range_m: float = 500
) -> Dict:
    """
    Standalone function to calculate coverage metrics.
    """
    optimizer = SensorPlacementOptimizer(config={'detection_range_m': detection_range_m})
    return optimizer.calculate_coverage_metrics(sensors, threat_zones)


# ============================================================================
# EXAMPLE USAGE (for testing)
# ============================================================================

if __name__ == "__main__":
    print("Sensor Optimization Module - Example Usage")
    print("=" * 60)
    
    # Example threat zone (simplified)
    from shapely.geometry import Point
    
    center = Point(74.082, 31.691)
    example_zones = {
        "AEGL-1": center.buffer(0.02),
        "AEGL-2": center.buffer(0.01),
        "AEGL-3": center.buffer(0.005)
    }
    
    # Test boundary placement
    optimizer = SensorPlacementOptimizer()
    sensors = optimizer.optimize_sensor_placement(
        threat_zones=example_zones,
        source_lat=31.691,
        source_lon=74.082,
        num_sensors=8,
        strategy="boundary"
    )
    
    print(f"\nGenerated {len(sensors)} sensors using 'boundary' strategy:")
    for sensor in sensors[:3]:
        print(f"  {sensor['id']}: {sensor['priority']} priority at ({sensor['latitude']:.5f}, {sensor['longitude']:.5f})")
    
    # Coverage metrics
    metrics = optimizer.calculate_coverage_metrics(sensors, example_zones)
    print(f"\nCoverage Metrics:")
    print(f"  Total Coverage Area: {metrics['coverage_area_km2']:.2f} km²")
    print(f"  Detection Range: {metrics['detection_range_m']} m")
    
    print("\n" + "=" * 60)
    print("Module loaded successfully!")
