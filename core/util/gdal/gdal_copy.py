from tqdm import tqdm
from osgeo import ogr
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from osgeo.ogr import Feature, Layer, DataSource

def copy_features(layer: "Layer", from_layer: "Layer"):
    layer_defn = from_layer.GetLayerDefn()

    for feature in tqdm(from_layer, desc="Copying features"):
        new_feature = ogr.Feature(layer_defn)
        for i in range(feature.GetFieldCount()):
            new_feature.SetField(i, feature.GetField(i))
        new_feature.SetGeometry(feature.GetGeometryRef().Clone())
        layer.CreateFeature(new_feature)
        new_feature = None

    return layer

def copy_layer(data_source: "DataSource", from_data_source: "DataSource"):
    for i in tqdm(range(from_data_source.GetLayerCount()), desc="Copying layers"):
        from_layer = from_data_source.GetLayerByIndex(i)
        out_layer = data_source.CreateLayer(from_layer.GetName(), 
                                from_layer.GetSpatialRef(), 
                                from_layer.GetGeomType())
        
        layer_defn = from_layer.GetLayerDefn()
        for i in range(layer_defn.GetFieldCount()):
            field_defn = layer_defn.GetFieldDefn(i)
            out_layer.CreateField(field_defn)
    
    return data_source