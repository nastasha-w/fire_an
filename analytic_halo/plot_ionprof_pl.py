
import matplotlib.cm as mcm
import matplotlib.colors as mcolors
import matplotlib.gridspec as gsp
import matplotlib.pyplot as plt
import numpy as np

import fire_an.analytic_halo.model_ionprof_pl as mip
import fire_an.makeplots.plot_utils as pu
import fire_an.utils.constants_and_units as c

outdir = '/Users/nastasha/ciera/projects_lead/fire3_ionabs/analytical/'
def plot_coldensprof(ion, pli):
    impactpars_kpc = np.linspace(5., 450., 50)
    logmvirs_msun = np.arange(11., 14.1, 0.2)
    fcgm = 0.9
    z_sol = 0.3
    redshifts = [0.5, 0.75, 1.0]

    vmin = logmvirs_msun[0]
    vmax = logmvirs_msun[-1]
    cmap = mcm.get_cmap('viridis')
    norm = mcolors.Normalize(vmin=vmin, vmax=vmax)

    fig = plt.figure(figsize=(11.5, 3.))
    grid = gsp.GridSpec(ncols=4, nrows=1, wspace=0.0, 
                        width_ratios=(10., 10., 10., 1.))
    axes = [fig.add_subplot(grid[i]) for i in range(3)]
    cax = fig.add_subplot(grid[3])
    fontsize = 12
    linewidth = 1.5
    path_effects = pu.getoutline(linewidth)

    
    for zi, redshift in enumerate(redshifts):
        ax = axes[zi]
        doleft = zi == 0
        ax.set_xlabel('$\\mathrm{r}_{\\perp} \\; [\\mathrm{pkpc}]$',
                  fontsize=fontsize)
        if doleft:
            ax.set_ylabel('$\\log_{10} \\, \\mathrm{N}(\\mathrm{Ne\\,VIII})'
                          '\\; [\\mathrm{cm}^{-2}]$',
                          fontsize=fontsize)
        ax.tick_params(which='both', direction='in', labelsize=fontsize - 1.,
                       top=True, right=True, labelleft=doleft)

        for lmv in logmvirs_msun:
            hmod = mip.PLmodel(10**lmv, redshift, fcgm, z_sol, pli)
            cvs = hmod.coldensprof(ion, impactpars_kpc)
            ax.plot(impactpars_kpc, np.log10(cvs), 
                    color=cmap((lmv - vmin) / (vmax - vmin)),
                    linewidth=linewidth, path_effects=path_effects)
    ylims = [ax.get_ylim() for ax in axes]
    ymin = min([ylim[0] for ylim in ylims])
    ymax = max([ylim[1] for ylim in ylims])
    [ax.set_ylim((ymin, ymax)) for ax in axes]

    plt.colorbar(mcm.ScalarMappable(norm=norm, cmap=cmap), cax=cax,
                 orientation='vertical')
    cax.set_ylabel('$\\log_{10} \\, \\mathrm{M}_{\\mathrm{vir}}'
                   '\\; [\\mathrm{M}_{\\odot}]$',
                   fontsize=fontsize)
    cax.tick_params(labelsize=fontsize - 1.)
    
    outname = f'cdprof_analytical_s19_{ion}_plmod_plivc_{pli:.2f}'
    outname = outname.replace('.', 'p')
    plt.savefig(outdir + outname + '.pdf', bbox_inches='tight')
