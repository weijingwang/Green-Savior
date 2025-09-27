# performance.py - Simplified LOD system
class PerformanceManager:
    """Manages Level of Detail (LOD) for performance optimization"""
    
    LOD_THRESHOLDS = [
        (1.0, "Mouse Size", -1, 1),      # zoom, name, max_segments, physics_skip
        (0.2, "Human Size", 100, 1),
        (0.1, "Room Size", 80, 1),
        (0.05, "House Size", 60, 2),
        (0.02, "Building Size", 40, 3),
        (0.01, "Block Size", 25, 5),
        (0.005, "District Size", 15, 8),
        (0.002, "City Size", 10, 12),
        (0.001, "Skyscraper Size", 6, 20)
    ]
    
    def __init__(self):
        self.physics_frame_counter = 0
    
    def get_lod_settings(self, zoom_factor):
        """Get appropriate LOD settings for current zoom level"""
        for threshold, name, segments, skip in self.LOD_THRESHOLDS:
            if zoom_factor >= threshold:
                return {
                    'name': name,
                    'max_segments': segments,
                    'physics_skip': skip
                }
        return self.LOD_THRESHOLDS[-1][1:]  # Return lowest LOD
    
    def should_update_physics(self, zoom_factor):
        """Determine if physics should update this frame"""
        self.physics_frame_counter += 1
        lod = self.get_lod_settings(zoom_factor)
        return self.physics_frame_counter % lod['physics_skip'] == 0