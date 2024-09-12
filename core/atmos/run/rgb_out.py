import os, copy
import numpy as np

import matplotlib as plot

import matplotlib.pyplot as plt
import matplotlib.patheffects as pe
from mpl_toolkits.axes_grid1 import make_axes_locatable

from PIL import Image

import core.atmos as atmos
from core.util import Logger

def create_map(im, lon, lat, scene_mask, rgb_used, font, title_base:str, cpar, pscale, points, xsb, ysb, xsbl, ysbl, sclabel,
               user_settings:dict, out_dir:str, out_file_stem:str, ro_type:str):

    def _load_params():
        default_colormap = user_settings['map_default_colormap']
        auto_range = user_settings['map_auto_range']
        auto_range_percentiles = user_settings['map_auto_range_percentiles']
        fill_color = user_settings['map_fill_color']
        fill_outrange = user_settings['map_fill_outrange']
        title_rgb_wavelengths = user_settings['map_title_rgb_wavelengths']
        map_raster = user_settings['map_raster']
        pcolormesh = user_settings['map_pcolormesh']
        xtick_rotation = user_settings['map_xtick_rotation']
        ytick_rotation = user_settings['map_ytick_rotation']
        fontsize = user_settings['map_fontsize']
        gridline_color = user_settings['map_gridline_color']
        title_exists = user_settings['map_title']
        scalebar = user_settings['map_scalebar']
        scalebar_color = user_settings['map_scalebar_color']
        colorbar = user_settings['map_colorbar']
        colorbar_orientation = user_settings['map_colorbar_orientation']
        dpi = user_settings['map_dpi']

        return default_colormap, auto_range, auto_range_percentiles, fill_color, fill_outrange, title_rgb_wavelengths, map_raster, pcolormesh, \
            xtick_rotation, ytick_rotation, fontsize, gridline_color, title_exists, scalebar, scalebar_color, colorbar, colorbar_orientation, dpi

    default_colormap, auto_range, auto_range_percentiles, fill_color, fill_outrange, title_rgb_wavelengths, map_raster, pcolormesh, \
        xtick_rotation, ytick_rotation, fontsize, gridline_color, title_exists, scalebar, scalebar_color, colorbar, colorbar_orientation, dpi = _load_params()

    rgb = len(im.shape) > 2
    norm, cmap = None, None

    ## find out parameter scaling to use
    if not rgb:
        ## get parameter config
        cparl = ro_type.lower()
        sp = cparl.split('_')
        wave = None
        if (f'{"_".join(sp[0:-1])}_*' in pscale) and (cparl not in pscale):
            pard = {k: pscale[f'{"_".join(sp[0:-1])}_*'][k] for k in pscale[f'{"_".join(sp[0:-1])}_*']}
            wave = sp[-1]
        elif (f'{sp[0]}_*' in pscale) and (cparl not in pscale):
            pard = {k: pscale[f'{sp[0]}_*'][k] for k in pscale[f'{sp[0]}_*']}
            wave = sp[-1]
        elif cparl in pscale:
            pard = {k: pscale[cparl][k] for k in pscale[cparl]}
        else:
            pard = {'log': False, 'name': cpar, 'unit': ''}
            pard['cmap'] = default_colormap  # 'Planck_Parchment_RGB'
        ## do auto ranging
        if auto_range or ('min' not in pard) or ('max' not in pard):
            drange = np.nanpercentile(im, auto_range_percentiles)
            pard['min'] = drange[0]
            pard['max'] = drange[1]

        ## parameter name and title
        part = f'{pard["name"]}{"" if wave is None else f" {wave} nm"} [{pard["unit"]}]'

        if pard['cmap'] == 'default':
            pard['cmap'] = default_colormap

        ctfile = f'{atmos.config["data_dir"]}/{"Shared/ColourTables"}/{pard["cmap"]}.txt'
        if os.path.exists(ctfile):
            pard['cmap'] = plot.colors.ListedColormap(np.loadtxt(ctfile) / 255.)
        else:
            try:
                cmap = copy.copy(plot.cm.get_cmap(pard['cmap']))
            except:
                pard['cmap'] = default_colormap

        ## copy colour map to not set bad/under globally
        cmap = copy.copy(plot.cm.get_cmap(pard['cmap']))
        cmap.set_bad(fill_color)
        if fill_outrange:
            cmap.set_under(fill_color)

        ## do log scaling
        if pard['log']:
            im = np.log10(im)
            pard['min'] = np.log10(pard['min'])
            pard['max'] = np.log10(pard['max'])
            part = f'log10 {part}'

        ## normalisation
        norm = plot.colors.Normalize(vmin=pard['min'], vmax=pard['max'])  # , clip=setu['map_fill_outrange'])
    else:
        part = rf'$\rho_{ro_type[-1]}$ RGB'
        if title_rgb_wavelengths:
            part += f' ({", ".join([f"{w:.0f} nm" for w in rgb_used])})'

    ## title and outputfile
    title = f'{title_base}\n{part}'
    ofile = f'{out_dir}/{out_file_stem}_{ro_type}.png'

    ## raster 1:1 pixel outputs
    if map_raster:
        if not rgb:
            ## scale to 255 int
            im = atmos.shared.datascl(im, dmin=pard['min'], dmax=pard['max'])
            ## look up in colormap and convert to uint
            im = cmap.__call__(im)[:, :, 0:3] * 255
            im = im.astype(np.uint8)
        else:
            ## fix for new RGB scaling methods
            im *= 255
            im = im.astype(np.uint8)

        img = Image.fromarray(im)
        img.save(ofile)

    ## matplotlib outputs
    else:
        # imratio, figsize = get_imratio(im)
        figsize = None
        fig = plt.figure(figsize=figsize)
        ax = fig.add_subplot(1, 1, 1)
        plt.sca(ax)

        if pcolormesh:
            if rgb:  ## convert rgb values to color tuple before mapping
                if plot.__version__ > '3.7.0':
                    axim = plt.pcolormesh(lon, lat, im, shading='auto')
                else:
                    mesh_rgb = im[:, :, :]
                    colorTuple = mesh_rgb.reshape((mesh_rgb.shape[0] * mesh_rgb.shape[1]), 3)
                    colorTuple = np.insert(colorTuple, 3, 1.0, axis=1)
                    axim = plt.pcolormesh(lon, lat, im[:, :, 0], color=colorTuple, shading='auto')
            else:
                axim = plt.pcolormesh(lon, lat, im, norm=norm, cmap=cmap, shading='auto')
                if scene_mask is not None:
                    plt.pcolormesh(lon, lat, scene_mask, cmap='gray', vmin=0, vmax=1)

            plt.xlabel('Longitude (°E)', **font)
            plt.ylabel('Latitude (°N)', **font)

            plt.xticks(**font)
            plt.yticks(**font)

            ## rotate tick labels
            plt.xticks(rotation=xtick_rotation)
            plt.yticks(rotation=ytick_rotation)

        else:
            axim = plt.imshow(im, norm=norm, cmap=cmap)
            if scene_mask is not None:
                plt.imshow(scene_mask, cmap='gray', vmin=0, vmax=1)

            plt.axis('off')


        if title_exists:
            plt.title(title, **font)

        # ## add point markers
        if points is not None:
            for pname in points:
                if 'px' not in points[pname]: continue
                p = points[pname]
                if 'facecolor' in p:
                    mfc = p['facecolor']
                    mew = 1.5
                else:
                    mfc = None
                    mew = None
                if 'edgecolor' in p:
                    mec = p['edgecolor']
                else:
                    mec = None
                if 'fontsize' in p:
                    fontsize = p['fontsize']
                else:
                    fontsize = None
                if 'markersize' in p:
                    markersize = p['markersize']
                else:
                    markersize = None
                ## plot marker
                pplot = plt.plot(p['px'], p['py'], color=p['color'],
                                 marker=p['sym'], zorder=10,
                                 markersize=markersize, mec=mec, mfc=mfc, mew=mew)
                ## plot marker label
                if p['label_plot']:
                    plt.text(p['pxl'], p['pyl'], p['label'], color='white', fontsize=fontsize, zorder=10,
                             path_effects=[pe.withStroke(linewidth=2, foreground=p['color'])],
                             verticalalignment=points[pname]['va'], horizontalalignment=points[pname]['ha'])
        ## end add point markers

        ## add the scalebar
        if scalebar:
            plt.plot(xsb, ysb, '-', linewidth=2, color=scalebar_color, zorder=10)
            ## add the label
            plt.text(xsbl, ysbl, sclabel, color=scalebar_color, zorder=11,
                     horizontalalignment='center', fontsize=fontsize)
        ## end scalebar

        ## color bars
        cbar = None
        if colorbar:
            if colorbar_orientation == 'vertical':
                divider = make_axes_locatable(ax)
                cax = divider.append_axes('right', size='5%', pad=0.05)

                cbar = fig.colorbar(axim, cax=cax, orientation='vertical')
                cbar.ax.set_ylabel(part)
            else:
                divider = make_axes_locatable(ax)
                cax = divider.append_axes('bottom', size='5%', pad=0.05)

                cbar = fig.colorbar(axim, cax=cax, orientation='horizontal')
                cbar.ax.set_xlabel(part)

        # plt.tight_layout()

        ## we also make a colorbar for RGB, to keep map extents the same
        ## delete it here
        if rgb:
            if cbar is not None:
                # cbar.solids.set_edgecolor("w")
                # cbar.outline.set_visible(False)
                # cbar.set_ticks([])
                cbar.ax._visible = False

        plt.savefig(ofile, dpi=dpi, bbox_inches='tight', facecolor='white')
            # if setu['verbosity'] > 1:
        Logger.get_logger().log('info', 'Wrote {}'.format(ofile))
        plt.close()

def write_map(band_dict:dict, out_settings:dict, out_file_stem:str, out_dir:str, global_attrs:dict=None, plot_datasets:list[str]=[]):

    user_settings = atmos.setting.parse(global_attrs['sensor'], settings=atmos.settings['run'])

    if out_settings:
        for k in out_settings: user_settings[k] = out_settings[k]

    def _load_params():
        fontname = user_settings['map_fontname']
        fontsize = user_settings['map_fontsize']
        map_mask = user_settings['map_mask']
        flag_exponent_outofscene = user_settings['flag_exponent_outofscene']
        usetex = user_settings['map_usetex']
        pcolormesh = user_settings['map_pcolormesh']
        points = user_settings['map_points']
        scalebar = user_settings['map_scalebar']
        scalebar_position = user_settings['map_scalebar_position']
        scalebar_length = user_settings['map_scalebar_length']
        scalebar_max_fraction = user_settings['map_scalebar_max_fraction']

        red_wl = user_settings['rgb_red_wl']
        green_wl = user_settings['rgb_green_wl']
        blue_wl = user_settings['rgb_blue_wl']
        add_band_name = user_settings['add_band_name']
        rgb_autoscale = user_settings['rgb_autoscale']
        rgb_autoscale_percentiles = user_settings['rgb_autoscale_percentiles']
        rgb_min = user_settings['rgb_min']
        rgb_max = user_settings['rgb_max']
        rgb_gamma = user_settings['rgb_gamma']
        rgb_stretch = user_settings['rgb_stretch']

        return fontname, fontsize, map_mask, flag_exponent_outofscene, usetex, pcolormesh, points, scalebar, scalebar_position, scalebar_length, \
            scalebar_max_fraction, red_wl, green_wl, blue_wl, add_band_name, rgb_autoscale, rgb_autoscale_percentiles, rgb_min, rgb_max, rgb_gamma, rgb_stretch

    fontname, fontsize, map_mask, flag_exponent_outofscene, usetex, pcolormesh, points, scalebar, scalebar_position, scalebar_length, \
        scalebar_max_fraction, red_wl, green_wl, blue_wl, add_band_name, rgb_autoscale, rgb_autoscale_percentiles, rgb_min, rgb_max, rgb_gamma, rgb_stretch = _load_params()

    ## set font settings
    font = {'fontname': fontname, 'fontsize': fontsize}
    plot.rc('text', usetex=usetex)

    scene_mask = None
    if ('l2_flags' in band_dict) and (map_mask):
        scene_mask = band_dict['l2_flags']
        ## convert scene mask to int if it is not (e.g. after reprojection)
        if scene_mask.dtype not in [np.int16, np.int32]: scene_mask = scene_mask.astype(int)
        scene_mask = (scene_mask & (2 ** flag_exponent_outofscene))
        scene_mask[scene_mask != (2 ** flag_exponent_outofscene)] = 0  # np.nan
        scene_mask[scene_mask == (2 ** flag_exponent_outofscene)] = 1
        scene_mask = scene_mask.astype(np.float32)
        scene_mask[scene_mask == 0] = np.nan

    ## load parameter configuration
    pscale = atmos.atmosp.parameter_scaling()
    pslot_name_map = {v['att']['parameter']:k for k, v in band_dict['bands'].items()}

    isodate = ''
    if 'isodate' in global_attrs:
        isodate = global_attrs['isodate']
    elif 'time_coverage_end' in global_attrs:
        isodate = global_attrs['time_coverage_end']
    elif 'time_coverage_start' in global_attrs:
        isodate = global_attrs['time_coverage_start']

    if 'satellite_sensor' in global_attrs:
        title_base = f"{global_attrs['satellite_sensor'].replace('_', '/')} {isodate.replace('T', ' ')[0:19]}"
    else:
        title_base = f"{global_attrs['sensor'].replace('_', '/')} {isodate.replace('T', ' ')[0:19]}"


    ## parameters to plot
    plot_parameters = [k for k in pslot_name_map if k in plot_datasets]
    for k in user_settings:
        if k[0:7] != 'rgb_rho': continue
        if user_settings[k]: plot_parameters+=[k]

    if len(plot_parameters) == 0: return

    lon = None
    lat = None
    ## load lat and lon
    if pcolormesh or (points is not None) or scalebar:
        lon = band_dict['lon']
        lat = band_dict['lat']
        ## find region mid point
        mid = int(lat.shape[0] / 2), int(lat.shape[1] / 2)
        ## find lon and lat ranges (at mid point)
        lonw, lone = lon[mid[0], 0], lon[mid[0], -1]
        latn, lats = lat[0, mid[1]], lat[-1, mid[1]]
        lonr, latr = lone - lonw, latn - lats
        ## compute distance in one degree at mid point latitude
        lond, latd = atmos.shared.distance_in_ll(lat=lat[mid[0], mid[1]])
        dd = lond * abs(lone - lonw)


    ## prepare scale bar
    ## approximate distance in one degree of longitude
    xsb, ysb, xsbl, ysbl, sclabel = None, None, None, None, None
    if scalebar:
        scale_pos = scalebar_position
        if scalebar_position not in ['UR', 'UL', 'LL', 'LR']:
            Logger.get_logger().log('info', 'Map scalebar position {} not recognised.')
            Logger.get_logger().log('info', f'Using default map_scalebar_position={scale_pos}.')
            user_settings['map_scalebar_position'] = 'UL'
        posv = {'U': 0.85, 'L': 0.10}
        posh = {'R': 0.95, 'L': 0.05}
        if scalebar_position[0] == 'U':
            latsc = lats + abs(latn - lats) * posv['U']  # 0.87
        if scalebar_position[0] == 'L':
            latsc = lats + abs(latn - lats) * posv['L']  # 0.08
        if scalebar_position[1] == 'R':
            lonsc = lonw + abs(lone - lonw) * posh['R']  # 0.92
            scale_sign = -1.
        if scalebar_position[1] == 'L':
            lonsc = lonw + abs(lone - lonw) * posh['L']  # 0.08
            scale_sign = 1.
        ## scale bar width
        if scalebar_length is not None:
            scalelen = int(scalebar_length)
            unit = 'km'
        else:
            ## compute optimal scale length (as maximum fraction of image width)
            scalelen = dd * scalebar_max_fraction
            scalelen, unit = atmos.shared.scale_dist(scalelen)
        ## compute scaleline
        sf = 1
        if unit == 'm':
            scaleline = (scalelen / 1000) / lond
        else:
            scaleline = scalelen / lond
        ## scalebar label
        sclabel = '{} {}'.format(scalelen * sf, unit)
        ## compute scalebar position
        xsb = (lonsc, lonsc + scale_sign * scaleline)
        ysb = (latsc, latsc)
        ## compute scalebar label position
        xsbl = lonsc + (scale_sign * scaleline) / 2
        ysbl = latsc + (latr * 0.03)
        ## compute positions in pixels
        if not pcolormesh:
            tmp = ((lon - xsb[0]) ** 2 + (lat - ysb[0]) ** 2) ** 0.5
            il, jl = np.where(tmp == np.nanmin(tmp))
            tmp = ((lon - xsb[1]) ** 2 + (lat - ysb[1]) ** 2) ** 0.5
            ir, jr = np.where(tmp == np.nanmin(tmp))
            ysb = (il[0], ir[0])
            xsb = (jl[0], jr[0])
            tmp = ((lon - xsbl) ** 2 + (lat - ysbl) ** 2) ** 0.5
            ip, jp = np.where(tmp == np.nanmin(tmp))
            xsbl, ysbl = jp, ip
    ## end prepare scale bar

    rgb_used = None
    ## make plots
    for cpar in plot_parameters:

        cparl = cpar.lower()
        ## RGB
        if (cpar[0:7] == 'rgb_rho'):
            ## find datasets for RGB compositing
            rgb_wave = [red_wl, green_wl, blue_wl]
            ds_base = [ds.split('_')[0:-1] for ds in pslot_name_map if cpar.split('_')[1] in ds[0:len(cpar.split('_')[1])]]
            if len(ds_base) == 0:
                ds_base = '{}_'.format(cpar.split('_')[1])
            else:
                ds_base = '_'.join(ds_base[0]) + '_'
                if add_band_name:
                    ds_base = f"{cpar.split('_')[1]}_"
            rho_ds = [ds for ds in pslot_name_map if ds_base in ds[0:len(ds_base)]]
            rho_wv = [int(ds.split('_')[-1]) for ds in rho_ds]
            if len(rho_wv) < 3: continue

            ## read and stack rgb
            rgb_used = []
            for iw, w in enumerate(rgb_wave):
                wi, ww = atmos.shared.closest_idx(rho_wv, w)
                rgb_used.append(ww)
                # ds_name = '{}{}'.format(ds_base,ww)
                band_name = [v for k, v in pslot_name_map.items() if (ds_base in k) and (f'{ww:.0f}' in k)][0]
                data = band_dict['bands'][band_name]['data']

                ## autoscale rgb to percentiles
                if rgb_autoscale:
                    bsc = np.nanpercentile(data, rgb_autoscale_percentiles)
                else:
                    bsc = np.asarray((rgb_min[iw], rgb_max[iw]))

                gamma = rgb_gamma[iw]

                ## do RGB stretch
                tmp = atmos.shared.rgb_stretch(data, gamma=gamma, bsc=bsc, stretch=rgb_stretch)

                ## mask
                # tmp[np.isnan(data)] = 1

                ## set min/max to rgb stretch
                tmp[data <= bsc[0]] = 0
                tmp[data >= bsc[1]] = 1

                ## stack RGB
                if iw == 0:
                    im = tmp
                else:
                    im = np.dstack((im, tmp))
        ## other parameters
        else:
            if cparl not in pslot_name_map:
                Logger.get_logger().log('info', f'{cpar} not exists.')
                continue
            ds = [bname for slot, bname in pslot_name_map.items() if cparl == slot][0]
            ## read data
            im = band_dict[ds]

        ## plot figure
        create_map(im, lon=lon, lat=lat, scene_mask=scene_mask, rgb_used=rgb_used, font=font, title_base=title_base,
                   cpar=cpar, pscale=pscale, points=points,
                   xsb=xsb, ysb=ysb, xsbl=xsbl, ysbl=ysbl, sclabel=sclabel,
                   user_settings=user_settings, out_dir=out_dir, out_file_stem=out_file_stem, ro_type=cpar)