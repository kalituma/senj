from typing import TYPE_CHECKING
from tqdm import tqdm
from osgeo import ogr
from osgeo import gdal
from pathlib import Path
if TYPE_CHECKING:
    from osgeo.ogr import Layer, FieldDefn

def get_vector_envelope(vector_layer: "Layer") -> tuple[float, float, float, float, float, float, float, float]:
    minx, maxx, miny, maxy = vector_layer.GetExtent()
    ulx, uly, urx, ury, lrx, lry, llx, lly = minx, maxy, maxx, maxy, maxx, miny, minx, miny
    return ulx, uly, urx, ury, lrx, lry, llx, lly

def create_envelope(ulx, uly, urx, ury, lrx, lry, llx, lly) -> ogr.Geometry:

    envelope = ogr.Geometry(ogr.wkbLinearRing)
    envelope.AddPoint(ulx, uly)
    envelope.AddPoint(urx, ury)
    envelope.AddPoint(lrx, lry)
    envelope.AddPoint(llx, lly)
    envelope.AddPoint(ulx, uly)

    env_geom = ogr.Geometry(ogr.wkbPolygon)
    env_geom.AddGeometry(envelope)

    return env_geom

def clip_vector(input_ds, clip_geom, out_ds):

    file_stem = Path(input_ds.GetFileList()[0]).stem
    
    in_layer = input_ds.GetLayer()
        
    out_layer = out_ds.GetLayer()
    out_defn = out_layer.GetLayerDefn()
    
    in_layer.ResetReading()
    for in_feat in tqdm(in_layer, desc=f"Clipping features for '{file_stem}'"):
        geom = in_feat.GetGeometryRef()
        clipped_geom = geom.Intersection(clip_geom)
        
        if clipped_geom and not clipped_geom.IsEmpty():
            out_feat = ogr.Feature(out_defn)
            out_feat.SetGeometry(clipped_geom)
            
            for i in range(out_defn.GetFieldCount()):
                out_feat.SetField(i, in_feat.GetField(i))
            
            out_layer.CreateFeature(out_feat)
            out_feat = None

    return out_ds

def get_vector_fields(vector_layer: "Layer") -> list["FieldDefn"]:
    fields = []
    layer_defn = vector_layer.GetLayerDefn()
    for i in range(layer_defn.GetFieldCount()):
        field_defn = layer_defn.GetFieldDefn(i)
        fields.append(field_defn)
    return fields