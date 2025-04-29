from abc import ABC, abstractmethod
from typing import Dict, List, TYPE_CHECKING
from osgeo import osr, ogr


from core.util.gdal.gdal_vector import get_vector_envelope, create_envelope, get_vector_fields
from core.util.gdal import create_ds, create_datasource

if TYPE_CHECKING:
    from osgeo.ogr import Geometry
    from osgeo.gdal import Dataset
    from core.vector.vector import Vector
    from core.util import ModuleType
    from osgeo.ogr import Feature, Layer, DataSource

class VectorHandler(ABC):
        
    @abstractmethod
    def get_features(self, raw) -> Dict:
        pass
    
    @abstractmethod
    def get_envelope_geom(self, raw) -> "Geometry":
        pass

    @abstractmethod
    def bounds(self, raw) -> tuple[float, float, float, float]:
        pass

    @abstractmethod
    def proj(self, raw):
        pass
    
    @abstractmethod
    def empty_raw(self, raw):
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
    
    def bounds(self, raw: "Dataset") -> tuple[float, float, float, float]:
        layer = raw.GetLayerByIndex(0)
        ulx, uly, _, _, lrx, lry, _, _ = get_vector_envelope(layer)
        return ulx, uly, lrx, lry
        
    def proj(self, raw:"Dataset") -> str:
        if raw.GetLayerCount() == 0:
            return None
            
        layer = raw.GetLayerByIndex(0)
        spatial_ref = layer.GetSpatialRef()
        if spatial_ref:
            return spatial_ref.ExportToWkt()
        return None

    def get_envelope_geom(self, raw: "Dataset") -> "Geometry":
        ulx, uly, urx, ury, lrx, lry, llx, lly = get_vector_envelope(raw.GetLayerByIndex(0))
        env_polygon = create_envelope(ulx, uly, urx, ury, lrx, lry, llx, lly)
        srs = raw.GetLayerByIndex(0).GetSpatialRef()
        env_polygon.AssignSpatialReference(srs)

        return env_polygon
    

    def get_fields(self, raw:"Dataset") -> List[str]:
        layer = raw.GetLayerByIndex(0)
        fields = []
        layer_defn = layer.GetLayerDefn()
        for i in range(layer_defn.GetFieldCount()):
            field_defn = layer_defn.GetFieldDefn(i)
            fields.append(field_defn.GetName())
        return fields

    def empty_raw(self, raw) -> "Dataset":
        
        in_layer = raw.GetLayerByIndex(0)        
        fields = get_vector_fields(in_layer)
        geom_type = in_layer.GetGeomType()
        proj_wkt = in_layer.GetSpatialRef().ExportToWkt()
        new_raw = create_ds(gdal_format="Memory", is_vector=True, field_defs=fields, geom_type=geom_type, proj_wkt=proj_wkt)

        return new_raw
    
    def shape_raw(self, path: str) -> "DataSource":
        new_raw = create_datasource(path=path)        
        return new_raw
    


    # def merge(self, raw_list: List["Dataset"]) -> "Dataset":
    #     from osgeo import ogr
        
    #     mem_driver = ogr.GetDriverByName('Memory')
    #     merged_ds = mem_driver.CreateDataSource('merged')
        
    #     ref_layer = raw_list[0].GetLayer()
        
    #     srs = ref_layer.GetSpatialRef()
    #     geom_type = ref_layer.GetGeomType()
    #     merged_layer = merged_ds.CreateLayer('merged', srs, geom_type)

    #     layer_defn = ref_layer.GetLayerDefn()
    #     for i in range(layer_defn.GetFieldCount()):
    #         field_defn = layer_defn.GetFieldDefn(i)
    #         merged_layer.CreateField(field_defn)

    #     for raw in raw_list:
    #         layer = raw.GetLayer()
    #         for feature in layer:
    #             new_feature = ogr.Feature(merged_layer.GetLayerDefn())
    #             for i in range(layer_defn.GetFieldCount()):
    #                 new_feature.SetField(i, feature.GetField(i))
    #             new_feature.SetGeometry(feature.GetGeometryRef().Clone())
    #             merged_layer.CreateFeature(new_feature)
    #             new_feature = None

    #     return merged_ds