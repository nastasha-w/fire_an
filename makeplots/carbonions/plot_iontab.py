import numpy as np

import matplotlib.gridspec as gsp
import matplotlib.pyplot as plt

from fire_an.ionrad.ion_utils import Linetable_PS20
import fire_an.makeplots.tol_colors as tc


def plotiontab(ions, z, outname=None):
    fraclevels = np.log10(np.array([0.01, 0.03, 0.1, 0.3]))
    fracstyles = ['dotted', 'dashdot', 'dashed', 'solid']
    zind = -2
    vmin = -3.
    vmax = 0.
    cmap = 'gist_yarg'
    fontsize = 12

    npanels = len(ions)
    ncols = min(npanels, 3)
    nrows = (npanels - 1) // ncols + 1
    hspace = 0.
    wspace = 0.
    panelsize = 2.5
    caxwidth = 0.5
    width = ncols * panelsize
    height = nrows * panelsize
    width_ratios = [panelsize] * ncols + [caxwidth]

    fig = plt.figure(figsize=(width, height))
    grid = gsp.GridSpec(nrows=nrows, ncols=ncols + 1,
                        hspace=hspace, wspace=wspace,
                        width_ratios=width_ratios)
    frameax = fig.add_subplot(grid[:, :-1])
    frameax.tick_params(bottom=False, left=False, labelbottom=False, 
                        labelleft=False)
    frameax.spines['top'].set_visible(False)
    frameax.spines['bottom'].set_visible(False)
    frameax.spines['left'].set_visible(False)
    frameax.spines['right'].set_visible(False)
    xlab = ('$\\log_{10} \\, \\mathrm{n}_{\\mathrm{H}}'
            ' \\; [\\mathrm{cm}^{-3}]$')
    ylab = '$\\log_{10} \\, \\mathrm{T} \\; [\\mathrm{K}]$'
    frameax.set_xlabel(xlab, fontsize=fontsize, labelpad=20)
    frameax.set_ylabel(ylab, fontsize=fontsize, labelpad=28)

    axes = [fig.add_subplot(grid[i // ncols, i % ncols]) 
            for i in range(npanels)]
    cax = fig.add_subplot(grid[:2, -1])
    for ii, ion in enumerate(ions):
        iontab = Linetable_PS20(ion, z, emission=False, vol=True,
                                lintable=False)
        iontab.findiontable()
        tab_logT = iontab.logTK
        tab_lognH = iontab.lognHcm3
        tab_logZ = iontab.logZsol + np.log10(iontab.solarZ)
        tab_ionbal_T_Z_nH = iontab.iontable_T_Z_nH.copy()
        tab_ionbal_T_nH = tab_ionbal_T_Z_nH[:, zind, :]
        zval = tab_logZ[zind]
        deltalT = np.average(np.diff(tab_logT))
        edges_logT = np.append(tab_logT - 0.5 * deltalT, 
                                tab_logT[-1] + 0.5 * deltalT)
        deltalnH = np.average(np.diff(tab_logT))
        edges_lognH = np.append(tab_lognH - 0.5 * deltalnH, 
                               tab_lognH[-1] + 0.5 * deltalnH)

        ax = axes[ii]
        labelbottom = ii >= npanels - ncols
        labelleft = ii % ncols == 0
        ax.tick_params(which='both', direction='in', top=True,
                       right=True, labelbottom=labelbottom, 
                       labelleft=labelleft)
        img = ax.pcolormesh(edges_lognH, edges_logT, tab_ionbal_T_nH,
                            cmap=cmap, vmin=vmin, vmax=vmax)
        ax.contour(tab_lognH, tab_logT, tab_ionbal_T_nH, 
                   levels=fraclevels, linestyles=fracstyles,
                   colors='fuchsia')
        ax.text(0.05, 0.82, ion, fontsize=fontsize, color='black',
                horizontalalignment='left', verticalalignment='top',
                transform=ax.transAxes)
        txt = f'$\\mathrm{{Z}} = {10**zval:.3f}, \\mathrm{{z}} = {z:.1f}$'
        ax.text(0.05, 0.95, txt, 
                fontsize=fontsize, color='black',
                horizontalalignment='left', verticalalignment='top',
                transform=ax.transAxes)
    plt.colorbar(img, cax=cax, orientation='vertical', extend='min')
    for ls, lv in zip(fracstyles, fraclevels):
        cax.axhline(lv, linestyle=ls, color='fuchsia')
    cax.set_ylabel('$\\log_{10}$ ion / element', fontsize=fontsize)
    
    if outname is not None:
        plt.savefig(outname, bbox_inches='tight')

def plotsetiontab(ionset='carbon'):
    zs = [0., 0.5, 1.0]
    outdir = '/Users/nastasha/ciera/projects_co/hsiao-wen_carbon_ions/'
    if ionset == 'carbon':
        filen = 'iontables_met0.013_z{z:.1f}_carbonions'
        ions = ['C1', 'C2', 'C3', 'C4', 'C5', 'C6']
    elif ionset == 'oxygen':
        filen = 'iontables_met0.013_z{z:.1f}_oxygenions'
        ions = [f'O{i}' for i in range(1, 9)]
    elif ionset == 'c4o3456':
        filen = 'iontables_met0.013_z{z:.1f}_C4Ocompions'
        ions = ['C4', 'O3', 'O4', 'O5', 'O6']
    for z in zs:
        outname = outdir + filen.format(z=z)
        outname.replace('.', 'p')
        outname = outname + '.pdf'
        plotiontab(ions, z, outname=outname)

def plotioncurve(ions, z, outname=None):
    zind = -2
    nHind = -11
    colors = tc.tol_cset('vibrant')
    linestyles = ['solid', 'dashed', 'dotted', 'dashdot']
    fontsize = 12
    fig = plt.figure(figsize=(5.5, 5.))
    ax = fig.add_axes([0.1, 0.1, 0.8, 0.8])
    xlab = '$\\log_{10} \\, \\mathrm{T} \\; [\\mathrm{K}]$'
    ax.set_xlabel(xlab, fontsize=fontsize)
    ax.set_ylabel('$\\log_{10}$ ion / element', fontsize=fontsize)
    ax.tick_params(which='both', direction='in', top=True,
                       right=True, labelbottom=True, 
                       labelleft=True)
    minx = np.inf
    maxx = -np.inf
    ymin = -4.2
    ymax = 0.1
    for ii, ion in enumerate(ions):
        iontab = Linetable_PS20(ion, z, emission=False, vol=True,
                                lintable=False)
        iontab.findiontable()
        tab_logT = iontab.logTK
        tab_lognH = iontab.lognHcm3
        tab_logZ = iontab.logZsol + np.log10(iontab.solarZ)
        tab_ionbal_T_Z_nH = iontab.iontable_T_Z_nH.copy()
        tab_ionbal_T = tab_ionbal_T_Z_nH[:, zind, nHind]
        zval = tab_logZ[zind]
        nHval = tab_lognH[nHind]

        color = colors[ii % len(colors)]
        ls = linestyles[ii //len(colors)]
        ax.plot(tab_logT, tab_ionbal_T, color=color, linestyle=ls,
                label=ion)
        xir = np.where(tab_ionbal_T >= ymin)[0]
        minx = min(minx, tab_logT[xir[0]])
        maxx = max(maxx, tab_logT[xir[-1]])
    txt = (f'$\\mathrm{{Z}} = {10**zval:.3f},\\; \\mathrm{{z}} = {z:.1f}'
           f',\\; \\mathrm{{n}}_{{\\mathrm{{H}}}} = 10^{{{nHval:.1f}}}'
           '\\mathrm{cm}^{-3}$')
    #ax.text(0.05, 0.95, txt, 
    #        fontsize=fontsize, color='black',
    #        horizontalalignment='left', verticalalignment='top',
    #        transform=ax.transAxes)
    ax.set_title(txt, fontsize=fontsize)
    ax.set_ylim((ymin, ymax))
    xlo = minx - 0.1 * (maxx - minx)
    xhi = maxx + 0.1 * (maxx - minx)
    ax.set_xlim((xlo, xhi))
    ax.legend(fontsize=fontsize)
    if outname is not None:
        plt.savefig(outname, bbox_inches='tight')

def plotsetioncurves(ionset='carbon'):
    zs = [0.]
    outdir = '/Users/nastasha/ciera/projects_co/hsiao-wen_carbon_ions/'
    if ionset == 'carbon':
        filen = 'ionbalT_met0.013_z{z:.1f}_carbonions'
        ions = ['C1', 'C2', 'C3', 'C4', 'C5', 'C6']
    elif ionset == 'oxygen':
        filen = 'ionbalT_met0.013_z{z:.1f}_oxygenions'
        ions = [f'O{i}' for i in range(1, 9)]
    elif ionset == 'c4o3456':
        filen = 'ionbalT_met0.013_z{z:.1f}_C4Ocompions'
        ions = ['C4', 'O3', 'O4', 'O5', 'O6']
    for z in zs:
        outname = outdir + filen.format(z=z)
        outname.replace('.', 'p')
        outname = outname + '.pdf'
        plotioncurve(ions, z, outname=outname)