from abc import ABC, abstractmethod
from typing import Dict, List

class VectorHandler(ABC):
    
    @abstractmethod
    def get_features(self, raw) -> Dict:
        pass
    
    @abstractmethod
    def get_envelope(self, raw) -> tuple:
        pass

    @abstractmethod
    def proj(self, raw):
        pass

class GdalVectorHandler(VectorHandler):
    def get_features(self, raw) -> Dict:
        features = {}
        for layer_idx in range(raw.GetLayerCount()):
            layer = raw.GetLayerByIndex(layer_idx)
            layer_name = layer.GetName()
            
            features[layer_name] = []
            layer.ResetReading()
            
            for feature in layer:
                feature_dict = {
                    'id': feature.GetFID(),
                    'geometry': feature.GetGeometryRef().ExportToWkt(),
                    'attributes': {}
                }
                
                for i in range(feature.GetFieldCount()):
                    field_name = feature.GetFieldDefnRef(i).GetName()
                    feature_dict['attributes'][field_name] = feature.GetField(i)
                
                features[layer_name].append(feature_dict)
                
        return features
    
    def get_envelope(self, raw) -> tuple:
        if raw.GetLayerCount() == 0:
            return None
            
        layer = raw.GetLayerByIndex(0)
        minx, maxx, miny, maxy = layer.GetExtent()
        
        for i in range(1, raw.GetLayerCount()):
            layer = raw.GetLayerByIndex(i)
            ext = layer.GetExtent()
            minx = min(minx, ext[0])
            maxx = max(maxx, ext[1])
            miny = min(miny, ext[2])
            maxy = max(maxy, ext[3])
            
        return (minx, miny, maxx, maxy)
    
    def proj(self, raw) -> str:
        if raw.GetLayerCount() == 0:
            return None
            
        layer = raw.GetLayerByIndex(0)
        spatial_ref = layer.GetSpatialRef()
        if spatial_ref:
            return spatial_ref.ExportToWkt()
        return None