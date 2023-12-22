'''
uses Jonathan Stern's cooling flow package to set up an analytical
halo model,
then calculates ion profiles from the Ploeckinger & Schaye (2020) 
tables
'''

import h5py
import numpy as np
import sys
import scipy.interpolate as spi

import fire_an.ionrad.ion_utils as iu
import fire_an.utils.constants_and_units as c
import fire_an.utils.cosmo_utils as cu
import fire_an.utils.math_utils as mu
import fire_an.utils.opts_locs as ol
import fire_an.utils.h5utils as h5u
import fire_an.mstar_mhalo.loader_smdpl_sfr as lds

sys.path.insert(1, ol.path_jscoolingflow)
import cooling_flow.cooling_flow as cf
import cooling_flow.WiersmaCooling as wcool
import cooling_flow.HaloPotential as halopot

#outdir_profiles = ('/Users/nastasha/ciera/projects_lead/fire3_ionabs/'
#                    'analytical/')
outdir_profiles = '/projects/b1026/nastasha/imgs/analytical/savedprof/'
# Planck 2015 from astropy, used in Jonathan Stern's model
cosmo_base = {'h': 0.6774, 'omegam': 0.3075, 'omegab': 0.0486}
cosmo_base['omegalambda'] = 1. - cosmo_base['omegam']


def get_sfrs_mh(logmhs_msun, z=0.75, percentiles=(0.16, 0.5, 0.84)):
    histobj = lds.SFRHMhists(np.array([z]))
    sfrs_tab, mhs_tab = histobj.getperc_sfrmh(z, mode='mhtosfr', 
                                              percvals=np.array(percentiles))
    out = [[mu.linterpsolve(mhs_tab, sfrs_tab_perc, mh_this) 
            for sfrs_tab_perc in sfrs_tab]
           for mh_this in logmhs_msun]
    return np.array(out)

def solutionset(logmvirs_msun, redshift, mdotperc=(0.16, 0.5, 0.84), 
                zsol=0.3, plind=-0.1):
    '''
    get density/temperature solutions for a given halo mass set (BN98
    halo masses), mass flow rate (mdot), metallicity (zsol), 
    v_circ slope (plind)

    plind: float
        power law index for the v_c profile
    zsol: float
        metallicity [solar units]
    '''
    mvirs_msun = 10**logmvirs_msun
    cosmopars = cosmo_base.copy()
    cosmopars['z'] = redshift
    cosmopars['a'] = 1. / (1. + redshift)
    rvirs_cm = cu.rvir_from_mvir(mvirs_msun * c.solar_mass,
                                  cosmopars, meandef='BN98')
    rvirs_kpc = rvirs_cm / (c.cm_per_mpc * 1e-3)
    vcs_cmps = np.sqrt(c.gravity * mvirs_msun * c.solar_mass / rvirs_cm)
    
    mdots = 10**get_sfrs_mh(logmvirs_msun, z=redshift, percentiles=mdotperc)

    potentials = [halopot.PowerLaw(plind, vc_cmps * cf.un.cm / cf.un.s, 
                                   rvir_kpc * cf.un.kpc)
                  for vc_cmps, rvir_kpc in zip(vcs_cmps, rvirs_kpc)]
    cooling = wcool.Wiersma_Cooling(zsol, redshift)
    # want to shoot from Rcirc, since the halos considered here will
    # generally be fully virialized. (The simulated ones sure seem to
    # be.)
    solutions = {}
    for lmv, potential, mdotsub in zip(logmvirs_msun, potentials, mdots):
        print(lmv)
        rcirc = 0.02 * potential.Rvir # inner stalled radius
        # allow +-2 Rvir los integration of ion density profiles
        # to impact parameter 2 Rvir from center
        rmax = 10. * potential.Rvir # np.sqrt(2) * 2.
        solutions[lmv] = {}
        for mdot in mdotsub:
            #print(rcirc, rmax)
            #print(potential.vc(rcirc))
            #print(potential.vc(rmax))
            solution = cf.shoot_from_R_circ(potential, cooling, 
                rcirc, mdot * cf.un.Msun / cf.un.yr, rmax, 
                v0=1. * cf.un.km / cf.un.s, max_step=0.1, 
                T_low=1e4 * cf.un.K, T_high=3e7 * cf.un.K,
                tol=1e-6, epsilon=0.1, terminalUnbound=True,
                pr=True, return_all_results=False)
            solutions[lmv][mdot] = solution
    return solutions

def findsolution_mdot_rsonic(logmvir_msun, mdot_tar_msunpyr, redshift,
                             mdot_reltol=1e-2,
                             zsol=0.3, plind=-0.1, R_sonic0_kpc=10.,
                             filen_out=None, grpn_out=None,
                             ion='Ne8', pmdot=None):
    '''
    ion: str
        col. dens. profile calculated for this based on the solution
    pmdot: float
        not actually used to calculate anything, just for storing the
        value
    '''
    if filen_out is not None:
        with h5py.File(filen_out) as fo:
            if grpn_out in fo:
                raise RuntimeError(f'target grpn_out {grpn_out} already'
                                   f'exists in filen_out {filen_out}')
    mvir_msun = 10**logmvir_msun
    cosmopars = cosmo_base.copy()
    cosmopars['z'] = redshift
    cosmopars['a'] = 1. / (1. + redshift)
    rvir_cm = cu.rvir_from_mvir(mvir_msun * c.solar_mass,
                                cosmopars, meandef='BN98')
    rvir_kpc = rvir_cm / (c.cm_per_mpc * 1e-3)
    vc_cmps = np.sqrt(c.gravity * mvir_msun * c.solar_mass / rvir_cm)

    potential = halopot.PowerLaw(plind, vc_cmps * cf.un.cm / cf.un.s, 
                                 rvir_kpc * cf.un.kpc)
    cooling = wcool.Wiersma_Cooling(zsol, redshift)
    max_step = 0.1 #lowest resolution of solution in ln(r)
    #inner radius of supersonic part of solution
    R_min    = min(0.1 * cf.un.kpc, 1e-5 * potential.Rvir) 
    # outer radius of subsonic region
    R_max    = 10. * potential.Rvir
    todoc = {'max_step': max_step,
             'R_min_kpc': R_min.to('kpc'),
             'R_max_kpc': R_max.to('kpc'),
             'target_mdot_msunperyr': mdot_tar_msunpyr,
             'mdot_reltol': mdot_reltol,
             'logMvir_Msun_BN98': logmvir_msun,
             'Z_solar': zsol,
             'plind_vc': plind,
             'cosmopars': cosmopars,
             'ion': ion,
             'mdot_percentile_at_Mvir': pmdot}
    kwa_rsonshoot = {'tol': 1e-6,
                     'epsilon': 1e-3,
                     'dlnMdlnRInit': -1,
                     'return_all_results': False,
                     'terminalUnbound': True,
                     'pr': False,
                     'calcInwardSolution':True,
                     'minT': 2e4,
                     'x_low': 1e-5,
                     'x_high': 1.}
    Rs_max = 0.7 * R_max
    Rs_min = 1.3 * R_min
    Rs_mid = R_sonic0_kpc * cf.un.kpc
    mdot_tar = mdot_tar_msunpyr * cf.un.Msun / cf.un.yr
    # search strategy based on Imran's 
    # (not copied because I'm not trying to match any FIRE sims here)

    ## gauge initial solutions: Mdot increases/decreases with R_sonic
    # raises error if not clearly monotonic
    sol_mid = cf.shoot_from_sonic_point(potential, cooling, Rs_mid,
                                        R_max,R_min, max_step=max_step,
                                        **kwa_rsonshoot)
    sol_max = cf.shoot_from_sonic_point(potential, cooling, Rs_max,
                                        R_max,R_min, max_step=max_step,
                                        **kwa_rsonshoot)
    sol_min = cf.shoot_from_sonic_point(potential, cooling, Rs_min,
                                        R_max,R_min, max_step=max_step,
                                        **kwa_rsonshoot)
    mdot_rsmid = sol_mid.Mdot
    mdot_rsmax = sol_max.Mdot
    mdot_rsmin = sol_min.Mdot
    if mdot_rsmin < mdot_rsmid and mdot_rsmax > mdot_rsmid:
        mdotincrwithrs = True
        if not (mdot_tar <= mdot_rsmax and mdot_tar >= mdot_rsmin):
            msg = (f'for target Mdot {mdot_tar_msunpyr} Msun/yr, '
                   f'log halo mass {logmvir_msun} Msun, '
                   f'Rs_min = R_min = {R_min.to("kpc")}, ',
                   f'Rs_max = R_max = {R_max.to("kpc")}, '
                   f'the Mdot range {mdot_rsmin} -- {mdot_rsmax}'
                   ' does not contain the desired value')
            raise RuntimeError(msg)
    elif mdot_rsmax < mdot_rsmid and mdot_rsmin > mdot_rsmid:
        mdotincrwithrs = False
        if not (mdot_tar >= mdot_rsmax and mdot_tar <= mdot_rsmin):
            msg = (f'for target Mdot {mdot_tar_msunpyr} Msun/yr, '
                   f'log halo mass {logmvir_msun} Msun, '
                   f'Rs_max = R_max = {Rs_max.to("kpc")}, '
                   f'Rs_min = R_min = {Rs_min.to("kpc")}, '
                   f'the Mdot range {mdot_rsmax} -- {mdot_rsmin}'
                   ' does not contain the desired value')
            raise RuntimeError(msg)
    else:
        msg = (f'for target Mdot {mdot_tar_msunpyr} Msun/yr, '
               f'log halo mass {logmvir_msun} Msun, '
               f'Rs_min = {Rs_min.to("kpc")} '
               f'Mdot = {mdot_rsmin},\n'
               f'Rs_mid = {Rs_mid.to("kpc")} '
               f'Mdot = {mdot_rsmid},\n'
               f'Rs_max = {Rs_max.to("kpc")} gives '
               f'Mdot = {mdot_rsmax}:\n'
               'Mdot does not appear to be monotonic in R_sonic')
        raise RuntimeError(msg)
    
    maxIter = 200
    for i in range(maxIter):
        if ((mdot_tar * (1 - mdot_reltol) < mdot_rsmid) 
                and (mdot_tar * (1 + mdot_reltol) > mdot_rsmid)):
            # solution found!
            break
        sol_rsmid = cf.shoot_from_sonic_point(potential, cooling, Rs_mid,
                                              R_max, R_min, max_step=max_step,
                                              **kwa_rsonshoot)
        if ((sol_mid.Mdot <= mdot_tar and mdotincrwithrs)
                or (sol_mid.Mdot > mdot_tar and not mdotincrwithrs)):
            Rs_max = Rs_mid
        elif ((sol_mid.Mdot > mdot_tar and mdotincrwithrs)
              or (sol_mid.Mdot <= mdot_tar and not mdotincrwithrs)):
            Rs_min = Rs_mid
        Rs_mid = (Rs_min * Rs_max)**0.5 # log average Rs
    if i == maxIter - 1:
        print(f'No solution found in {maxIter} iterations for '
              f'logmvir {logmvir_msun}, '
              f'fmdot_tar_msunperyr {mdot_tar_msunpyr}. '
              f'The last iteration had Mdot = {sol_rsmid.Mdot}')
        return None
    solution = sol_rsmid
    
    fcgm = calc_cgmfrac(solution, 10**logmvir_msun)
    rvir_cm = solution.potential.Rvir.to('cm').value
    truncate_inner_cm = 0.09 * rvir_cm
    impactpars_cm = np.arange(0.1, 2.02, 0.05) * rvir_cm
    lossample_cm = np.arange(-2., 2.002, 0.005) * rvir_cm
    coldens_cm2 = calcionprof(solution, ion, redshift, zsol,
                              impactpars_cm, lossample_cm, 
                              truncate_inner_cm)
    with h5py.File(filen_out, 'a') as f:
        grp = f.create_group(grpn_out)
        grp.attrs.create('mdot_MsunperYr', solution.Mdot)
        grp.attrs.create('mdot_percentile_at_Mvir', pmdot)
        grp.attrs.create('failed', False)
        h5u.savedict_hdf5(grp, todoc)
        sgrp = grp.create_group('kwargs_shoot_from_sonic_point')
        h5u.savedict_hdf5(sgrp, kwa_rsonshoot)

        grp.create_dataset('R_kpc', data=solution.Rs().to('kpc').value)
        grp.create_dataset('T_K', data=solution.Ts().to('K').value)
        grp.create_dataset('nH_cm3', data=solution.nHs().to('cm**-3').value)
        
        grp.attrs.create('fCGM', fcgm)
        grp.attrs.create('Rvir_cm', rvir_cm)
        sgrp = grp.create_group(f'coldens_{ion}')
        sgrp.create_dataset('impactpar_cm', data=impactpars_cm)
        sgrp.create_dataset('coldens_cm2', data=coldens_cm2)
    return solution, sol_rsmid.to('kpc'), todoc    

def findsolutions_mdot_rsonic(logmvirs_msun, pmdots, redshift,
                              zsols=(0.3,), plinds=(-0.1,),
                              filen_out=None):
    '''
    Use Jonathan Stern's shoot_from_rsonic method to find a cooling
    flow model that yields a given inflow rate Mdot.
    Iterates over logmvirs_msun, mdots_msunperyr pairs, assuming the
    last pair's sonic radius is a good starting point for the next 
    one.
    '''

    mh_sfr = get_sfrs_mh(logmvirs_msun, z=redshift, percentiles=pmdots)
    print(logmvirs_msun)
    print(mh_sfr)
    if filen_out is not None:
        filen_out = outdir_profiles + filen_out
    
    _rs0_kpc = 1.1
    for zsol in zsols:
        for plind in plinds:
            for sfri, pmdot in enumerate(pmdots):
                rs0_kpc = _rs0_kpc # reset for new Mvir loop
                for mvi, mvir in enumerate(logmvirs_msun):
                    sfr = 10**mh_sfr[mvi, sfri]
                    grpn_out = (f'z{redshift:.2f}_Zsolar{zsol:.2e}'
                                f'_vcplind{plind:.2f}_mdotperc{pmdot:.3f}'
                                f'_logmvirMsun{mvir:.2f}')
                    print(grpn_out) # progess note
                    solution, rs_sol, todoc = findsolution_mdot_rsonic(
                        mvir, sfr, redshift, mdot_reltol=1e-2, zsol=zsol, 
                        plind=plind, R_sonic0_kpc=rs0_kpc, 
                        filen_out=filen_out, grpn_out=grpn_out,
                        ion='Ne8', pmdot=pmdot)
                    # for small Mvir increments, should be a good start
                    rs0_kpc = rs_sol 

def calc_cgmfrac(solution, mvir_msun):
    '''
    get the CGM gas mass fraction. (Inflow rates as an input parameter
    seem uncertain, but gas fractions I can check.)
    built-in Mgas includes all radii, I want 0.1 -- 1 Rvir
    assumes there are at least two solution points before and after
    the radial range edges
    '''
    _rmin_rvir = 0.1
    _rmax_rvir = 1.0
    rmin = _rmin_rvir * solution.potential.Rvir
    rmax = _rmax_rvir * solution.potential.Rvir
    rs = solution.Rs()
    rimin = np.searchsorted(rs, rmin, side='right')
    rimax = np.searchsorted(rs, rmax, side='left')
    frac_rimin_m1 = (rmin - rs[rimin - 1]) / (rs[rimin] - rs[rimin - 1])
    frac_rimax = (rs[rimax] - rmax) / (rs[rimax] - rs[rimax - 1])
    print(frac_rimin_m1, frac_rimax)

    rsel = slice(rimin - 1, rimax + 1, None)
    rsel_diff = slice(rimin - 2, rimax + 2, None)
    drs = 0.5 * (rs[rsel_diff][2:] - rs[rsel_diff][:-2])
    print(drs)
    drs[0] = drs[0] * frac_rimin_m1
    drs[-1] = drs[-1] * frac_rimax
    print(rs[rsel])
    dms = 4. * np.pi * rs[rsel]**2 * drs * solution.rhos()[rsel]
    mtot = np.sum(dms)
    return mtot.to('Msun') / (mvir_msun * cf.un.Msun)

def calcionprof(solution, ion, redshift, zsol,
                impactpars_cm, lossample_cm, 
                truncate_inner_cm):
    r_cm = solution.Rs().to('cm').value 
    logT_K = np.log10(solution.Ts().to('K').value)
    lognH_cm3 = np.log10(solution.nHs().to('cm**-3').value)
    tab = iu.Linetable_PS20(ion, redshift, emission=False,
                            lintable=True)
    logZ = np.log10(zsol * tab.solarZ) * np.ones(len(r_cm))
    interpdct = {'logT': logT_K, 'lognH': lognH_cm3, 'logZ': logZ}
    ionfrac = tab.find_ionbal(interpdct, log=False)
    eltabund = tab.find_assumedabundance(interpdct, log=False)
    iondens = ionfrac * eltabund * 10**lognH_cm3
    rimin = np.where(r_cm > truncate_inner_cm)[0][0]
    _iondens_prof = spi.interp1d(np.log10(r_cm), np.log10(iondens), 
                                 kind='linear',
                                 fill_value=0.)
    lid0 = _iondens_prof(np.log10(truncate_inner_cm))
    _r_cm = np.append(truncate_inner_cm, r_cm[rimin:])
    _liondens = np.append(lid0, np.log10(iondens)[rimin:])
    liondens_prof = spi.interp1d(np.log10(_r_cm), _liondens, 
                                 kind='linear',
                                 fill_value=0.)
    loscens_cm = 0.5 * (lossample_cm[1:] + lossample_cm[:-1])
    logr3d_cm = 0.5 * np.log10((impactpars_cm[:, np.newaxis]/1e21)**2 +
                               (loscens_cm[np.newaxis, :]/1e21)**2) \
                + 21.
    dl = lossample_cm[1:] - lossample_cm[:-1]
    iondens = 10**liondens_prof(logr3d_cm)
    coldens = np.sum(iondens * dl[np.newaxis, :], axis=1)
    #print('coldens: ', coldens)
    return coldens

def savesol(solution, ion, redshift, zsol, plind, mdot, pmdot, 
            logmvir_msun, outfilen):
    grpn = (f'z{redshift:.2f}_Zsolar{zsol:.2e}_vcplind{plind:.2f}'
            f'_mdotperc{pmdot:.3f}_logmvirMsun{logmvir_msun:.2f}')
    if solution is None:
        with h5py.File(outfilen, 'a') as f:
            if grpn in f:
                raise RuntimeError(f'group already stored in {outfilen}:'
                                   f' {grpn}')            
            grp = f.create_group(grpn)
            grp.attrs.create('failed', True)
        return None

    fcgm = calc_cgmfrac(solution, 10**logmvir_msun)
    rvir_cm = solution.potential.Rvir.to('cm').value
    truncate_inner_cm = 0.09 * rvir_cm
    impactpars_cm = np.arange(0.1, 2.02, 0.05) * rvir_cm
    lossample_cm = np.arange(-2., 2.002, 0.005) * rvir_cm
    coldens_cm2 = calcionprof(solution, ion, redshift, zsol,
                              impactpars_cm, lossample_cm, 
                              truncate_inner_cm)
    with h5py.File(outfilen, 'a') as f:
        if grpn in f:
            raise RuntimeError(f'group already stored in {outfilen}: {grpn}')
        grp = f.create_group(grpn)
        grp.attrs.create('redshift', redshift)
        grp.attrs.create('Z_solar', zsol)
        grp.attrs.create('vcplind', plind)
        grp.attrs.create('mdot_MsunperYr', mdot)
        grp.attrs.create('mdot_percentile_at_Mvir', pmdot)
        grp.attrs.create('failed', False)
        grp.attrs.create('logMvir_Msun_BN98', logmvir_msun)
        grp.create_dataset('R_kpc', data=solution.Rs().to('kpc').value)
        grp.create_dataset('T_K', data=solution.Ts().to('K').value)
        grp.create_dataset('nH_cm3', data=solution.nHs().to('cm**-3').value)
        
        grp.attrs.create('fCGM', fcgm)
        grp.attrs.create('Rvir_cm', rvir_cm)
        sgrp = grp.create_group(f'coldens_{ion}')
        sgrp.create_dataset('impactpar_cm', data=impactpars_cm)
        sgrp.create_dataset('coldens_cm2', data=coldens_cm2)
    return None

# test1: col. dens. values are negative and of unreasonably 
#        large magnitude. R_kpc, T_K, nH_cm3 look ok.
# test2: issue seems to have been with log/lin ion fracs.
# note that lower Mvir values do not give a solution; this will
# be before inner CGM virialization
# test3: looks ok
# set1: rmax = np.sqrt(2) * 2. * potential.Rvir 
#       T_low=1e4 * cf.un.K, 
#       T_high=1e8 * cf.un.K,
#       tol=1e-6, epsilon=0.1, terminalUnbound=True,
#       pr=True, return_all_results=False
# set2: same as set1, but rmax = 10. * potential.Rvir 
def runsolsgrid(outfilen='set1_jsmodel.hdf5'):
    logmvirs_msun = np.arange(11.0, 13.65, 0.1)
    #redshifts = np.arange(0.5, 1.05, 0.1)
    redshifts = np.array([0.75])
    #zs_sol = np.array([0.1, 0.2, 0.5, 1.])
    zs_sol = np.array([0.1, 0.3, 1.])
    #plinds = np.array([0., -0.1, -0.2, -0.5])
    plinds = np.array([0., -0.1, -0.2])
    #mdots = np.array([0.01, 0.03, 0.1, 0.3, 1., 3., 10., 30., 100.])
    pmdots = np.array([0.16, 0.5, 0.84])
    
    for redshift in redshifts:
        for zsol in zs_sol:
            for plind in plinds:
                sols = solutionset(logmvirs_msun, redshift, 
                                    mdotperc=pmdots, 
                                    zsol=zsol, plind=plind)
                for mhsol in sols:
                    sfsols = list(sols[mhsol].keys())
                    sfsols.sort()
                    for sfsol, pmdot in zip(sfsols, pmdots):
                        savesol(sols[mhsol][sfsol], 'Ne8', redshift, zsol,
                                plind, sfsol, pmdot, mhsol,
                                outdir_profiles + outfilen)

def main(i):
    if i == 0:
        # solutions don't seem to want to get Mdot as low as perc. 16
        # in an 11.0 halo
        filen_out = 'test5_jsmodel.hdf5'
        redshift = 0.75
        logmvirs_msun = np.arange(11., 13.6, 0.5)
        pmdots = (0.16, 0.5, 0.84)
        findsolutions_mdot_rsonic(logmvirs_msun, pmdots, redshift,
                                  zsols=(0.3,), plinds=(-0.1,),
                                  filen_out=filen_out)
    print(f'Done running solution-finding loop {i}')

if __name__ == '__main__':
    if len(sys.argv) > 1:
        arg = int(sys.argv[1])
        main(arg)
        sys.exit(0)
    else:
        print('Please specify an integer index argument')
        sys.exit(1)
    

