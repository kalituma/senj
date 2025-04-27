from osgeo import ogr

def get_envelope_coords(raw) -> tuple[float, float, float, float, float, float, float, float]:
    gt = raw.GetGeoTransform()
    cols = raw.RasterXSize
    rows = raw.RasterYSize

    ulx, uly = gt[0], gt[3]
    urx, ury = gt[0] + cols * gt[1], gt[3] + cols * gt[2] 
    lrx, lry = gt[0] + cols * gt[1] + rows * gt[4], gt[3] + cols * gt[2] + rows * gt[5]
    llx, lly = gt[0] + rows * gt[4], gt[3] + rows * gt[5]

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
    
    in_layer = input_ds.GetLayer()
        
    out_layer = out_ds.CreateLayer('clipped',
                                  in_layer.GetSpatialRef(),
                                  in_layer.GetGeomType())
        
    in_layer_defn = in_layer.GetLayerDefn()
    for i in range(in_layer_defn.GetFieldCount()):
        out_layer.CreateField(in_layer_defn.GetFieldDefn(i))
    
    out_defn = out_layer.GetLayerDefn()
    
    in_layer.ResetReading()
    for in_feat in in_layer:
        geom = in_feat.GetGeometryRef()
        clipped_geom = geom.Intersection(clip_geom)
        
        if clipped_geom and not clipped_geom.IsEmpty():
            out_feat = ogr.Feature(out_defn)
            out_feat.SetGeometry(clipped_geom)
            
            for i in range(in_layer_defn.GetFieldCount()):
                out_feat.SetField(i, in_feat.GetField(i))
            
            out_layer.CreateFeature(out_feat)
            out_feat = None

    return out_ds