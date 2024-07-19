
def region_to_wkt(region): # region: [ul_x, ul_y, lr_x, lr_y]
    return f'POLYGON(({region[0]} {region[1]}, {region[2]} {region[1]}, {region[2]} {region[3]}, {region[0]} {region[3]}, {region[0]} {region[1]}))'