import h5py
import numpy as np
import os
import pandas as pd

import matplotlib.gridspec as gsp
import matplotlib.lines as mlines
import matplotlib.patches as mpatch
import matplotlib.pyplot as plt

import fire_an.makeplots.get_2dprof as gpr
import makeplots.litcomp.b19_datasel_old as bds 
import makeplots.litcomp.b19_vs_analytical_old as bva
import fire_an.makeplots.tol_colors as tc
import fire_an.makeplots.plot_utils as pu
import fire_an.simlists as sl
import fire_an.utils.constants_and_units as c
import fire_an.utils.cosmo_utils as cu
import fire_an.utils.opts_locs as ol

def addcoldata(ax, data_bur, labelmeas=None, labelul=None, datasel=None):
    isul = data_bur['log_N_Ne8_isUL'].copy()
    notul = np.logical_not(isul)
    if datasel is None:
        datasel = np.ones((len(data_bur),), dtype=bool)
    color_main = 'black'
    color_rest = 'gray'
    dsel_main_ul = np.logical_and(isul, datasel)
    dsel_main_noul = np.logical_and(notul, datasel)
    dsel_rest_ul = np.logical_and(isul, np.logical_not(datasel))
    dsel_rest_noul = np.logical_and(notul, np.logical_not(datasel))
    
    labelsset = False
    for dsel_ul, dsel_noul, color in [(dsel_main_ul, dsel_main_noul, 
                                       color_main),
                                      (dsel_rest_ul, dsel_rest_noul, 
                                       color_rest)]:
        if not labelsset:
            _labelmeas = labelmeas
            _labelul = labelul
            labelsset = True
        else:
            _labelmeas = None
            _labelul = None
        ax.errorbar(data_bur['impact_parameter_kpc'][dsel_noul], 
                    data_bur['log_N_Ne8_pcm2'][dsel_noul],
                    yerr=data_bur['log_N_Ne8_pcm2_err'][dsel_noul], 
                    linestyle='None', elinewidth=2., marker='o', 
                    markersize=7, color=color, capsize=3,
                    label=_labelmeas, zorder=5,
                    markeredgecolor='black', ecolor='black')
        ax.scatter(data_bur['impact_parameter_kpc'][dsel_ul], 
                    data_bur['log_N_Ne8_pcm2'][dsel_ul],
                    linestyle='None', marker='v', 
                    s=30, facecolors='none', edgecolors=color, 
                    label=_labelul, zorder=5, linewidths=1.5)

def addveldata(ax, data_bur, label=None, absvals=True, datasel=None):
    isul = data_bur['log_N_Ne8_isUL'].copy()
    notul = np.logical_not(isul)
    ydata = (data_bur['v_kmps']).astype(np.float)
    if absvals: 
        ydata = np.abs(ydata)
    if datasel is None:
        datasel = np.ones((len(data_bur),), dtype=bool)
    color_main = 'black'
    color_rest = 'gray'
    dsel_main_noul = np.logical_and(datasel, notul)
    dsel_rest_noul = np.logical_and(np.logical_not(datasel), notul)
    labelsset = False
    for dsel_noul, color in [(dsel_main_noul, color_main),
                             (dsel_rest_noul, color_rest)]:
        if not labelsset:
            _label = label
            labelsset = True
        else:
            _label = None
        ax.errorbar(data_bur['impact_parameter_kpc'][dsel_noul], 
                    ydata[dsel_noul],
                    yerr=data_bur['v_kmps_err'][dsel_noul], 
                    linestyle='None', elinewidth=2., marker='o', 
                    markersize=7, color=color, markeredgecolor='black',
                    ecolor='black', capsize=3,
                    label=_label, zorder=5)

def cdprof_ne8_burchett19(filen_temp, simnames, rbins_pkpc,
                          showscatter='clean',
                          datafieldsels=None, outname=None,
                          plottype='coldens', ne8_colsel=None,
                          inclf2md=True):
    '''
    plottype: 'coldens', 'abslosvel', or 'losvel'
    '''
    oddir = '/projects/b1026/nastasha/extdata/'
    ofilen = oddir + 'data_burchett_etal_2019_table1.txt'

    fontsize = 12
    xlabel = '$\\mathrm{r}_{\\perp}$ [pkpc]'
    if plottype == 'coldens':
        ylabel = ('$\\log_{10} \\, \\mathrm{N}(\\mathrm{Ne\\, VIII}) \\;'
                  '[\\mathrm{cm}^{-2}]$')
    elif plottype == 'abslosvel':
        ylabel = ('$|v_{\\mathrm{los}}| \\; '
                  '[\\mathrm{km}\\, \\mathrm{s}^{-1}]$')
    elif plottype == 'losvel':
        ylabel = ('$v_{\\mathrm{los}} \\; '
                  '[\\mathrm{km}\\, \\mathrm{s}^{-1}]$')
    if inclf2md:
        axlabels = ['FIRE-2', 'noBH', 'AGN-noCR', 'AGN-CR']
    else: 
        axlabels = ['noBH', 'AGN-noCR', 'AGN-CR']
    otherfills = [{'pax': 'x'}, {'pax': 'y'}, {'pax': 'z'}]
    sims_sr = sl.m12_sr_all2 + sl.m13_sr_all2
    sims_hr = sl.m12_hr_all2 + sl.m13_hr_all2
    sims_f2md = sl.m12_f2md

    if showscatter == 'clean':
        ics = [simname.split('_')[0] for simname in simnames]
        icsset = np.array(list(set(ics)))
        cleansel = np.array([sum([_ic == ic for _ic in ics]) == len(axlabels)
                            for ic in icsset])
        scatterics = icsset[cleansel]
    elif showscatter == 'all':
        scatterics = [simname.split('_')[0] for simname in simnames]
    else:
        scatterics = showscatter

    lw_main = 2.
    lw_sup = 1.
    alpha_range = 0.3
    colors = sl.m13_iccolors.copy()
    colors.update(sl.m12_iccolors)
    icusedlist = []
    rcens = 0.5 * (rbins_pkpc[1:] + rbins_pkpc[:-1])

    panelsize = 3.
    numcols = len(axlabels)
    numrows = 1
    legheight = 0.5
    wspace = 0.
    width_ratios = [panelsize] * numcols
    hspace = 0.25
    height_ratios = [panelsize] * numrows + [legheight]
    width = sum(width_ratios) * (1. + 1. / (len(width_ratios) - 1.) * wspace)
    height = sum(height_ratios) \
             * (1. + 1. / (len(height_ratios) - 1.) * hspace)
    fig = plt.figure(figsize=(width, height))
    grid = gsp.GridSpec(nrows=numrows + 1, ncols=numcols, hspace=hspace, 
                        wspace=wspace, width_ratios=width_ratios,
                        height_ratios=height_ratios)
    axes = [fig.add_subplot(grid[0, i]) for i in range(numcols)]
    lax = fig.add_subplot(grid[1, :])

    #title = 'Burchett et al. (2019) data vs. FIRE-3 z=0.5-1.0'
    #fig.suptitle(title, fontsize=fontsize)

    #print(modelfilelists)
    for simn in simnames:
        if simn in sims_sr:
            snapnums = sl.snaps_sr
        elif simn in sims_hr:
            snapnums = sl.snaps_hr
        elif simn in sims_f2md:
            snapnums = sl.snaps_f2md
        else:
            msg = (f'No snap list for simname {simn}; options:'
                   f'{sims_hr},\n{sims_sr}')
            raise RuntimeError(msg)
        simlabel = sl.ic_from_simname(simn)
        filens = [filen_temp.format(simname=simn, snapnum=snap, **ofill)
                  for snap in snapnums for ofill in otherfills]
        if plottype == 'coldens':
            weightmap = True
            absvals = False
            unitconv = 1.
        elif plottype == 'abslosvel':
            weightmap = False
            absvals = True
            unitconv = 1e-5
        elif plottype == 'losvel':
            weightmap = False
            absvals = False
            unitconv = 1e-5
        plo, pmed, phi = gpr.get_profile_massmap(filens, rbins_pkpc,
                                                 rbin_units='pkpc',
                                                 profiles=['perc-0.1', 
                                                           'perc-0.5', 
                                                           'perc-0.9'],
                                                 weightmap=weightmap,
                                                 absvals=absvals,
                                                 weightrange=ne8_colsel)
        if simlabel not in icusedlist:
            icusedlist.append(simlabel)
        #    _label = None
        #    ici = np.where([simlabel == _ic for _ic in icusedlist])[0][0]
        #else:
        #    _label = simlabel
        #    icusedlist.append(simlabel)
        #    ici = len(icusedlist) - 1 
        plab = sl.physlabel_from_simname(simn) 
        #ismain = simlabel in scatterics
        lw = 1.5 #lw_main if ismain else lw_sup
        ax = axes[np.where([plab == axt for axt in axlabels])[0][0]] 
        color = colors[simlabel]
        ls = 'solid'
        _label = None
        ax.plot(rcens, pmed * unitconv, color=color, linestyle=ls, linewidth=lw, 
                label=_label, path_effects=pu.getoutline(lw))
        #if ismain:
        #    ax.fill_between(rcens, plo * unitconv, phi * unitconv, color=color, 
        #                    alpha=alpha_range, linestyle=ls,
        #                    linewidth=0.5)
        #else:
        ax.plot(rcens, phi * unitconv, color=color, 
                alpha=1., linestyle='dashed',
                linewidth=1.2)
        if plottype == 'losvel':
            ax.plot(rcens, plo * unitconv, color=color, 
                    alpha=1., linestyle='dashed',
                    linewidth=1.2)
        else:
            ax.plot(rcens, plo * unitconv, color=color, 
                alpha=1., linestyle='dotted',
                linewidth=1.)
            
    data_bur = bva.readdata_b19(nsigma=1.)
    cosmopars_bur = {'h': 0.677, 'omegam': 0.31, 'omegalambda': 0.69}
    def hmfunc(x):
        csm = cosmopars_bur.copy()
        csm.update({'z': x.zgal, 'a': 1. / (1. + x.zgal)})
        mv = cu.mvir_from_rvir(x.rvir_kpc * 1e-3 * c.cm_per_mpc, 
                               csm, meandef='200m')
        return mv / c.solar_mass
    data_bur = data_bur.assign(Mvir_Msun=lambda x: hmfunc(x))
    if datafieldsels is not None:
        datasels = []
        for seltuples in datafieldsels:
            datasel = np.ones((len(data_bur),), dtype=bool)
            for seltuple in seltuples:
                field = seltuple[0]
                minv = seltuple[1]
                maxv = seltuple[2]
                #data_bur = data_bur[data_bur[field] >= minv]
                #data_bur = data_bur[data_bur[field] <= maxv]
                datasel &= data_bur[field] >= minv
                datasel &= data_bur[field] <= maxv
            datasels.append(datasel)
        data_bur = data_bur[datasels[1]]
        datasel_show = datasels[0][datasels[1]]
            
    for axi, (ax, axlabel) in enumerate(zip(axes, axlabels)):
        ax.set_title(sl.plotlabel_from_physlabel[axlabel], fontsize=fontsize)
        ax.set_xlabel(xlabel, fontsize=fontsize)
        if axi == 0:
            ax.set_ylabel(ylabel, fontsize=fontsize)
            _label = 'Burchett+19'
            _ullabel = 'Burchett+19 (UL)'
        else:
            _label = None
            _ullabel = None
        ax.tick_params(labelsize=fontsize - 1., direction='in', which='both',
                       top=True, right=True, labelleft=axi == 0)
        if plottype == 'coldens':
            addcoldata(ax, data_bur, labelmeas=_label, labelul=_ullabel,
                       datasel=datasel_show)
        elif plottype == 'abslosvel':
            addveldata(ax, data_bur, label=_label, absvals=True,
                       datasel=datasel_show)
        elif plottype == 'losvel':
            addveldata(ax, data_bur, label=_label, absvals=False,
                       datasel=datasel_show)
    ylims = [ax.get_ylim() for ax in axes]
    ymax = min([yl[1] for yl in ylims])
    ymin = max([yl[0] for yl in ylims])
    if plottype == 'coldens':
        ymin = min([yl[0] for yl in ylims])
        ymin = max(ymin, 12.5)
    elif plottype == 'abslosvel':
        ymin = 0.
    [ax.set_ylim((ymin, ymax)) for ax in axes]

    hlist = []
    for ax in axes:
        _h, _ = ax.get_legend_handles_labels()
        hlist = hlist + _h
    handles1 = [mlines.Line2D((), (), linewidth=lw_main, linestyle='solid',
                            label='FIRE median', color='black'),
                #mpatch.Patch(label='FIRE perc. 10-90', linewidth=0.5, 
                #             color='black', alpha=alpha_range)
                ]
    if plottype in ['coldens', 'abslosvel']:
        handles1 = handles1 + \
                   [mlines.Line2D((), (), linewidth=lw_main, 
                                  linestyle='dashed',
                                  label='FIRE 90%', color='black'),
                    mlines.Line2D((), (), linewidth=lw_main, 
                                  linestyle='dotted',
                                  label='FIRE 10%', color='black')]
    elif plottype == 'losvel':
        handles1 = handles1 + \
                   [mlines.Line2D((), (), linewidth=lw_main, 
                                  linestyle='dotted',
                                  label='FIRE 10, 90%', color='black')]
    handles2 = [mlines.Line2D((), (), linewidth=lw_main, 
                                  linestyle='solid',
                                  label=ic, color=colors[ic])
                for ic in icusedlist]

    lax.axis('off')
    if numcols == 3:
        nc_bw = 1
        nc_col = 3
    elif numcols == 4:
        nc_bw = 2
        nc_col = 4
    l1 = lax.legend(handles=handles1 + hlist, fontsize=fontsize, ncol=nc_bw,
               loc='upper left')
    lax.legend(handles=handles2, fontsize=fontsize, ncol=nc_col,
               loc='upper right')
    lax.add_artist(l1)
    
    if ne8_colsel is not None:
        #seltitle = ('$\\log_{10} \\, \\mathrm{N}(\\mathrm{Ne \\, VIII})'
        #            '\\; [\\mathrm{cm}^{-2}] \\geq'
        #            f' {ne8_colsel[0]:.1f}$')
        seltitle = ('$\\mathrm{Ne \\, VIII} \\geq '
                    f'{ne8_colsel[0]:.1f}$')
        axes[1].text(0.95, 0.95, seltitle, fontsize=fontsize,
                     horizontalalignment='right', verticalalignment='top',
                     transform=axes[1].transAxes)
    if outname is not None:
        plt.savefig(outname, bbox_inches='tight')

def plotsets_ne8_burchett19(hsel='all', masscomp='halo_recalc'):
    mdir = '/projects/b1026/nastasha/maps/vdopmaps_all2/'
    filen_temp = ('vdoplos_by_coldens_Ne8_{simname}_snap{snapnum}'
                  '_shrink-sph-cen_BN98_depth_2.0rvir_{pax}-proj_v3.hdf5')
    dcrange_m, dcrange_z = bds.plotMz_burchett_etal_2019(hset=hsel, 
                                                         masscomp=masscomp)
    rbins_pkpc_m12 = np.linspace(0., 450., 50)
    rbins_pkpc_m13 = np.linspace(0., 600., 50)
    rbins = {'m12': rbins_pkpc_m12,
             'm13': rbins_pkpc_m13}
    simnames_all = {'m12': sl.m12_sr_all2 + sl.m12_hr_all2 + sl.m12_f2md,
                    'm13': sl.m13_sr_all2 + sl.m13_hr_all2}
    simnames = dict()
    for key in simnames_all:
        _sns = simnames_all[key].copy()
        for sn in sl.buglist1:
            if sn in _sns:
                _sns.remove(sn)
        if hsel == 'all':
            simnames[key] = _sns
        elif hsel == 'clean':
            ics = [sn.split('_')[0] for sn in _sns]
            uniqueics = np.unique(ics)
            icsel = np.array([sum([_ic == ic for _ic in ics]) == 3 
                              for ic in uniqueics])
            ics_incl = uniqueics[icsel]
            simnames[key] = [sn for sn in _sns 
                             if sn.split('_')[0] in ics_incl]
    
    outdir = '/projects/b1026/nastasha/imgs/datacomp/'
    ne8_colsels = [None, (12.5, np.inf), (13.0, np.inf), (13.5, np.inf)]
    for mset in ['m12', 'm13']:
        if masscomp == 'halo':
            datafieldsels = [[('Mvir_Msun',) + _dcrange_m[mset],
                              ('zgal',) + _dcrange_z[mset]]
                             for _dcrange_m, _dcrange_z 
                             in zip(dcrange_m, dcrange_z)]
        elif masscomp == 'halo_recalc':
            datafieldsels = [[('logmvir_msun_bestest',) + _dcrange_m[mset],
                              ('zgal',) + _dcrange_z[mset]]
                              for _dcrange_m, _dcrange_z 
                             in zip(dcrange_m, dcrange_z)]
        elif masscomp == 'stellar':
            datafieldsels = [[('log_Mstar_Msun',) + _dcrange_m[mset],
                              ('zgal',) + _dcrange_z[mset]]
                              for _dcrange_m, _dcrange_z 
                             in zip(dcrange_m, dcrange_z)]
        print(datafieldsels)
        for plottype in ['coldens', 'abslosvel', 'losvel']:
            if plottype in ['abslosvel', 'losvel']:
                for ne8_colsel in ne8_colsels:
                    cstr = ('' if ne8_colsel is None else 
                            f'_Ne8_qe_{ne8_colsel[0]:.1f}')
                    cstr = cstr.replace('.', 'p')
                    outname = outdir + (f'{plottype}_Ne8comp_{mset}_{hsel}2'
                                        f'_{masscomp}mass_sel{cstr}_v2.pdf')
            
                    cdprof_ne8_burchett19(mdir + filen_temp, simnames[mset], 
                                         rbins[mset],
                                         showscatter='clean',
                                         datafieldsels=datafieldsels,
                                         outname=outname,
                                         plottype=plottype, 
                                         ne8_colsel=ne8_colsel,
                                         inclf2md=mset=='m12')
            else:
                outname = outdir + (f'{plottype}_Ne8comp_{mset}_{hsel}2'
                                        f'_{masscomp}mass_sel_v3.pdf')
            
                cdprof_ne8_burchett19(mdir + filen_temp, simnames[mset], 
                                      rbins[mset],
                                      showscatter='clean',
                                      datafieldsels=datafieldsels,
                                      outname=outname,
                                      plottype=plottype,
                                      inclf2md=mset=='m12')
