import os, copy
import numpy as np

import pyproj
from osgeo import ogr, osr

import matplotlib as mpl
import matplotlib.cm as cm
import matplotlib.pyplot as plt
import matplotlib.patheffects as pe
from mpl_toolkits.axes_grid1 import make_axes_locatable
from cartopy.mpl.gridliner import LONGITUDE_FORMATTER, LATITUDE_FORMATTER

from PIL import Image

import core.atmos as atmos

def output_map(im, lon, lat, scene_mask, rgb_used, graph_limit, font, crs, out_dir, out_file_name, ro_type, title_base:str,
               cpar, pscale, img_extent, image_crs, points, xsb, ysb, xsbl, ysbl, sclabel,
               map_save:bool, map_show:bool, user_settings:dict):

    def _load_params():
        default_colormap = user_settings['map_default_colormap']
        auto_range = user_settings['map_auto_range']
        auto_range_percentiles = user_settings['map_auto_range_percentiles']
        fill_color = user_settings['map_fill_color']
        fill_outrange = user_settings['map_fill_outrange']
        title_rgb_wavelengths = user_settings['map_title_rgb_wavelengths']
        raster = user_settings['map_raster']
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

        return default_colormap, auto_range, auto_range_percentiles, fill_color, fill_outrange, title_rgb_wavelengths, raster, pcolormesh, \
            xtick_rotation, ytick_rotation, fontsize, gridline_color, title_exists, scalebar, scalebar_color, colorbar, colorbar_orientation, dpi

    default_colormap, auto_range, auto_range_percentiles, fill_color, fill_outrange, title_rgb_wavelengths, raster, pcolormesh, \
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
            pard['cmap'] = mpl.colors.ListedColormap(np.loadtxt(ctfile) / 255.)
        else:
            try:
                cmap = copy.copy(mpl.cm.get_cmap(pard['cmap']))
            except:
                pard['cmap'] = default_colormap

        ## copy colour map to not set bad/under globally
        cmap = copy.copy(mpl.cm.get_cmap(pard['cmap']))
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
        norm = mpl.colors.Normalize(vmin=pard['min'], vmax=pard['max'])  # , clip=setu['map_fill_outrange'])
    else:
        part = rf'$\rho_{ro_type[-1]}$ RGB'
        if title_rgb_wavelengths:
            part += f' ({", ".join([f"{w:.0f} nm" for w in rgb_used])})'

    ## title and outputfile
    title = f'{title_base}\n{part}'
    ofile = f'{out_dir}/{out_file_name}_{ro_type}.png'

    ## raster 1:1 pixel outputs
    if raster:
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
        ax = fig.add_subplot(1, 1, 1, projection=crs)
        plt.sca(ax)
        if crs is None:
            if pcolormesh:
                if rgb:  ## convert rgb values to color tuple before mapping
                    if mpl.__version__ > '3.7.0':
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
                if graph_limit is not None:
                    plt.xlim(graph_limit[1], graph_limit[3])
                    plt.ylim(graph_limit[0], graph_limit[2])
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
        else:  ## cartopy
            axim = ax.imshow(im, origin='upper', extent=img_extent, transform=image_crs, norm=norm, cmap=cmap)
            gl = ax.gridlines(draw_labels=True, linewidth=1, color=gridline_color, alpha=0.75, linestyle='--')
            gl.top_labels = False
            gl.left_labels = True
            gl.bottom_labels = True
            gl.right_labels = False
            ## set size and rotation of ticklabels
            gl.xlabel_style = {'size': fontsize, 'rotation': xtick_rotation}
            gl.ylabel_style = {'size': fontsize, 'rotation': ytick_rotation}

            ## format ticks
            gl.xformatter = LONGITUDE_FORMATTER
            gl.yformatter = LATITUDE_FORMATTER

        if title_exists:
            plt.title(title, **font)

        ## add point markers
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
                if crs is None:
                    divider = make_axes_locatable(ax)
                    cax = divider.append_axes('right', size='5%', pad=0.05)
                else:
                    cax = ax.inset_axes((1.02, 0, 0.02, 1));  # make a color bar axis
                cbar = fig.colorbar(axim, cax=cax, orientation='vertical')
                cbar.ax.set_ylabel(part)
            else:
                if crs is None:
                    divider = make_axes_locatable(ax)
                    cax = divider.append_axes('bottom', size='5%', pad=0.05)
                else:
                    cax = ax.inset_axes((0, -0.05, 1, 0.02))  # make a color bar axis
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

        if map_save:
            plt.savefig(ofile, dpi=dpi, bbox_inches='tight', facecolor='white')
            # if setu['verbosity'] > 1: print('Wrote {}'.format(ofile))
        if map_show:
            plt.show()
        plt.close()

def write_map(output_dict, output_band_list, out_dir, out_file_stem):
    pass