import matplotlib.gridspec as gsp
import matplotlib.colors as mcolors
import matplotlib.lines as mlines
import matplotlib.patches as mpatch
import matplotlib.pyplot as plt
import numpy as np

import fire_an.makeplots.cgm_fgas_zne.readprop as rpr
import fire_an.makeplots.plot_utils as pu
import fire_an.makeplots.tol_colors as tc
import fire_an.simlists as sl
import fire_an.utils.constants_and_units as c

mdir = '/projects/b1026/nastasha/imgs/cgmprop/'

#copied from PS20 tables
solarmassfrac_Ne = 10**-2.9008431 
solarmassfrac_Ztot = 0.01337137

def checkfracs_T_ne8():
    '''
    fraction of Ne8 < 10^5.0 K
    m12, (0.1, 1.0) Rvir: max 0.1169863860406003 missing
    m12, (0.0, 0.1) Rvir: max 0.0017332917011777527 missing
    m12, (0.0, 1.0) Rvir: max 0.1150003753578468 missing
    m12, (0.15, 0.25) Rvir: max 0.11599025905318427 missing
    m12, (0.45, 0.55) Rvir: max 0.21306723218894474 missing
    m12, (0.9, 1.0) Rvir: max 0.2676769245827688 missing
    m13, (0.1, 1.0) Rvir: max 0.005922894556624092 missing
    m13, (0.0, 0.1) Rvir: max 2.8164352013915206e-06 missing
    m13, (0.0, 1.0) Rvir: max 0.00591089235167197 missing
    m13, (0.15, 0.25) Rvir: max 1.7881382923801148e-05 missing
    m13, (0.45, 0.55) Rvir: max 0.00037643901925377143 missing
    m13, (0.9, 1.0) Rvir: max 0.019033203151526568 missing
    '''
    print('fraction of Ne8 < 10^5.0 K')
    for massset in ['m12', 'm13']:
        for rrange_rvir in [(0.1, 1.0), (0.0, 0.1), (0.0, 1.0),
                            (0.15, 0.25), (0.45, 0.55), (0.9, 1.0)]:
            data_allT = rpr.readin_all_data(rrange_rvir=rrange_rvir, 
                                            trange_logk=(-np.inf, np.inf),
                                            massset=massset)
            data_hiT = rpr.readin_all_data(rrange_rvir=rrange_rvir, 
                                           trange_logk=(5.0, np.inf),
                                           massset=massset)
            misshi = 1. - data_hiT['Ne8_numpart'] / data_allT['Ne8_numpart']
            print(f'{massset}, {rrange_rvir} Rvir: max {np.max(misshi)}'
                  ' missing')

def addpanel_hist(ax, df, kwa_phys, panel='fgas', fontsize=12,
                  xlabel=None):
    physmodels = list(np.unique(df['physmodel']))
    print(physmodels)
    if panel == 'fgas':
        _xlabel = ('$\\log_{10} \\, \\mathrm{M}_{\mathrm{gas}} \\,/\\, '
                  '(\\Omega_{\\mathrm{b}} '
                  ' \\mathrm{M}_{\mathrm{vir}} \\,/ \\,'
                  '\\Omega_{\\mathrm{m}})$')
        datakey = 'fgas'
    elif panel == 'ZNe':
        _xlabel = ('$\\log_{10} \\, \\mathrm{Z}_{\\mathrm{Ne}}'
              ' \\; [\\mathrm{Z}_{\\mathrm{Ne}, \\odot}]$')
        df['ZNe_solar'] = df['Neon_numpart'] * c.atomw_Ne * c.u \
                          / df['gasmass_g'] / solarmassfrac_Ne
        datakey = 'ZNe_solar'
    elif panel == 'Ne8frac':
        _xlabel = ('$\\log_{10} \\, \\mathrm{Ne\\,VIII} \\,/ \\,'
                  ' \\mathrm{Ne}$')
        datakey = 'Ne8frac'
        df['Ne8frac'] = df['Ne8_numpart'] / df['Neon_numpart']
    elif panel == 'meanNe8col':
        _xlabel = ('$\\log_{10} \\, \\langle\\mathrm{N}(\\mathrm{Ne\\,VIII})'
                  '\\rangle \\; [\\mathrm{cm}^{-2}]$')
        datakey = 'meanNe8col'
        df['meanNe8col'] = df['Ne8_numpart'] / (np.pi * df['Rvir_cm']**2)
    elif panel == 'Ztot':
        _xlabel = ('$\\log_{10} \\, \\mathrm{Z}_{\\mathrm{tot}}'
              ' \\; [\\mathrm{Z}_{\\mathrm{tot}, \\odot}]$')
        df['Ztot_solar'] = df['Ztot gasmass-wtd (mass fraction)'] \
                          / solarmassfrac_Ztot
        datakey ='Ztot_solar'
    elif panel == 'ZoverMstarcen':
        _xlabel = ('$\\log_{10} \\, \\mathrm{Metal\\,mass}'
              ' \\,/\\, \\mathrm{M}_{\\star, \\mathrm{cen}}$')
        df['ZoverMstarcen'] = df['Ztot gasmass-wtd (mass fraction)'] \
                              * df['gasmass_g'] / df['Mstarcen_g']
        datakey = 'ZoverMstarcen'
    elif panel == 'ZoverMstarhalo':
        _xlabel = ('$\\log_{10} \\, \\mathrm{Metal\\,mass}'
                  ' \\,/\\, \\mathrm{M}_{\\star, \\mathrm{halo}}$')
        df['ZoverMstarhalo'] = df['Ztot gasmass-wtd (mass fraction)'] \
                              * df['gasmass_g'] / df['Mstar_current_g']
        datakey = 'ZoverMstarhalo'
    elif panel == 'Mvir':
        _xlabel = ('$\\log_{10} \\, \\mathrm{M}_{\\mathrm{vir}}'
                  ' \\; [\\mathrm{M}_{\\odot}]$')
        df['Mvir_Msun'] = df['Mvir_g'] / c.solar_mass
        datakey = 'Mvir_Msun'
    elif panel == 'Mstarcen':
        _xlabel = ('$\\log_{10} \\, \\mathrm{M}_{\\star, \\mathrm{cen}}'
                   ' \\; [\\mathrm{M}_{\\odot}]$')
        df['Mstarcen'] = df['Mstarcen_g'] / c.solar_mass
        datakey = 'Mstarcen'
    elif panel == 'Ne8':
        _xlabel = ('$\\log_{10} \\, \\mathrm{M}(\\mathrm{Ne\\,VIII})'
                  ' \\; [\\mathrm{M}_{\\odot}]$')
        df['Ne8mass'] = df['Ne8_numpart'] * c.atomw_Ne * c.u / c.solar_mass
        datakey = 'Ne8mass'
    if xlabel is None:
        xlabel = _xlabel
    # somewhat iterative bin determination 
    # (tiny bins make line overlaps hard to avoid)
    numbins = 15
    vmin = np.log10(np.min(df[datakey]))
    vmax = np.log10(np.max(df[datakey]))
    numphys = len(physmodels)
    delta = 0.015
    bins = np.linspace(vmin - delta * numphys, 
                       vmax + delta * numphys, 
                       numbins + 1)
    if np.average(np.diff(bins)) > 0.15 * delta:
        numbins = 12
        bins = np.linspace(vmin - delta * numphys, 
                           vmax + delta * numphys, 
                           numbins + 1)
    if np.average(np.diff(bins)) > 0.2 * delta:
        numbins = 10
        bins = np.linspace(vmin - delta * numphys, 
                           vmax + delta * numphys, 
                           numbins + 1)
    print('bin size / offset: ', np.average(np.diff(bins)) / delta)

    sortorder = {'FIRE-2': 0,
                 'noBH': 1,
                 'noBH-m12+': 2,
                 'AGN-noCR': 3,
                 'AGN-CR': 4,
                 'FIRE-3x-scmodules': 5,
                 'FIRE-3x-constpterm': 6}
    #print(df.loc[df['physmodel'] == 'noBH-m12+', 'Mvir_g'] / c.solar_mass)
    #print(df.loc[df['physmodel'] == 'noBH-m12+', 'Mstarcen_g'] / c.solar_mass)
    physmodels.sort(key=sortorder.__getitem__)
    for pi, physmodel in enumerate(physmodels):
        binoffset = delta * (pi + 0.5 - 0.5 * numphys)
        filter = df['physmodel'] == physmodel
        ax.hist(np.log10(df.loc[filter, datakey]), 
                bins=bins + binoffset,
                **(kwa_phys[physmodel]),
                histtype='step', density=True)
    ax.set_xlabel(xlabel, fontsize=fontsize)

def plotpanels_general(massset, rrange_rvir=(0.1, 1.0),
                       trange_logk=(5.0, np.inf),
                       panels=('fgas', 'ZNe', 'Ne8frac'),
                       xlabels=None, inclm12plus=False,
                       f3xset=False):
    fontsize = 12
    npanels = len(panels)
    ncols = min(npanels, 2)
    nrows = (npanels - 1) // ncols + 1
    panelsize = 2.5
    width_ratios = [panelsize] * ncols
    height_ratios = [panelsize] * nrows
    wspace = 0.0
    hspace = 0.25
    width = sum(width_ratios) * (1. + (ncols - 1.) / ncols * wspace)
    height = sum(height_ratios) * (1. + (nrows - 1.) / ncols * hspace)

    fig = plt.figure(figsize=(width, height))
    grid = gsp.GridSpec(ncols=ncols, nrows=nrows, 
                        height_ratios=height_ratios,
                        width_ratios=width_ratios,
                        wspace=wspace, hspace=hspace)
    axes = [fig.add_subplot(grid[i // ncols, i % ncols])
            for i in range(npanels)]
    
    df = rpr.readin_all_data(massset=massset, rrange_rvir=rrange_rvir,
                             trange_logk=trange_logk, 
                             inclm12plus=inclm12plus, f3xset=f3xset)
    kwa_phys = {key: {'color': val, 'linewidth': 1.5}
                for key, val in sl.physcolors.items()}
    kwa_phys['noBH-m12+'] = kwa_phys['noBH'].copy()
    kwa_phys['noBH-m12+']['linestyle'] = 'dashed'
    kwa_phys['noBH-m12+']['color'] = 'black'
    kwa_phys['FIRE-3x-scmodules'] = kwa_phys['noBH'].copy()
    kwa_phys['FIRE-3x-scmodules']['color'] = sl._physcolors.cyan
    kwa_phys['FIRE-3x-constpterm'] = kwa_phys['noBH'].copy()
    kwa_phys['FIRE-3x-constpterm']['color'] = sl._physcolors.purple

    for axi, (ax, panel) in enumerate(zip(axes, panels)):
        doleft = axi % ncols == 0
        ax.tick_params(which='both', direction='in', labelsize=fontsize - 1,
                       right=True, top=True, labelbottom=True, 
                       labelleft=doleft)
        if doleft:
            ax.set_ylabel('pdf', fontsize=fontsize)
        if xlabels is None:
            _xl = None
        else:
            _xl  = xlabels[axi]
        addpanel_hist(ax, df, kwa_phys, panel=panel, 
                      fontsize=fontsize, xlabel=_xl)
    xlims = [ax.get_xlim() for ax in axes]
    xranges = [xl[1] - xl[0] for xl in xlims]
    xrmax = max(xranges)
    ylims = [ax.get_ylim() for ax in axes]
    ymin = min([yl[0] for yl in ylims])
    ymax = max([yl[1] for yl in ylims])
    for ax in axes:
        ax.set_ylim((ymin, ymax))
        xlim = ax.get_xlim()
        xr = xlim[1] - xlim[0]
        if xr < xrmax:
            xmin = xlim[0] - 0.5 * (xrmax - xr)
            xmax = xlim[1] + 0.5 * (xrmax - xr)
            ax.set_xlim((xmin, xmax))
    
    handles = [mlines.Line2D((), (), label=sl.plotlabel_from_physlabel[key],
                             **val)
               for key, val in kwa_phys.items()]
    axes[0].legend(handles=handles, fontsize=fontsize - 2,
                   handlelength=1.)
    
    m12plusstr = '_inclm12plus' if inclm12plus else ''
    f3xstr = '_f3xtest' if f3xset else ''
    outname = (f'cgmprophist_{massset}_{rrange_rvir[0]:.2f}_to_'
               f'{rrange_rvir[1]:.2f}_gas_ge_{trange_logk[0]:.1f}_logK'
               '_') + m12plusstr + f3xstr + '_'.join(panels)
    outname = outname.replace('.', 'p')
    outname = outname.replace('-', 'm')
    outname = mdir + outname + '.pdf'
    plt.savefig(outname, bbox_inches='tight')

def plotpanels_main(massset='m12'):
    panels = ('meanNe8col', 'fgas', 'ZNe', 'Ne8frac')
    xlabels = [('$\\log_{10} \\, \\langle\\mathrm{N}(\\mathrm{Ne\\,VIII})'
                '\\rangle \\; [\\mathrm{cm}^{-2}]$'),
               ('$\\log_{10} \\, \\mathrm{M}_{\mathrm{gas},'
                ' \\mathrm{hot}} \\,/\\, '
                '(\\Omega_{\\mathrm{b}} '
                ' \\mathrm{M}_{\mathrm{vir}} \\,/ \\,'
                '\\Omega_{\\mathrm{m}})$'),
               ('$\\log_{10} \\, \\mathrm{Z}_{\\mathrm{Ne}, '
                '\\mathrm{hot}}'
                ' \\; [\\mathrm{Z}_{\\mathrm{Ne}, \\odot}]$'),
               ('$\\log_{10} \\, \\mathrm{Ne\\,VIII} \\,/ \\,'
                ' \\mathrm{Ne}_{\\mathrm{hot}}$'),
               ]
    dat_allgas = rpr.readin_all_data(rrange_rvir=(0.1, 1.0), 
                                     trange_logk=(-np.inf, np.inf),
                                     massset=massset)
    dat_whcgm = rpr.readin_all_data(rrange_rvir=(0.1, 1.0), 
                                    trange_logk=(5.0, np.inf),
                                    massset=massset)
    dat = dat_whcgm.copy()
    dat['meanNe8col'] = dat_allgas['Ne8_numpart'] \
                        / (np.pi * dat_allgas['Rvir_cm']**2)
    dat['ZNe'] = dat_whcgm['Neon_numpart'] * c.atomw_Ne * c.u \
                / dat_whcgm['gasmass_g'] / solarmassfrac_Ne
    dat['Ne8frac'] = dat_allgas['Ne8_numpart'] / dat_whcgm['Neon_numpart']
    physmodels = list(np.unique(dat['physmodel']))
    sortorder = {'FIRE-2': 0,
                 'noBH': 1,
                 'AGN-noCR': 2,
                 'AGN-CR': 3}
    physmodels.sort(key=sortorder.__getitem__)

    fontsize = 12
    npanels = len(panels)
    ncols = min(npanels, 2)
    nrows = (npanels - 1) // ncols + 1
    panelsize = 2.5
    width_ratios = [panelsize] * ncols
    height_ratios = [panelsize] * nrows
    wspace = 0.25
    hspace = 0.25
    width = sum(width_ratios) * (1. + (ncols - 1.) / ncols * wspace)
    height = sum(height_ratios) * (1. + (nrows - 1.) / ncols * hspace)

    fig = plt.figure(figsize=(width, height))
    grid = gsp.GridSpec(ncols=ncols, nrows=nrows, 
                        height_ratios=height_ratios,
                        width_ratios=width_ratios,
                        wspace=wspace, hspace=hspace)
    axes = [fig.add_subplot(grid[i // ncols, i % ncols])
            for i in range(npanels)]
    
    kwa_phys = {key: {'color': val, 'linewidth': 1.5}
                for key, val in sl.physcolors.items()}
    kwa_phys['FIRE-2'].update({'path_effects': pu.getoutline(1.7)})
    
    for axi, (ax, panel, xlab) in enumerate(zip(axes, panels, xlabels)):
        doleft = True #axi % ncols == 0
        ax.tick_params(which='both', direction='in',
                       labelsize=fontsize - 1,
                       right=True, top=True, labelbottom=True, 
                       labelleft=doleft)
        if doleft:
            ax.set_ylabel('pdf', fontsize=fontsize)
        ax.set_xlabel(xlab, fontsize=fontsize - 1)

        # somewhat iterative bin determination 
        # (tiny bins make line overlaps hard to avoid)
        numbins = 15
        vmin = np.log10(np.min(dat[panel]))
        vmax = np.log10(np.max(dat[panel]))
        numphys = len(physmodels)
        delta = 0.015
        bins = np.linspace(vmin - delta * numphys, 
                           vmax + delta * numphys, 
                           numbins + 1)
        if np.average(np.diff(bins)) > 0.15 * delta:
            numbins = 12
            bins = np.linspace(vmin - delta * numphys, 
                            vmax + delta * numphys, 
                            numbins + 1)
        if np.average(np.diff(bins)) > 0.2 * delta:
            numbins = 10
            bins = np.linspace(vmin - delta * numphys, 
                            vmax + delta * numphys, 
                            numbins + 1)
        print('bin size / offset: ', np.average(np.diff(bins)) / delta)
        for pi, physmodel in enumerate(physmodels):
            binoffset = delta * (pi + 0.5 - 0.5 * numphys)
            filter = dat['physmodel'] == physmodel
            ax.hist(np.log10(dat.loc[filter, panel]), 
                    bins=bins + binoffset,
                    **(kwa_phys[physmodel]),
                    histtype='step', density=True,
                    label=sl.plotlabel_from_physlabel[physmodel])
            
    xlims = [ax.get_xlim() for ax in axes]
    xranges = [xl[1] - xl[0] for xl in xlims]
    xrmax = max(xranges)
    #ylims = [ax.get_ylim() for ax in axes]
    #ymin = min([yl[0] for yl in ylims])
    #ymax = max([yl[1] for yl in ylims])
    ylim0 = axes[0].get_ylim()
    axes[0].set_ylim((ylim0[0], 2.0 * ylim0[1])) # add space for legend
    for axi, ax in enumerate(axes):
        #ax.set_ylim((ymin, ymax))
        xlim = ax.get_xlim()
        xr = xlim[1] - xlim[0]
        if xr < xrmax:
            xmin = xlim[0] - 0.5 * (xrmax - xr)
            xmax = xlim[1] + 0.5 * (xrmax - xr)
            # avoid tick label overlap
            if axi == 3 and massset == 'm12': 
                xmin -= 0.2
                xmax -= 0.2
            #elif axi == 2 and massset == 'm12':
            #    xmin += 0.1
            #    xmax += 0.1
            ax.set_xlim((xmin, xmax))
    
    #handles = [mlines.Line2D((), (), label=sl.plotlabel_from_physlabel[key],
    #                         **val)
    #           for key, val in kwa_phys.items()]
    axes[0].legend(fontsize=fontsize - 2,
                   handlelength=1.)
    outname = (f'cgmprophist_{massset}_0p1_to_1p0_gasNe_geq_5p0_logK_allNe8'
               '_') + '_'.join(panels)
    outname = outname.replace('.', 'p')
    outname = outname.replace('-', 'm')
    outname = mdir + outname + '.pdf'
    plt.savefig(outname, bbox_inches='tight')


def plotoverviews_f3xtest():
    plotpanels_general('m12', rrange_rvir=(0.1, 1.0),
                       trange_logk=(5.0, np.inf),
                       panels=('Mvir', 'Mstarcen',
                               'ZoverMstarcen', 'ZoverMstarhalo',
                               'fgas', 'ZNe', 'Ztot'),
                       xlabels=None, inclm12plus=False,
                       f3xset=True)
    plotpanels_general('m12', rrange_rvir=(0.1, 1.0),
                       trange_logk=(-np.inf, np.inf),
                       panels=('Mvir', 'Mstarcen',
                               'ZoverMstarcen', 'ZoverMstarhalo',
                               'fgas', 'ZNe', 'Ztot'),
                       xlabels=None, inclm12plus=False,
                       f3xset=True)
    

        
        

    

