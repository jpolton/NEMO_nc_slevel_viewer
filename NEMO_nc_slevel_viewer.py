import matplotlib.pyplot as plt

from datetime import datetime,timedelta
import numpy as np
from netCDF4 import Dataset,date2num,num2date
import pdb,os,sys
import os.path
import xarray
import glob
import cftime
import matplotlib
import csv

from NEMO_nc_slevel_viewer_lib import set_perc_clim_pcolor, get_clim_pcolor, set_clim_pcolor,set_perc_clim_pcolor_in_region,get_colorbar_values,scale_color_map,lon_lat_to_str
from NEMO_nc_slevel_viewer_lib import interp1dmat_wgt, interp1dmat_create_weight, interp_UV_vel_to_Tgrid
from NEMO_nc_slevel_viewer_lib import rotated_grid_from_amm15, reduce_rotamm15_grid,regrid_2nd_thin_params,regrid_iijj_ew_ns
from NEMO_nc_slevel_viewer_lib import nearbed_int_index_val
from NEMO_nc_slevel_viewer_lib import pea_TS
from NEMO_nc_slevel_viewer_lib import load_nc_dims,load_nc_var_name_list
from NEMO_nc_slevel_viewer_lib import field_gradient_2d,weighted_depth_mean_masked_var
from NEMO_nc_slevel_viewer_lib import vector_div, vector_curl,sw_dens,reload_data_instances


from NEMO_nc_slevel_viewer_lib import reload_map_data_comb_zmeth_zindex,reload_map_data_comb_zmeth_ss_3d,reload_map_data_comb_zmeth_nb_df_zm_3d
from NEMO_nc_slevel_viewer_lib import reload_map_data_comb_zmeth_zslice,reload_map_data_comb_2d,reload_map_data_comb,reload_ew_data_comb,reload_ns_data_comb
from NEMO_nc_slevel_viewer_lib import reload_hov_data_comb,reload_ts_data_comb
from NEMO_nc_slevel_viewer_lib import regrid_2nd,grad_horiz_ns_data,grad_horiz_ew_data,grad_vert_ns_data,grad_vert_ew_data,grad_vert_hov_data
#from NEMO_nc_slevel_viewer_lib import indices_from_ginput_ax


letter_mat = ['a','b','c','d','e','f','g','h','i','j','k','l','m','n','o','p','q','r','s','t','u','v','w','x','y','z']

import time
import argparse
import textwrap

import socket
computername = socket.gethostname()
comp = 'linux'
if computername in ['xcel00','xcfl00']: comp = 'hpc'

import warnings
warnings.filterwarnings("ignore")

script_dir=os.path.dirname(os.path.realpath(__file__)) + '/'

global fname_lst, fname_lst_2nd,var

import matplotlib
matplotlib.rcParams['font.family'] = 'serif'

matplotlib.use('Qt5Agg')

def nemo_slice_zlev(fname_lst, config = 'amm7',  
    zlim_max = None,var = None,
    fname_lst_2nd = None,config_2nd = None,
    U_fname_lst = None,V_fname_lst = None,
    U_fname_lst_2nd = None,V_fname_lst_2nd = None,
    thin = 1,thin_2nd = 1, 
    thin_x0=0,thin_x1=None,thin_y0=0,thin_y1=None,
    thin_files = 1,thin_files_0 = 0,thin_files_1 = None, 
    xlim = None, ylim = None, tlim = None, clim = None,
    ii = None, jj = None, ti = None, zz = None, 
    lon_in = None, lat_in = None, date_in_ind = None, date_fmt = '%Y%m%d',
    z_meth = None,
    secdataset_proc = 'Dataset 1',
    hov_time = True, do_cont = True, do_grad = 1,
    allow_diff_time = False,
    preload_data = False,
    ld_lst = None, ld_nctvar = 'time_counter',ld_lab_lst = '-36,-12,012,036,060,084,108,132',
    clim_sym = None, clim_pair = True,use_cmocean = False,
    fig_dir = None,fig_lab = 'figs',fig_cutout = True, 
    justplot = False, justplot_date_ind = None,justplot_z_meth_zz = None,justplot_secdataset_proc = None,
    fig_fname_lab = None, fig_fname_lab_2nd = None, 
    verbose_debugging = False):

    print('Initialise at ',datetime.now())
    init_timer = []
    init_timer.append((datetime.now(),'Starting Program'))





    th = {}
    th['df'] = thin_files
    th['f0'] = thin_files_0
    th['f1'] = thin_files_1


    
    fname_lst = fname_lst[th['f0']:th['f1']:th['df']]
    if fname_lst_2nd is not None: fname_lst_2nd = fname_lst_2nd[th['f0']:th['f1']:th['df']]
    if U_fname_lst is not None: U_fname_lst = U_fname_lst[th['f0']:th['f1']:th['df']]
    if V_fname_lst is not None: V_fname_lst = V_fname_lst[th['f0']:th['f1']:th['df']]
    if U_fname_lst_2nd is not None: U_fname_lst_2nd = U_fname_lst_2nd[th['f0']:th['f1']:th['df']]
    if V_fname_lst_2nd is not None: V_fname_lst_2nd = V_fname_lst_2nd[th['f0']:th['f1']:th['df']]

    if thin_x0 is None: thin_x0 = 0
    if thin_y0 is None: thin_y0 = 0

    if config.upper() in ['ORCA025','ORCA025EXT']: 
        if thin_y1 is None: thin_y1 = -2
    if config.upper() in ['ORCA12']: 
        if thin_y1 is None: thin_y1 = -200
        if thin_y0 is None: thin_y1 = 1000



    thin_x0_2nd=thin_x0
    thin_x1_2nd=thin_x1
    thin_y0_2nd=thin_y0
    thin_y1_2nd=thin_y1
    if config_2nd is None:
        thin_2nd=thin

    if config_2nd is not None:

        thin_x0_2nd=0
        thin_x1_2nd=None
        thin_y0_2nd=0
        thin_y1_2nd=None
        #if thin_2nd is None:
        #thin_2nd=1



    th['dx'] = thin
    th['dy'] = thin
    th['x0'] = thin_x0
    th['x1'] = thin_x1
    th['y0'] = thin_y0
    th['y1'] = thin_y1
    th['dx_2nd'] = thin_2nd
    th['dy_2nd'] = thin_2nd
    th['x0_2nd'] = thin_x0_2nd
    th['x1_2nd'] = thin_x1_2nd
    th['y0_2nd'] = thin_y0_2nd
    th['y1_2nd'] = thin_y1_2nd

    del(thin)
    del(thin_x0)
    del(thin_x1)
    del(thin_y0)
    del(thin_y1)
    del(thin_2nd)
    del(thin_x0_2nd)
    del(thin_x1_2nd)
    del(thin_y0_2nd)
    del(thin_y1_2nd)

    del(thin_files)
    del(thin_files_0)
    del(thin_files_1)


    axis_scale = 'Auto'

    if do_grad is None: do_grad = 0
    if do_cont is None: do_cont = True
    
    # For T Diff
    Time_Diff = False
    data_inst_1_Tm1,data_inst_2_Tm1 = None,None
    preload_data_ti_Tm1,preload_data_var_Tm1,preload_data_ldi_Tm1 = 0.5,'None',0.5

    if verbose_debugging:
        print('======================================================')
        print('======================================================')
        print('=== Debugging printouts: verbose_debugging = True  ===')
        print('======================================================')
        print('======================================================')

    
    #Default variable for U and V flist
    tmp_var_U, tmp_var_V = 'vozocrtx','vomecrty'


    z_meth_mat = ['z_slice','ss','nb','df','zm']

    nav_lon_varname = 'nav_lon'
    nav_lat_varname = 'nav_lat'
    time_varname = 'time_counter'

    nav_lon_var_mat = ['nav_lon'.upper(),'lon'.upper(),'longitude'.upper()]
    nav_lat_var_mat = ['nav_lat'.upper(),'lat'.upper(),'latitude'.upper()]
    time_varname_mat = ['time_counter'.upper(),'time'.upper()]


    if use_cmocean:
        
        import cmocean
        # default color map to use
        base_cmap = cmocean.cm.thermal
        scnd_cmap = cmocean.cm.balance
    else:
        base_cmap = matplotlib.cm.viridis
        scnd_cmap = matplotlib.cm.coolwarm

    col_scl = 0
    curr_cmap = base_cmap
    base_cmap_low,base_cmap_high = scale_color_map(curr_cmap)

    #pdb.set_trace()

    if clim_sym is None: clim_sym = False
    
    clim_sym_but = 0
    #clim_sym_but_norm_val = clim_sym

    # default initial indices
    if ii is None: ii = 10
    if jj is None: jj = 10
    if ti is None: ti = 0
    if zz is None: zz = 0
    if zz == 0: zi = 0
    if zi is None: zi = 0
    #pdb.set_trace()
    if fig_dir is None:

        #fig_dir = os.getcwd() + '/tmpfigs'
        fig_dir = script_dir + '/tmpfigs'
        print('fig_dir: ',fig_dir )

    #need to load lon_mat and lat_mat to implement lon_in and lat_in
    #need to load date_mat to implement date_in_ind

    # Set mode: Click or Loop
    mode = 'Click'
    loop_sleep = 0.01

    load_2nd_files = False
    # repeat if comparing two time series. 
    if fname_lst_2nd is not None:        
        load_2nd_files = True



    # if a secondary data set, give ability to change data sets. 
    secdataset_proc_list = ['Dataset 1', 'Dataset 2', 'Dat2-Dat1', 'Dat1-Dat2']
    if secdataset_proc is None: secdataset_proc = 'Dataset 1'

    if load_2nd_files == False:
        clim_pair = False
    
    if justplot is None: justplot = False


    if hov_time is None: hov_time = True

    print('thin: %i; thin_files: %i; hov_time: %s; '%(th['dx'],th['df'],hov_time))


    config_fnames_dict = {}
    config_fnames_dict[config] = {}

    
    init_timer.append((datetime.now(),'Indices set'))
    
    #pdb.set_trace()
    config_csv_fname = script_dir + 'NEMO_nc_slevel_viewer_config_%s.csv'%config.upper()
    with open(config_csv_fname, mode='r') as infile:
        reader = csv.reader(infile)
        for rows in reader :config_fnames_dict[config][rows[0]] = rows[1]


    if config_2nd is not None:
        nlon_amm7 = 297
        nlat_amm7 = 375
        nlon_amm15 = 1458
        nlat_amm15 = 1345

    if config_2nd is not None:
        config_fnames_dict[config_2nd] = {}
        config_2nd_csv_fname = script_dir + 'NEMO_nc_slevel_viewer_config_%s.csv'%config_2nd.upper()
        with open(config_2nd_csv_fname, mode='r') as infile:
            reader = csv.reader(infile)
            for rows in reader :config_fnames_dict[config_2nd][rows[0]] = rows[1]

    z_meth_default = config_fnames_dict[config]['z_meth_default']
    ncgdept = 'gdept_0'
    nce1t = 'e1t'
    nce2t = 'e2t'
    nce3t = 'e3t_0'
    ncglamt = 'glamt'
    ncgphit = 'gphit'

    if 'ncgdept' in config_fnames_dict[config].keys():ncgdept = config_fnames_dict[config]['ncgdept']
    if 'nce1t' in config_fnames_dict[config].keys():nce1t = config_fnames_dict[config]['nce1t']
    if 'nce2t' in config_fnames_dict[config].keys():nce2t = config_fnames_dict[config]['nce2t']
    if 'nce3t' in config_fnames_dict[config].keys():nce3t = config_fnames_dict[config]['nce3t']
    if 'ncglamt' in config_fnames_dict[config].keys():ncglamt = config_fnames_dict[config]['ncglamt']
    if 'ncgphit' in config_fnames_dict[config].keys():ncgphit = config_fnames_dict[config]['ncgphit']
    rootgrp_gdept = None


    
    init_timer.append((datetime.now(),'Config files read'))
        
    # depth grid file
    rootgrp_gdept = Dataset(config_fnames_dict[config]['mesh_file'], 'r', format='NETCDF4')

    init_timer.append((datetime.now(),'Gdept opened'))


    #config version specific info - mainly grid, and lat/lon info
    if config.upper() == 'AMM7':
        #grid lat lon
        lon = np.arange(-19.888889,12.99967+1/9.,1/9.)
        lat = np.arange(40.066669,65+1/15.,1/15.)

    elif config.upper() == 'GULF18':

        #grid lat lon
        lon = rootgrp_gdept.variables[ncglamt][:,0,:].ravel()
        lat = rootgrp_gdept.variables[ncgphit][:,:,0].ravel()

    if z_meth is None:
        z_meth = z_meth_default


    global rootgrp_gdept_2nd, nav_lon_2nd, nav_lat_2nd

    rootgrp_gdept_2nd = rootgrp_gdept   


    regrid_meth = 1
    regrid_params = None

    if config_2nd is not None:

        if (config.upper() in ['AMM7','AMM15']) & (config_2nd.upper() in ['AMM7','AMM15']):  
            mesh_file_2nd = config_fnames_dict[config_2nd]['mesh_file'] 
            rootgrp_gdept_2nd = Dataset(mesh_file_2nd, 'r', format='NETCDF4')

            if (config.upper() == 'AMM15') & (config_2nd.upper() == 'AMM7'):  


                lon = np.arange(-19.888889,12.99967+1/9.,1/9.)
                lat = np.arange(40.066669,65+1/15.,1/15.)


                amm_conv_dict = {}
                rootgrp = Dataset(config_fnames_dict[config]['regrid_amm7_amm15'], 'r')
                for var_conv in rootgrp.variables.keys(): amm_conv_dict[var_conv] = rootgrp.variables[var_conv][:]
                rootgrp.close()
    
                nlon_amm        = nlon_amm15
                nlat_amm        = nlat_amm15
                nlon_amm_2nd    = nlon_amm7
                nlat_amm_2nd    = nlat_amm7


            elif (config.upper() == 'AMM7') & (config_2nd.upper() == 'AMM15'):

                amm_conv_dict = {}
                rootgrp = Dataset(config_fnames_dict[config_2nd]['regrid_amm15_amm7'], 'r')
                for var_conv in rootgrp.variables.keys(): amm_conv_dict[var_conv] = rootgrp.variables[var_conv][:]
                rootgrp.close()
    
                nlon_amm        = nlon_amm7
                nlat_amm        = nlat_amm7
                nlon_amm_2nd    = nlon_amm15
                nlat_amm_2nd    = nlat_amm15

            regrid_params = regrid_2nd_thin_params(amm_conv_dict,
                th['dx_2nd'],th['x0_2nd'],th['y0_2nd'],
                nlon_amm,nlat_amm, 
                nlon_amm_2nd,nlat_amm_2nd,
                th['dx'],th['x0'],th['y0'],th['x1'],th['y1'])


    init_timer.append((datetime.now(),'config 2 params'))


    init_timer.append((datetime.now(),'xarray open_mfdataset T connecting'))
    print ('xarray open_mfdataset, Start',datetime.now())

    # open file list with xarray
    xarr_dict = {}
    xarr_dict['Dataset 1'] = {}
    xarr_dict['Dataset 2'] = {}

        
    for grid in ['T','U','V']:
        xarr_dict['Dataset 1'][grid] = []
        xarr_dict['Dataset 2'][grid] = []

    #pdb.set_trace()
    if ld_lst is None:
        nldi = 0
    else:
        if isinstance(ld_lst, str):
            ldi_ind_mat = np.array([int(ss) for ss in ld_lst.split(',')])
            nldi = ldi_ind_mat.size
        else:
            pdb.set_trace()

        if ld_lab_lst is None:
            ld_lab_mat = np.array(['%i'%(ii) for ii in ldi_ind_mat])
        else:
            ld_lab_mat = np.array(ld_lab_lst.split(','))

    if nldi == 0:
        xarr_dict['Dataset 1']['T'].append(xarray.open_mfdataset(fname_lst, combine='by_coords',parallel = True))
    else:
        for li,(ldi,ldilab) in enumerate(zip(ldi_ind_mat, ld_lab_mat)):xarr_dict['Dataset 1']['T'].append(xarray.open_mfdataset(fname_lst, combine='by_coords',parallel = True, preprocess=lambda ds: ds[{ld_nctvar:slice(ldi,ldi+1)}]))   
    ncvar_mat = [ss for ss in xarr_dict['Dataset 1']['T'][0].variables.keys()]
  
    init_timer.append((datetime.now(),'xarray open_mfdataset T connected'))

    
    # check name of lon and lat ncvar in data.
    # cycle through variables and if it is a possibnle varibable name, use it
    for ncvar in ncvar_mat: 
        if ncvar.upper() in nav_lon_var_mat: nav_lon_varname = ncvar
        if ncvar.upper() in nav_lat_var_mat: nav_lat_varname = ncvar
        if ncvar.upper() in time_varname_mat: time_varname = ncvar


    if nav_lon_varname not in ncvar_mat:
        pdb.set_trace()

    init_timer.append((datetime.now(),'xarray open_mfdataset UV connecting'))
    print ('xarray open_mfdataset, Finish',datetime.now())
    #Add baroclinic velocity magnitude
    UV_vec = False
    if (U_fname_lst is not None) & (V_fname_lst is not None):
        UV_vec = True
        
        if nldi == 0 :
            xarr_dict['Dataset 1']['U'].append(xarray.open_mfdataset(U_fname_lst, combine='by_coords',parallel = True))
            xarr_dict['Dataset 1']['V'].append(xarray.open_mfdataset(V_fname_lst, combine='by_coords',parallel = True))
        else:
            for li,(ldi,ldilab) in enumerate(zip(ldi_ind_mat, ld_lab_mat)):xarr_dict['Dataset 1']['U'].append(xarray.open_mfdataset(U_fname_lst, combine='by_coords',parallel = True, preprocess=lambda ds: ds[{ld_nctvar:slice(ldi,ldi+1)}]) )
            for li,(ldi,ldilab) in enumerate(zip(ldi_ind_mat, ld_lab_mat)):xarr_dict['Dataset 1']['V'].append(xarray.open_mfdataset(V_fname_lst, combine='by_coords',parallel = True, preprocess=lambda ds: ds[{ld_nctvar:slice(ldi,ldi+1)}]) )
    


    #pdb.set_trace()    
    init_timer.append((datetime.now(),'xarray open_mfdataset UV connected'))
    print ('xarray open_mfdataset, Finish U and V',datetime.now())

    # load nav_lat and nav_lon
    if config.upper() in ['ORCA025','ORCA025EXT','ORCA12']: 

        nav_lon = np.ma.masked_invalid(rootgrp_gdept.variables[ncglamt][0])
        nav_lat = np.ma.masked_invalid(rootgrp_gdept.variables[ncgphit][0])
        
        # Fix Longitude, to be between -180 and 180.
        fixed_nav_lon = nav_lon.copy()
        for i, start in enumerate(np.argmax(np.abs(np.diff(nav_lon)) > 180, axis=1)):            fixed_nav_lon[i, start+1:] += 360
        fixed_nav_lon -=360
        fixed_nav_lon[fixed_nav_lon<-287.25] +=360
        fixed_nav_lon[fixed_nav_lon>73] -=360
        nav_lon = fixed_nav_lon.copy()


        nav_lat = np.ma.array(nav_lat[th['y0']:th['y1']:th['dy'],th['x0']:th['x1']:th['dx']])
        nav_lon = np.ma.array(nav_lon[th['y0']:th['y1']:th['dy'],th['x0']:th['x1']:th['dx']])

        
    elif config.upper() in ['CO9P2']: 

        nav_lon = np.ma.masked_invalid(rootgrp_gdept.variables[ncglamt][0])
        nav_lat = np.ma.masked_invalid(rootgrp_gdept.variables[ncgphit][0])
        nav_lat_amm15 = np.ma.array(nav_lat.copy())
        nav_lon_amm15 = np.ma.array(nav_lon.copy())
        

        nav_lat = np.ma.array(nav_lat[th['y0']:th['y1']:th['dy'],th['x0']:th['x1']:th['dx']])
        nav_lon = np.ma.array(nav_lon[th['y0']:th['y1']:th['dy'],th['x0']:th['x1']:th['dx']])

        #pdb.set_trace()

    else:
        if len(xarr_dict['Dataset 1']['T'][0].variables[nav_lat_varname].shape) == 2:
            nav_lon = np.ma.masked_invalid(xarr_dict['Dataset 1']['T'][0].variables[nav_lon_varname][th['y0']:th['y1']:th['dy'],th['x0']:th['x1']:th['dx']].load())
            nav_lat = np.ma.masked_invalid(xarr_dict['Dataset 1']['T'][0].variables[nav_lat_varname][th['y0']:th['y1']:th['dy'],th['x0']:th['x1']:th['dx']].load())
        else:
            # if only 1d lon and lat
            tmp_nav_lon = np.ma.masked_invalid(xarr_dict['Dataset 1']['T'][0].variables[nav_lon_varname].load())
            tmp_nav_lat = np.ma.masked_invalid(xarr_dict['Dataset 1']['T'][0].variables[nav_lat_varname].load())

            nav_lon_mat, nav_lat_mat = np.meshgrid(tmp_nav_lon,tmp_nav_lat)


            nav_lat = nav_lat_mat[th['y0']:th['y1']:th['dy'],th['x0']:th['x1']:th['dx']]
            nav_lon = nav_lon_mat[th['y0']:th['y1']:th['dy'],th['x0']:th['x1']:th['dx']]

    #Check if any nav_lat or nav_lon have masked values (i.e. using land suppression)
    if ((nav_lat == 0) & (nav_lon == 0)).sum()>10:
        print('Several points (>10) for 0degN 0degW - suggesting land suppression - use glamt and gphit from mesh')

        nav_lon = np.ma.masked_invalid(rootgrp_gdept.variables[ncglamt][0])
        nav_lat = np.ma.masked_invalid(rootgrp_gdept.variables[ncgphit][0])

        nav_lat = np.ma.array(nav_lat[th['y0']:th['y1']:th['dy'],th['x0']:th['x1']:th['dx']])
        nav_lon = np.ma.array(nav_lon[th['y0']:th['y1']:th['dy'],th['x0']:th['x1']:th['dx']])



    if config.upper() in ['AMM15']: 
        # AMM15 lon and lats are always 2d
        nav_lat_amm15 = np.ma.masked_invalid(xarr_dict['Dataset 1']['T'][0].variables[nav_lat_varname].load())
        nav_lon_amm15 = np.ma.masked_invalid(xarr_dict['Dataset 1']['T'][0].variables[nav_lon_varname].load())

    

    # if lon_in and lat_in are present, use them
    if (lon_in is not None) & (lat_in is not None):
        #pdb.set_trace()

        lonlatin_dist_mat = np.sqrt((nav_lon - lon_in)**2 + (nav_lat - lat_in)**2)
        jj,ii = lonlatin_dist_mat.argmin()//nav_lon.shape[1], lonlatin_dist_mat.argmin()%nav_lon.shape[1]
    
    nav_lon_2nd, nav_lat_2nd = nav_lon, nav_lat


    init_timer.append((datetime.now(),'Lon/Lats loaded'))

    grid_dict = {}
    grid_dict['Dataset 1'] = {}
    grid_dict['Dataset 2'] = {}

    grid_dict['Dataset 1']['e1t'] = rootgrp_gdept.variables[nce1t][0,th['y0']:th['y1']:th['dy'],th['x0']:th['x1']:th['dx']]
    grid_dict['Dataset 1']['e2t'] = rootgrp_gdept.variables[nce2t][0,th['y0']:th['y1']:th['dy'],th['x0']:th['x1']:th['dx']]
    grid_dict['Dataset 1']['e3t'] = rootgrp_gdept.variables[nce3t][0,:,th['y0']:th['y1']:th['dy'],th['x0']:th['x1']:th['dx']]
    grid_dict['Dataset 1']['gdept'] = rootgrp_gdept.variables[ncgdept][0,:,th['y0']:th['y1']:th['dy'],th['x0']:th['x1']:th['dx']]


    nz = grid_dict['Dataset 1']['gdept'].shape[0]
    if load_2nd_files:
        


        grid_dict['Dataset 2']['e1t'] = rootgrp_gdept_2nd.variables[nce1t][0,th['y0_2nd']:th['y1_2nd']:th['dy_2nd'],th['x0_2nd']:th['x1_2nd']:th['dx_2nd']]
        grid_dict['Dataset 2']['e2t'] = rootgrp_gdept_2nd.variables[nce2t][0,th['y0_2nd']:th['y1_2nd']:th['dy_2nd'],th['x0_2nd']:th['x1_2nd']:th['dx_2nd']]
        grid_dict['Dataset 2']['e3t'] = rootgrp_gdept_2nd.variables[nce3t][0,:,th['y0_2nd']:th['y1_2nd']:th['dy_2nd'],th['x0_2nd']:th['x1_2nd']:th['dx_2nd']]
        
        if config_2nd is None:
            grid_dict['Dataset 2']['gdept'] = rootgrp_gdept_2nd.variables[ncgdept][0,:,th['y0_2nd']:th['y1_2nd']:th['dy_2nd'],th['x0_2nd']:th['x1_2nd']:th['dx_2nd']]
        else:
            grid_dict['Dataset 2']['gdept'] = rootgrp_gdept_2nd.variables[config_fnames_dict[config_2nd]['ncgdept']][0,:,th['y0_2nd']:th['y1_2nd']:th['dy_2nd'],th['x0_2nd']:th['x1_2nd']:th['dx_2nd']]


    init_timer.append((datetime.now(),'gdept, e1t, e2t, e3t loaded'))


    deriv_var = []
    if load_2nd_files: 
        deriv_var_2nd = []
    x_dim, y_dim, z_dim, t_dim = load_nc_dims(xarr_dict['Dataset 1']['T'][0]) #  find the names of the x, y, z and t dimensions.
    var_4d_mat, var_3d_mat, var_mat, nvar4d, nvar3d, nvar, var_dim = load_nc_var_name_list(xarr_dict['Dataset 1']['T'][0], x_dim, y_dim, z_dim,t_dim)# find the variable names in the nc file
    var_grid = {}
    for ss in var_mat: var_grid[ss] = 'T'


    init_timer.append((datetime.now(),'var dims and names loaded'))

    if UV_vec == True:
        
        U_x_dim, U_y_dim, U_z_dim, U_t_dim  = load_nc_dims(xarr_dict['Dataset 1']['U'][0]) #  find the names of the x, y, z and t dimensions.
        U_var_names = load_nc_var_name_list(xarr_dict['Dataset 1']['U'][0], U_x_dim, U_y_dim, U_z_dim,U_t_dim)# find the variable names in the nc file # var_4d_mat, var_3d_mat, var_mat, nvar4d, nvar3d, nvar, var_dim = 
        U_var_4d_mat, U_var_3d_mat, U_var_mat, U_var_dim = U_var_names[0],U_var_names[1],U_var_names[2],U_var_names[6]

        V_x_dim, V_y_dim, V_z_dim, V_t_dim = load_nc_dims(xarr_dict['Dataset 1']['V'][0]) #  find the names of the x, y, z and t dimensions.
        V_var_names = load_nc_var_name_list(xarr_dict['Dataset 1']['V'][0], V_x_dim, V_y_dim, V_z_dim, V_t_dim)# find the variable names in the nc file # var_4d_mat, var_3d_mat, var_mat, nvar4d, nvar3d, nvar, var_dim
        V_var_4d_mat, V_var_3d_mat, V_var_mat, V_var_dim = V_var_names[0],V_var_names[1],V_var_names[2],V_var_names[6]
        
        var_mat = np.append(np.append(var_mat, U_var_mat), V_var_mat)
        for ss in U_var_dim: var_dim[ss] = U_var_dim[ss]
        for ss in V_var_dim: var_dim[ss] = V_var_dim[ss]
        
        
        for ss in U_var_mat: var_grid[ss] = 'U'
        for ss in V_var_mat: var_grid[ss] = 'V'

    
    init_timer.append((datetime.now(),'var dims and names loaded for UV'))

    if var is None: var = 'votemper'
    if var not in var_mat: var = var_mat[0]

    nice_varname_dict = {}
    for tmpvar in var_mat: nice_varname_dict[tmpvar] = tmpvar

    nice_varname_dict['votemper'] = 'Temperature'
    nice_varname_dict['vosaline'] = 'Salinity'
    nice_varname_dict['pea'] = 'Potential Energy Anomaly'
    nice_varname_dict['peat'] = 'Potential Energy Anomaly (T component)'
    nice_varname_dict['peas'] = 'Potential Energy Anomaly (S component)'
    nice_varname_dict['rho'] = 'Density'

    nice_varname_dict['baroc_mag'] = 'Baroclinic current magnitude'
    nice_varname_dict['barot_mag'] = 'Barotropic current magnitude'

    nice_varname_dict['baroc_curl'] = 'Baroclinic current curl'
    nice_varname_dict['barot_curl'] = 'Barotropic current curl'

    nice_varname_dict['baroc_div'] = 'Baroclinic current divergence'
    nice_varname_dict['barot_div'] = 'Barotropic current divergence'

    nice_varname_dict['vozocrtx'] = 'Baroclinic current (eastward component)'
    nice_varname_dict['vomecrty'] = 'Baroclinic current (westward component)'

    nice_varname_dict['sossheig'] = 'Sea surface height'
    nice_varname_dict['temper_bot'] = 'Bottom temperature'
    nice_varname_dict['tempis_bot'] = 'Bottom (in situ) temperature'
    nice_varname_dict['votempis'] = 'Temperature (in situ)'
    nice_varname_dict['mld25h_1'] = 'Mixed layer depth (version 1)'
    nice_varname_dict['mld25h_2'] = 'Mixed layer depth (version 2)'
    nice_varname_dict['karamld'] = 'Mixed layer depth (Kara)'

    nice_varname_dict['pCO2'] = 'Carbonate pCO2'
    nice_varname_dict['CHL'] = 'Total Chlorophyll'
    nice_varname_dict['netPP'] = 'Net Primary Production'
    nice_varname_dict['N1p'] = 'Phosphate'
    nice_varname_dict['N3n'] = 'Nitrate'
    nice_varname_dict['N5s'] = 'Silicate'
    nice_varname_dict['N4n'] = 'Ammonium Nitrogen'
    nice_varname_dict['O2o'] = 'Oxygen'

    nice_varname_dict['N:P'] = 'Nitrate to Phosphate Ratio'


    nice_varname_dict['pH'] = 'Carbonate pH'
    nice_varname_dict['PhytoC'] = 'Phytoplankton (carbon)'
    nice_varname_dict['Visib'] = 'Secchi depth '
    nice_varname_dict['spCO2'] = 'Surface Carbonate pCO2'

    
    init_timer.append((datetime.now(),'Nice names loaded'))

    # extract time information from xarray.
    # needs to work for gregorian and 360 day calendars.
    # needs to work for as x values in a plot, or pcolormesh
    # needs work, xarray time is tricky

    init_timer.append((datetime.now(),'nc time started'))
    
    print ('xarray start reading nctime',datetime.now())
    nctime = xarr_dict['Dataset 1']['T'][0].variables[time_varname]


    try:


        print ('xarray finished reading nctime',datetime.now())

        rootgrp_hpc_time = Dataset(fname_lst[0], 'r', format='NETCDF4')
        #pdb.set_trace()
        
        nc_time_var = rootgrp_hpc_time.variables[time_varname]
        if 'time_origin' in nc_time_var.ncattrs():
            nc_time_origin = nc_time_var.time_origin
        else:
            nc_time_origin = '1980-01-01 00:00:00'
            print('No time origin set - set to 1/1/1980. Other Time parameters likely to be missing')

            #pdb.set_trace()
        rootgrp_hpc_time.close()

       
        #different treatment for 360 days and gregorian calendars... needs time_datetime for plotting, and time_datetime_since_1970 for index selection
        if type(np.array(nctime)[0]) is type(cftime._cftime.Datetime360Day(1980,1,1)):
            nctime_calendar_type = '360'
        else:
            nctime_calendar_type = 'greg'


        #different treatment for 360 days and gregorian calendars... needs time_datetime for plotting, and time_datetime_since_1970 for index selection
        if  nctime_calendar_type in ['360','360_day']:
            # if 360 days

            time_datetime_since_1970 = np.array([ss.year + (ss.month-1)/12 + (ss.day-1)/360 for ss in np.array(nctime)])
            time_datetime = time_datetime_since_1970
        else:
            # if gregorian        
            sec_since_origin = [float(ii.data - np.datetime64(nc_time_origin))/1e9 for ii in nctime]
            time_datetime_cft = num2date(sec_since_origin,units = 'seconds since ' + nc_time_origin,calendar = 'gregorian') #nctime.calendar)

            time_datetime = np.array([datetime(ss.year, ss.month,ss.day,ss.hour,ss.minute) for ss in time_datetime_cft])
            time_datetime_since_1970 = np.array([(ss - datetime(1970,1,1,0,0)).total_seconds()/86400 for ss in time_datetime])


        if date_in_ind is not None:
            date_in_ind_datetime = datetime.strptime(date_in_ind,date_fmt)
            date_in_ind_datetime_timedelta = np.array([(ss - date_in_ind_datetime).total_seconds() for ss in time_datetime])
            ti = np.abs(date_in_ind_datetime_timedelta).argmin()
            if verbose_debugging: print('Setting ti from date_in_ind (%s): ti = %i (%s). '%(date_in_ind,ti, time_datetime[ti]), datetime.now())

    except:
        print()
        print()
        print()
        print(' Not able to read time in second data set, using dummy time')
        print()
        print()
        print()
        time_datetime = np.array([datetime(datetime.now().year, datetime.now().month, datetime.now().day) + timedelta(days = i_i) for i_i in range( xarr_dict['Dataset 1']['T'][0].dims[t_dim])])
        time_datetime_since_1970 = np.array([(ss - datetime(1970,1,1,0,0)).total_seconds()/86400 for ss in time_datetime])

        if date_in_ind is not None: ti = 0
    ntime = time_datetime.size
    
    init_timer.append((datetime.now(),'nc time completed'))

    if justplot: 
        print('justplot:',justplot)
        print('Just plotting, and exiting, not interactive.')
        
        just_plt_cnt = 0

        if justplot_date_ind is None:
             justplot_date_ind = time_datetime[ti].strftime(date_fmt)

        if justplot_z_meth_zz is None:
             justplot_z_meth_zz = 'ss:0,nb:0,df:0'

        if justplot_secdataset_proc is None:
             justplot_secdataset_proc = 'Dataset_1,Dataset_2,Dat2-Dat1'

        justplot_secdataset_proc = justplot_secdataset_proc.replace('_',' ')

        
        justplot_date_ind_lst = justplot_date_ind.split(',')
        justplot_z_meth_zz_lst = justplot_z_meth_zz.split(',')
        justplot_secdataset_proc_lst = justplot_secdataset_proc.split(',')
                
        
        just_plt_vals = []
        for justplot_date_ind_str in justplot_date_ind_lst:
            for zmi, justplot_z_meth_zz in enumerate(justplot_z_meth_zz_lst):
                justplot_z_meth,justplot_zz_str = justplot_z_meth_zz.split(':')
                justplot_zz = int(justplot_zz_str)
                for spi, secdataset_proc in enumerate(justplot_secdataset_proc_lst):
                    if (spi == 0):
                        just_plt_vals.append((secdataset_proc,justplot_date_ind_str, justplot_z_meth,justplot_zz, True, True, True, False, False))
                    else:
                        just_plt_vals.append((secdataset_proc,justplot_date_ind_str, justplot_z_meth,justplot_zz, False, False, False, False, False))
                      

    init_timer.append((datetime.now(),'justplot prepared'))
    # repeat if comparing two time series. 
    if fname_lst_2nd is not None:
        
        clim_sym = True
        
        init_timer.append((datetime.now(),'xarray open_mfdataset 2nd T connecting'))

        print ('xarray open_mfdataset 2nd, Start',datetime.now())   
        if nldi == 0:
            xarr_dict['Dataset 2']['T'].append(xarray.open_mfdataset(fname_lst_2nd, combine='by_coords',parallel = True))
        else:
            for li,(ldi,ldilab) in enumerate(zip(ldi_ind_mat, ld_lab_mat)):xarr_dict['Dataset 2']['T'].append(xarray.open_mfdataset(fname_lst_2nd, combine='by_coords',parallel = True, preprocess=lambda ds: ds[{ld_nctvar:slice(ldi,ldi+1)}]))   

        print ('xarray open_mfdataset 2nd, Finish',datetime.now())   

        init_timer.append((datetime.now(),'xarray open_mfdataset 2nd T connecting'))



        init_timer.append((datetime.now(),'xarray open_mfdataset 2nd UV connecting'))
        print ('xarray open_mfdataset, Start 2nd U and V',datetime.now())
        #Add baroclinic velocity magnitude
        UV_vec_2nd = False
        if (U_fname_lst_2nd is not None) & (V_fname_lst_2nd is not None):
            UV_vec_2nd = True
            if nldi == 0:
                xarr_dict['Dataset 2']['U'].append(xarray.open_mfdataset(U_fname_lst_2nd, combine='by_coords',parallel = True))
                xarr_dict['Dataset 2']['V'].append(xarray.open_mfdataset(V_fname_lst_2nd, combine='by_coords',parallel = True))
            else:
                for li,(ldi,ldilab) in enumerate(zip(ldi_ind_mat, ld_lab_mat)):xarr_dict['Dataset 2']['U'].append(xarray.open_mfdataset(U_fname_lst_2nd, combine='by_coords',parallel = True, preprocess=lambda ds: ds[{ld_nctvar:slice(ldi,ldi+1)}]) )
                for li,(ldi,ldilab) in enumerate(zip(ldi_ind_mat, ld_lab_mat)):xarr_dict['Dataset 2']['V'].append(xarray.open_mfdataset(V_fname_lst_2nd, combine='by_coords',parallel = True, preprocess=lambda ds: ds[{ld_nctvar:slice(ldi,ldi+1)}]) )
  
        print ('xarray open_mfdataset, finish 2nd U and V',datetime.now())
        init_timer.append((datetime.now(),'xarray open_mfdataset 2nd UV connecting'))




        if len(xarr_dict['Dataset 2']['T'][0].variables[nav_lat_varname].shape) == 2:
            nav_lat_2nd = np.ma.masked_invalid(xarr_dict['Dataset 2']['T'][0].variables[nav_lat_varname][th['y0_2nd']:th['y1_2nd']:th['dy_2nd'],th['x0_2nd']:th['x1_2nd']:th['dx_2nd']].load())
            nav_lon_2nd = np.ma.masked_invalid(xarr_dict['Dataset 2']['T'][0].variables[nav_lon_varname][th['y0_2nd']:th['y1_2nd']:th['dy_2nd'],th['x0_2nd']:th['x1_2nd']:th['dx_2nd']].load())
        else:
            # if only 1d lon and lat
            tmp_nav_lon = np.ma.masked_invalid(xarr_dict['Dataset 2']['T'][0].variables[nav_lon_varname].load())
            tmp_nav_lat = np.ma.masked_invalid(xarr_dict['Dataset 2']['T'][0].variables[nav_lat_varname].load())

            nav_lon_mat, nav_lat_mat = np.meshgrid(tmp_nav_lon,tmp_nav_lat)


            nav_lat_2nd = nav_lat_mat[th['y0']:th['y1']:th['dy'],th['x0']:th['x1']:th['dx']]
            nav_lon_2nd = nav_lon_mat[th['y0']:th['y1']:th['dy'],th['x0']:th['x1']:th['dx']]


        if load_2nd_files:
            if config_2nd is not None:
                if config_2nd.upper() in ['AMM15','CO9P2']: 
                    nav_lat_amm15 = np.ma.masked_invalid(xarr_dict['Dataset 2']['T'][0].variables[nav_lat_varname].load())
                    nav_lon_amm15 = np.ma.masked_invalid(xarr_dict['Dataset 2']['T'][0].variables[nav_lon_varname].load())
        print ('xarray start reading 2nd \nctime',datetime.now())
        init_timer.append((datetime.now(),'nc time 2nd started'))

        nctime_2nd = xarr_dict['Dataset 2']['T'][0].variables[time_varname]
        try: 
            print ('xarray finish reading 2nd nctime',datetime.now())

            rootgrp_hpc_time = Dataset(fname_lst_2nd[0], 'r', format='NETCDF4')
            nc_time_origin_2nd = rootgrp_hpc_time.variables[time_varname].time_origin
            rootgrp_hpc_time.close()
            #pdb.set_trace()
            
            #different treatment for 360 days and gregorian calendars... needs time_datetime for plotting, and time_datetime_since_1970 for index selection
            if type(np.array(nctime_2nd)[0]) is type(cftime._cftime.Datetime360Day(1980,1,1)):
                nctime_calendar_type_2nd = '360'
            else:
                nctime_calendar_type_2nd = 'greg'



            #different treatment for 360 days and gregorian calendars... needs time_datetime for plotting, and time_datetime_since_1970 for index selection
            #if type(np.array(nctime)[0]) is type(cftime._cftime.Datetime360Day(1980,1,1)):
            if  nctime_calendar_type in ['360','360_day']:
                # if 360 days

                time_datetime_since_1970_2nd = np.array([ss.year + (ss.month-1)/12 + (ss.day-1)/360 for ss in np.array(nctime_2nd)])
                time_datetime_2nd = time_datetime_since_1970_2nd
            else:
                # if gregorian        
                sec_since_origin_2nd = [float(ii.data - np.datetime64(nc_time_origin_2nd))/1e9 for ii in nctime_2nd]
                time_datetime_cft_2nd = num2date(sec_since_origin_2nd,units = 'seconds since ' + nc_time_origin_2nd,calendar = 'gregorian') #nctime.calendar)

                time_datetime_2nd = np.array([datetime(ss.year, ss.month,ss.day,ss.hour,ss.minute) for ss in time_datetime_cft_2nd])

                time_datetime_since_1970_2nd = np.array([(ss - datetime(1970,1,1,0,0)).total_seconds()/86400 for ss in time_datetime_2nd])

        except:
            print()
            print()
            print()
            print(' Not able to read time in second data set, using dummy time')
            print()
            print()
            print()
            time_datetime_2nd = np.array([datetime(datetime.now().year, datetime.now().month, datetime.now().day) + timedelta(days = i_i) for i_i in range( xarr_dict['Dataset 1']['T'][0].dims[t_dim])])
            time_datetime_since_1970_2nd = np.array([(ss - datetime(1970,1,1,0,0)).total_seconds()/86400 for ss in time_datetime_2nd])



        ntime_2nd = time_datetime_2nd.size
        
        # check both filessets have the same times
        if ntime_2nd != ntime:     
            print('Diff Times have different number of files')
            pdb.set_trace() 
        else:
            if allow_diff_time == False:
                if (time_datetime_since_1970_2nd != time_datetime_since_1970).any():   
                    print()
                    print("Times don't match between Dataset 1 and Dataset 2")
                    print()
                    pdb.set_trace()

        if config_2nd is None:
            if (nav_lat != nav_lat_2nd).any():
                print('Diff nav_lat_2nd dont match')
                pdb.set_trace()
            if (nav_lon != nav_lon_2nd).any():
                print('Diff nav_lon_2nd dont match')
                pdb.set_trace()
        # use a difference colormap if comparing files
        curr_cmap = scnd_cmap

        init_timer.append((datetime.now(),'nc time 2nd completed'))

        x_dim_2nd, y_dim_2nd, z_dim_2nd, t_dim_2nd = load_nc_dims(xarr_dict['Dataset 2']['T'][0]) #  find the names of the x, y, z and t dimensions.
        var_4d_mat_2nd, var_3d_mat_2nd, var_mat_2nd, nvar4d_2nd, nvar3d_2nd, nvar_2nd, var_dim_2nd = load_nc_var_name_list(xarr_dict['Dataset 2']['T'][0], x_dim_2nd, y_dim_2nd, z_dim_2nd,t_dim_2nd)# find the variable names in the nc file
        var_grid_2nd = {}
        for ss in var_mat_2nd: var_grid_2nd[ss] = 'T'

        init_timer.append((datetime.now(),'var dims and names 2nd loaded'))
        if UV_vec_2nd == True:
            U_x_dim_2nd, U_y_dim_2nd, U_z_dim_2nd, U_t_dim_2nd  = load_nc_dims(xarr_dict['Dataset 2']['U'][0]) #  find the names of the x, y, z and t dimensions.
            U_var_names_2nd = load_nc_var_name_list(xarr_dict['Dataset 2']['U'][0], U_x_dim_2nd, U_y_dim_2nd, U_z_dim_2nd,U_t_dim_2nd)# find the variable names in the nc file # var_4d_mat, var_3d_mat, var_mat, nvar4d, nvar3d, nvar, var_dim = 
            U_var_4d_mat_2nd, U_var_3d_mat_2nd, U_var_mat_2nd, U_var_dim_2nd = U_var_names_2nd[0],U_var_names_2nd[1],U_var_names_2nd[2],U_var_names_2nd[6]

            V_x_dim_2nd, V_y_dim_2nd, V_z_dim_2nd, V_t_dim_2nd = load_nc_dims(xarr_dict['Dataset 2']['V'][0]) #  find the names of the x, y, z and t dimensions.
            V_var_names_2nd = load_nc_var_name_list(xarr_dict['Dataset 2']['V'][0], V_x_dim_2nd, V_y_dim_2nd, V_z_dim_2nd, V_t_dim_2nd)# find the variable names in the nc file # var_4d_mat, var_3d_mat, var_mat, nvar4d, nvar3d, nvar, var_dim
            V_var_4d_mat_2nd, V_var_3d_mat_2nd, V_var_mat_2nd, V_var_dim_2nd = V_var_names_2nd[0],V_var_names_2nd[1],V_var_names_2nd[2],V_var_names_2nd[6]
            
            var_mat_2nd = np.append(np.append(var_mat_2nd, U_var_mat_2nd), V_var_mat_2nd)
            for ss in U_var_dim_2nd: var_dim_2nd[ss] = U_var_dim_2nd[ss]
            for ss in V_var_dim_2nd: var_dim_2nd[ss] = V_var_dim_2nd[ss]
            
            
            for ss in U_var_mat_2nd: var_grid_2nd[ss] = 'U'
            for ss in V_var_mat_2nd: var_grid_2nd[ss] = 'V'
        init_timer.append((datetime.now(),'var dims and names 2nd loaded for UV'))

    add_TSProf = False
    if ('votemper' in var_mat) & ('vosaline' in var_mat):
        add_TSProf = True
        for ss in ['pea','peat','peas']:
            var_mat = np.append(var_mat,ss)
            if load_2nd_files:
                var_mat_2nd = np.append(var_mat_2nd,ss)
            var_dim[ss] = 3
            var_grid[ss] = 'T'
            deriv_var.append(ss)


        for ss in ['rho']:
            var_mat = np.append(var_mat,ss)
            if load_2nd_files:
                var_mat_2nd = np.append(var_mat_2nd,ss)
            var_dim[ss] = 4
            var_grid[ss] = 'T'
            deriv_var.append(ss)


    if ('vozocrtx' in var_mat) & ('vomecrty' in var_mat):
        for ss in ['baroc_mag', 'baroc_div', 'baroc_curl']: 
            #ss = 'baroc_mag'
            var_mat = np.append(var_mat,ss)
            if load_2nd_files:
                if ('vozocrtx' in var_mat_2nd) & ('vomecrty' in var_mat_2nd):
                    var_mat_2nd = np.append(var_mat_2nd,ss)
            var_dim[ss] = 4
            var_grid[ss] = 'UV'
            deriv_var.append(ss)

    if ('ubar' in var_mat) & ('vbar' in var_mat):
        for ss in ['barot_mag', 'barot_div', 'barot_curl']: 
            #ss = 'barot_mag'
            var_mat = np.append(var_mat,ss)
            if load_2nd_files:
                if ('ubar' in var_mat_2nd) & ('vbar' in var_mat_2nd):
                    var_mat_2nd = np.append(var_mat_2nd,ss)
            var_dim[ss] = 3
            var_grid[ss] = 'UV'
            deriv_var.append(ss)


    if ('N3n' in var_mat) & ('N1p' in var_mat):
        ss = 'N:P'
        var_mat = np.append(var_mat,ss)
        if load_2nd_files:
            if ('N3n' in var_mat_2nd) & ('N1p' in var_mat_2nd):
                var_mat_2nd = np.append(var_mat_2nd,ss)
        var_dim[ss] = 4
        var_grid[ss] = 'T'
        deriv_var.append(ss)



    ldi = 0 

    data_inst_1 = None
    data_inst_2 = None
    if preload_data:
        preload_data_ti = ti
        preload_data_ti_2nd = ti
        preload_data_var = var
        preload_data_ldi = ldi


        
    init_timer.append((datetime.now(),'Derived var defined'))



    if (config.upper() in ['AMM15','CO9P2']): 
        lon_rotamm15,lat_rotamm15 = reduce_rotamm15_grid(nav_lon_amm15, nav_lat_amm15)

        dlon_rotamm15 = (np.diff(lon_rotamm15)).mean()
        dlat_rotamm15 = (np.diff(lat_rotamm15)).mean()
        nlon_rotamm15 = lon_rotamm15.size
        nlat_rotamm15 = lat_rotamm15.size

    if load_2nd_files:
        if config_2nd is not None:
            if (config_2nd.upper() in ['AMM15','CO9P2']):
                lon_rotamm15,lat_rotamm15 = reduce_rotamm15_grid(nav_lon_amm15, nav_lat_amm15)

                dlon_rotamm15 = (np.diff(lon_rotamm15)).mean()
                dlat_rotamm15 = (np.diff(lat_rotamm15)).mean()
                nlon_rotamm15 = lon_rotamm15.size
                nlat_rotamm15 = lat_rotamm15.size


    # find variables common to both data sets, and use them for the buttons
    
    var_but_mat = var_mat.copy()
    # If two datasets, find variables in both datasets
    if load_2nd_files:   
        var_but_mat = np.intersect1d(var_mat, var_mat_2nd)
        
        # sort them to match the order of the first dataset
        var_but_mat_order = []
        for var_but in var_but_mat:var_but_mat_order.append(np.where(var_mat == var_but )[0][0])
        var_but_mat = var_but_mat[np.argsort(var_but_mat_order)]

    nbutvar = var_but_mat.size


    #pdb.set_trace()

    
    init_timer.append((datetime.now(),'AMM15 grid rotated'))

    # set up figure.
    #   set up default figure, and then and and delete plots when you change indices.
    #   change indices with mouse click, detected with ginput
    #   ginput only works on one axes, so add a hidden fill screen axes, and then convert figure indices to an axes, and then using axes position and x/ylims into axes index. 
    #   create boxes with variable names as buttons to change variables. 
    climnorm = None # matplotlib.colors.LogNorm(0.005,0.1)
    
    print('Creating Figure', datetime.now())

    ax = []
    pax = []


    fig_tit_str = 'Interactive figure, Select lat/lon in a); lon in b); lat  in c); depth in d) and time in e).\n'
    if fig_fname_lab is not None: fig_tit_str = fig_tit_str + ' Dataset 1 = %s;'%fig_fname_lab
    if fig_fname_lab is not None: fig_tit_str = fig_tit_str + ' Dataset 2 = %s;'%fig_fname_lab_2nd

    fig_tit_str_int = 'Interactive figure, Select lat/lon in a); lon in b); lat  in c); depth in d) and time in e). %s[%i, %i, %i, %i] (thin = %i; thin_files = %i) '%(var,ii,jj,zz,ti, th['dx'], th['df'])
    fig_tit_str_lab = ''
    if fig_fname_lab is not None: fig_tit_str_lab = fig_tit_str_lab + ' Dataset 1 = %s;'%fig_fname_lab
    if fig_fname_lab is not None: fig_tit_str_lab = fig_tit_str_lab + ' Dataset 2 = %s;'%fig_fname_lab_2nd


    nvarbutcol = 16 # 18
    nvarbutcol = 22 # 18

    fig = plt.figure()
    fig.suptitle(fig_tit_str_int + '\n' + fig_tit_str_lab, fontsize=14)
    fig.set_figheight(12)
    fig.set_figwidth(18)
    if nbutvar <nvarbutcol:
        plt.subplots_adjust(top=0.88,bottom=0.1,left=0.09,right=0.91,hspace=0.2,wspace=0.065)
    else:
        plt.subplots_adjust(top=0.88,bottom=0.1,left=0.15,right=0.91,hspace=0.2,wspace=0.065)

    cbwid,cbgap = 0.01,0.01
    wgap = 0.06
    hgap = 0.04
    dyhig = 0.17
    axwid = 0.4
    if nbutvar <nvarbutcol:
        axwid = 0.39
        leftgap = 0.09
    else:
        axwid = 0.35
        leftgap = 0.15

    ax.append(fig.add_axes([leftgap,                                  0.10, axwid - cbwid - cbgap,  0.80]))
    ax.append(fig.add_axes([leftgap + (axwid - cbwid - cbgap) + wgap, 0.73, axwid - cbwid - cbgap,  0.17]))
    ax.append(fig.add_axes([leftgap + (axwid - cbwid - cbgap) + wgap, 0.52, axwid - cbwid - cbgap,  0.17]))
    ax.append(fig.add_axes([leftgap + (axwid - cbwid - cbgap) + wgap, 0.31, axwid - cbwid - cbgap,  0.17]))
    ax.append(fig.add_axes([leftgap + (axwid - cbwid - cbgap) + wgap, 0.10, axwid - cbwid - cbgap,  0.17]))




    labi,labj = 0.05, 0.95
    for ai,tmpax in enumerate(ax): tmpax.text(labi,labj,'%s)'%letter_mat[ai], transform=tmpax.transAxes, ha = 'left', va = 'top', fontsize = 12,bbox=dict(facecolor='white', alpha=0.75, pad=1, edgecolor='none'))


    tsaxtx1 = ax[4].text(0.01,0.01,'Dataset 1', ha = 'left', va = 'bottom', transform=ax[4].transAxes, color = 'r', fontsize = 12,bbox=dict(facecolor='white', alpha=0.75, pad=1, edgecolor='none'))
    if (fig_fname_lab is not None) : 
        tsaxtx1.set_text(fig_fname_lab)

    if load_2nd_files:                
        tsaxtx2 = ax[4].text(0.99,0.01,'Dataset 2', ha = 'right', va = 'bottom', transform=ax[4].transAxes, color = 'b', fontsize = 12,bbox=dict(facecolor='white', alpha=0.75, pad=1, edgecolor='none'))
    
        if (fig_fname_lab_2nd is not None) : 
            tsaxtx2.set_text(fig_fname_lab_2nd)

        tsaxtx3 = ax[4].text(0.99,0.975,'Dat2-Dat1', ha = 'right', va = 'top', transform=ax[4].transAxes, color = 'g', fontsize = 12,bbox=dict(facecolor='white', alpha=0.75, pad=1, edgecolor='none'))
                    

    #flip depth axes
    for tmpax in ax[1:]: tmpax.invert_yaxis()
    #use log depth scale, setiched off as often causes problems (clashes with hidden axes etc).
    #for tmpax in ax[1:]: tmpax.set_yscale('log')

    # add hidden fill screen axes 
    clickax = fig.add_axes([0,0,1,1], frameon=False)
    clickax.axis('off')
    

    
    init_timer.append((datetime.now(),'Figure Created'))


    if verbose_debugging: print('Created figure', datetime.now())

    #pdb.set_trace()
    #add "buttons"
    but_x0 = 0.01
    but_x1 = 0.06
    func_but_x1 = 0.99
    func_but_x0 = 0.94
    func_but_dx1 = func_but_x1 -func_but_x0 
    but_dy = 0.04
    but_dy = 0.03
    but_ysp = 0.01 
    but_ysp = 0.01 
    
    but_dysp = but_dy + but_ysp 
    

    but_extent = {}
    but_line_han,but_text_han = {},{}
    for vi,var_dat in enumerate(var_but_mat): 
        tmpcol = 'k'
        if var_dim[var_dat] == 3: tmpcol = 'darkgreen'
        if var_grid[var_dat] != 'T': tmpcol = 'gold'
        if var_dat in deriv_var: tmpcol = '0.5'
        vi_num = vi
        if vi>=nvarbutcol:
            vi_num = vi-nvarbutcol

            but_x0 = 0.01 + 0.06
            but_x1 = 0.06 + 0.06
      

        #note button extends (as in position.x0,x1, y0, y1)
        but_extent[var_dat] = np.array([but_x0,but_x1,0.9 - (but_dy + vi*but_dysp),0.9 - (0 + vi_num*but_dysp)])
        #add button box
        but_line_han[var_dat] = clickax.plot([but_x0,but_x1,but_x1,but_x0,but_x0],0.9 - (np.array([0,0,but_dy,but_dy,0]) + vi_num*but_dysp),color = tmpcol)
        #add button names
        but_text_han[var_dat] = clickax.text((but_x0+but_x1)/2,0.9 - ((but_dy/2) + vi_num*but_dysp),var_dat, ha = 'center', va = 'center')


    clickax.axis([0,1,0,1])
    
    if verbose_debugging: print('Added variable boxes', datetime.now())

    mode_name_lst = ['Click','Loop']

    func_names_lst = ['Hov/Time','ColScl','Reset zoom', 'Zoom', 'Axis','Clim: Reset','Clim: Zoom','Clim: Expand','Clim: pair','Clim: sym','Surface', 'Near-Bed', 'Surface-Bed','Depth-Mean','Depth level','Contours','Grad','T Diff','TS Diag','LD time','Fcst Diag','Save Figure','Quit']
    

    if add_TSProf:
        #ts_diag_coord = np.ma.ones(3)*np.ma.masked
        figts = None
        figfc = None
    else:
        func_names_lst.remove('TS Diag')

    if nldi < 2: # no point being able to change lead time database if only one 
        func_names_lst.remove('LD time')
        func_names_lst.remove('Fcst Diag')
    else:
        ldi=0
        

    if load_2nd_files == False:
        func_names_lst.remove('Clim: pair')

    func_names_lst = func_names_lst + mode_name_lst

    # if a secondary data set, give ability to change data sets. 
    if load_2nd_files:
        func_names_lst = func_names_lst + secdataset_proc_list + ['regrid_meth']

    func_but_line_han,func_but_text_han = {},{}
    func_but_extent = {}
    

    mode_name_secdataset_proc_list = mode_name_lst

    if load_2nd_files: 
        mode_name_secdataset_proc_list = mode_name_secdataset_proc_list + secdataset_proc_list + ['regrid_meth']

    #add button box
    for vi,funcname in enumerate(func_names_lst): 

        #note button extends (as in position.x0,x1, y0, y1)
        #func_but_extent[funcname] = [func_but_x0,func_but_x1,0.95 - (but_dy + vi*0.05),0.95 - (0 + vi*0.05)]
        func_but_extent[funcname] = [func_but_x0,func_but_x1,0.90 - (but_dy + vi*but_dysp),0.90 - (0 + vi*but_dysp)]


    for vi, tmp_funcname in enumerate(mode_name_secdataset_proc_list):
        func_but_extent[tmp_funcname] = [0.15 + vi*(func_but_dx1+0.01), 0.15 + vi*(func_but_dx1+0.01) + func_but_dx1, 0.025,  0.025 + but_dy]

    for vi,funcname in enumerate(func_names_lst): 

        func_but_line_han[funcname] = clickax.plot([func_but_extent[funcname][0],func_but_extent[funcname][1],func_but_extent[funcname][1],func_but_extent[funcname][0],func_but_extent[funcname][0]], [func_but_extent[funcname][2],func_but_extent[funcname][2],func_but_extent[funcname][3],func_but_extent[funcname][3],func_but_extent[funcname][2]],'k')
         #add button names
        func_but_text_han[funcname] = clickax.text((func_but_extent[funcname][0]+func_but_extent[funcname][1])/2,(func_but_extent[funcname][2]+func_but_extent[funcname][3])/2,funcname, ha = 'center', va = 'center')
    
    
    # if a secondary data set, det default behaviour. 
    if load_2nd_files: func_but_text_han[secdataset_proc].set_color('darkgreen')


    # Set intial mode to be Click
    func_but_text_han['Click'].set_color('gold')

    func_but_text_han['Depth level'].set_color('k')
    func_but_text_han['Surface'].set_color('k')
    func_but_text_han['Near-Bed'].set_color('k')
    func_but_text_han['Surface-Bed'].set_color('k')
    func_but_text_han['Depth-Mean'].set_color('k')
    if z_meth == 'z_slice':func_but_text_han['Depth level'].set_color('r')
    if z_meth == 'ss':func_but_text_han['Surface'].set_color('r')
    if z_meth == 'nb':func_but_text_han['Near-Bed'].set_color('r')
    if z_meth == 'df':func_but_text_han['Surface-Bed'].set_color('r')
    if z_meth == 'zm':func_but_text_han['Depth-Mean'].set_color('r')


    
    if load_2nd_files: 
        func_but_text_han['regrid_meth'].set_text('Regrid: NN')
        if clim_pair:func_but_text_han['Clim: pair'].set_color('gold')

    if hov_time:
        func_but_text_han['Hov/Time'].set_color('darkgreen')
    else:
        func_but_text_han['Hov/Time'].set_color('0.5')


    if do_cont:
        func_but_text_han['Contours'].set_color('darkgreen')
    else:
        func_but_text_han['Contours'].set_color('0.5')

    if do_grad == 1:
        func_but_text_han['Grad'].set_color('darkgreen')
    else:
        func_but_text_han['Grad'].set_color('0.5')
        func_but_text_han['Grad'].set_text('Grad')



    func_but_text_han['ColScl'].set_text('Col: Linear')

    func_but_text_han['Axis'].set_text('Axis: Auto')


    ldi = 0
    if nldi > 2:
        func_but_text_han['LD time'].set_text('LD time: %s'%ld_lab_mat[ldi])


    init_timer.append((datetime.now(),'Added functions boxes'))

    # When we move to loop mode, we stop checking for button presses, 
    #   so need another way to end the loop... 
    #       could just wait till the end of the loop, but could be ages
    #   therefore see if the mouse points to the "Click" button and change the mode.
    #
    # this could be an alternate method to the plt.ginput method.
    # Therefore define a global variable "mouse_in_Click" and use the matplotlib 
    # Connect, 'motion_notify_event', on_move method:
    #   https://matplotlib.org/stable/gallery/event_handling/coords_demo.html
    #
    global mouse_in_Click
    mouse_in_Click = False

    def on_move(event):
        global mouse_in_Click
        if event.inaxes:


            if (event.xdata>func_but_extent['Click'][0]) & (event.xdata<func_but_extent['Click'][1]) & (event.ydata>func_but_extent['Click'][2]) & (event.ydata<func_but_extent['Click'][3]):
                mouse_in_Click = True
                if verbose_debugging: print('Mouse in Click',datetime.now())
            else:
                mouse_in_Click = False


    binding_id = plt.connect('motion_notify_event', on_move)


    init_timer.append((datetime.now(),'Added Mouse tracking functions'))


    but_text_han[var].set_color('r')

    if verbose_debugging: print('Added functions boxes', datetime.now())


    ###########################################################################
    # Define inner functions
    ###########################################################################

    #global map_x,map_y,map_dat,ew_slice_x,ew_slice_y,ew_slice_dat,ns_slice_x,ns_slice_y,ns_slice_dat,hov_x,hov_y,hov_dat,ts_x,ts_dat
    #global ii,jj

    if verbose_debugging: print('Create inner functions', datetime.now())
    init_timer.append((datetime.now(),'Create inner functions'))


    def indices_from_ginput_ax(ax,clii,cljj,th,ew_line_x = None,ew_line_y = None,ns_line_x = None,ns_line_y = None):


        '''
        ginput doesn't tell you which subplot you are clicking, only the position within that subplot.
        we need which axis is clicked as well as the cooridinates within that axis
        
        we therefore trick ginput to give use figure coordinate (with a dummy, invisible full figure size subplot
        in front of everything, and then use this function to turn those coordinates into the coordinates within the 
        the subplot, and the which axis/subplot it is

ax,
        '''
        sel_ii,sel_jj,sel_ti ,sel_zz = None,None,None,None
        sel_ax = None
    
        for ai,tmpax in enumerate(ax): 
            tmppos =  tmpax.get_position()
            # was click within extent
            if (clii >= tmppos.x0) & (clii <= tmppos.x1) & (cljj >= tmppos.y0) & (cljj <= tmppos.y1):
                sel_ax = ai

                #convert figure coordinate of click, into location with the axes, using data coordinates
                clxlim = np.array(tmpax.get_xlim())
                clylim = np.array(tmpax.get_ylim())
                normxloc = (clii - tmppos.x0 ) / (tmppos.x1 - tmppos.x0)
                normyloc = (cljj - tmppos.y0 ) / (tmppos.y1 - tmppos.y0)
                xlocval = normxloc*clxlim.ptp() + clxlim.min()
                ylocval = normyloc*clylim.ptp() + clylim.min()

                if (th['dx'] != 1):
                    if config.upper() not in ['AMM7','AMM15', 'CO9P2', 'ORCA025','ORCA025EXT','GULF18','ORCA12']:
                        print('Thinning lon lat selection not programmed for ', config.upper())
                        pdb.set_trace()


                # what do the local coordiantes of the click mean in terms of the data to plot.
                # if on the map, or the slices, need to covert from lon and lat to ii and jj, which is complex for amm15.

                # if in map, covert lon lat to ii,jj
                if ai == 0:
                    loni,latj= xlocval,ylocval
                    if config.upper() in ['AMM7','GULF18']:
                        sel_ii = (np.abs(lon[th['x0']:th['x1']:th['dx']] - loni)).argmin()
                        sel_jj = (np.abs(lat[th['y0']:th['y1']:th['dy']] - latj)).argmin()
                    elif config.upper() in ['AMM15','CO9P2']:
                        lon_mat_rot, lat_mat_rot  = rotated_grid_from_amm15(loni,latj)
                        sel_ii = np.minimum(np.maximum( np.round((lon_mat_rot - lon_rotamm15[th['x0']:th['x1']:th['dx']].min())/(dlon_rotamm15*th['dx'])).astype('int') ,0),nlon_rotamm15//th['dx']-1)
                        sel_jj = np.minimum(np.maximum( np.round((lat_mat_rot - lat_rotamm15[th['y0']:th['y1']:th['dy']].min())/(dlat_rotamm15*th['dx'])).astype('int') ,0),nlat_rotamm15//th['dx']-1)
                    elif config.upper() in ['ORCA025','ORCA025EXT','ORCA12']:
                        sel_dist_mat = np.sqrt((nav_lon[:,:] - loni)**2 + (nav_lat[:,:] - latj)**2 )
                        sel_jj,sel_ii = sel_dist_mat.argmin()//sel_dist_mat.shape[1], sel_dist_mat.argmin()%sel_dist_mat.shape[1]

                    else:
                        print('config not supported:', config)
                        pdb.set_trace()
                    # and reload slices, and hovmuller/time series

                elif ai in [1]: 
                    # if in ew slice, change ns slice, and hov/time series
                    loni= xlocval
                    if config.upper() == 'AMM7':
                        sel_ii = (np.abs(lon[th['x0']:th['x1']:th['dx']] - loni)).argmin()
                    elif config.upper() in ['AMM15','CO9P2']:                        
                        latj =  ew_line_y[(np.abs(ew_line_x - loni)).argmin()] 
                        lon_mat_rot, lat_mat_rot  = rotated_grid_from_amm15(loni,latj)
                        sel_ii = np.minimum(np.maximum(np.round((lon_mat_rot - lon_rotamm15[th['x0']:th['x1']:th['dx']].min())/(dlon_rotamm15*th['dx'])).astype('int'),0),nlon_rotamm15//th['dx']-1)
                    elif config.upper() in ['ORCA025','ORCA025EXT','ORCA12']:
                        sel_ii = (np.abs(ew_line_x - loni)).argmin()
                    else:
                        print('config not supported:', config)
                        pdb.set_trace()
                    sel_zz = int( (1-normyloc)*clylim.ptp() + clylim.min() )
                    
                    
                elif ai in [2]:
                    # if in ns slice, change ew slice, and hov/time series
                    latj= xlocval
                    if config.upper() == 'AMM7':
                        sel_jj = (np.abs(lat[th['y0']:th['y1']:th['dy']] - latj)).argmin()
                    elif config.upper() in ['AMM15','CO9P2']:                        
                        loni =  ns_line_x[(np.abs(ns_line_y - latj)).argmin()]
                        lon_mat_rot, lat_mat_rot  = rotated_grid_from_amm15(loni,latj)
                        sel_jj = np.minimum(np.maximum(np.round((lat_mat_rot - lat_rotamm15[th['y0']:th['y1']:th['dy']].min())/(dlat_rotamm15*th['dx'])).astype('int'),0),nlat_rotamm15//th['dx']-1)
                    elif config.upper() in ['ORCA025','ORCA025EXT','ORCA12']:
                        sel_jj = (np.abs(ns_line_y - latj)).argmin()
                    else:
                        print('config not supported:', config)
                        #pdb.set_trace()
                    sel_zz = int( (1-normyloc)*clylim.ptp() + clylim.min() )

                elif ai in [3]:
                    # if in hov/time series, change map, and slices

                    # re calculate depth values, as y scale reversed, 
                    sel_zz = int( (1-normyloc)*clylim.ptp() + clylim.min() )
                    #pdb.set_trace()


                elif ai in [4]:
                    # if in hov/time series, change map, and slices
                    sel_ti = np.abs(xlocval - time_datetime_since_1970).argmin()
                    
                else:
                    print('clicked in another axes??')
                    return
                    pdb.set_trace()


        
        return sel_ax,sel_ii,sel_jj,sel_ti,sel_zz



    def save_figure_funct():


        figdpi = 90
        if not os.path.exists(fig_dir):
            os.makedirs(directory)

        secdataset_proc_figname = ''
        if secdataset_proc == 'Dataset 1':secdataset_proc_figname = '_Datset_1'
        if secdataset_proc == 'Dataset 2':secdataset_proc_figname = '_Datset_2'
        if secdataset_proc == 'Dat1-Dat2':secdataset_proc_figname = '_Diff_1-2'
        if secdataset_proc == 'Dat2-Dat1':secdataset_proc_figname = '_Diff_2-1'
        fig_out_name = '%s/output_%s_%s_th%02i_fth%02i_%04i_%04i_%03i_%03i_%s%s'%(fig_dir,fig_lab,var,th['dx'],th['df'],ii,jj,ti,zz,z_meth,secdataset_proc_figname)
        if fig_fname_lab is not None: fig_out_name = fig_out_name + '_d1_%s'%fig_fname_lab
        if fig_fname_lab_2nd is not None: fig_out_name = fig_out_name + '_d2_%s'%fig_fname_lab_2nd
        fig_out_name = fig_out_name


        fig_tit_str_lab = ''
        if load_2nd_files == False:
            fig_tit_str_lab = fig_fname_lab
        else:
            if secdataset_proc == 'Dataset 1':fig_tit_str_lab = '%s'%fig_fname_lab
            elif secdataset_proc == 'Dataset 2':fig_tit_str_lab = '%s'%fig_fname_lab_2nd
            elif secdataset_proc =='Dat1-Dat2':                
                fig_tit_str_lab = '%s minus %s'%(fig_fname_lab,fig_fname_lab_2nd)
            elif secdataset_proc =='Dat2-Dat1':                
                fig_tit_str_lab = '%s minus %s'%(fig_fname_lab_2nd,fig_fname_lab)



        fig.suptitle( fig_tit_str_lab, fontsize=14)


        if fig_cutout:


            bbox_cutout_pos = [[(but_x1+0.01), (0.066)],[(func_but_x0-0.01),0.965]]
            bbox_cutout_pos_inches = [[fig.get_figwidth()*(but_x1+0.01), fig.get_figheight()*(0.066)],[fig.get_figwidth()*(func_but_x0-0.01),fig.get_figheight()*(0.965)]]
            bbox_cutout_pos_inches = [[fig.get_figwidth()*(but_x1+0.01), fig.get_figheight()*(0.066)],[fig.get_figwidth()*(func_but_x0-0.01),fig.get_figheight()]]
            bbox_inches =  matplotlib.transforms.Bbox(bbox_cutout_pos_inches)
            
            if verbose_debugging: print('Save Figure: bbox_cutout_pos',bbox_cutout_pos, datetime.now())
            fig.savefig(fig_out_name+ '.png',bbox_inches = bbox_inches, dpi = figdpi)
        else:
            fig.savefig(fig_out_name+ '.png', dpi = figdpi)

        print('')
        print(fig_out_name + '.png')
        print('')





        fig.suptitle(fig_tit_str_int + '\n' + fig_tit_str_lab, fontsize=14)

        try:


            arg_output_text = 'flist1=$(echo "/dir1/file0[4-7]??_*.nc")\n'
            arg_output_text = arg_output_text + 'flist2=$(echo "/dir2/file0[4-7]??_*.nc")\n'
            arg_output_text = arg_output_text + '\n\n\n'

            arg_output_text = arg_output_text + 'python NEMO_nc_slevel_viewer.py %s'%config
            arg_output_text = arg_output_text + ' "$flist1" '
            if zlim_max is not None:arg_output_text = arg_output_text + ' --zlim_max %i'%zlim_max
            arg_output_text = arg_output_text + ' --thin %i'%th['dx']
            arg_output_text = arg_output_text + ' --thin_files %i'%th['df']
            arg_output_text = arg_output_text + ' --fig_fname_lab %s'%fig_fname_lab
            arg_output_text = arg_output_text + ' --lon %f'%nav_lon[jj,ii]
            arg_output_text = arg_output_text + ' --lat %f'%nav_lat[jj,ii]
            arg_output_text = arg_output_text + ' --date_ind %s'%time_datetime[ti].strftime(date_fmt)
            arg_output_text = arg_output_text + ' --date_fmt %s'%date_fmt
            arg_output_text = arg_output_text + ' --var %s'%var
            arg_output_text = arg_output_text + ' --z_meth %s'%z_meth
            arg_output_text = arg_output_text + ' --zz %s'%zz
            if xlim is not None:arg_output_text = arg_output_text + ' --xlim %f %f'%tuple(xlim)
            if ylim is not None:arg_output_text = arg_output_text + ' --ylim %f %f'%tuple(ylim)
            if load_2nd_files:
                if config_2nd is not None: 
                    arg_output_text = arg_output_text + ' --config_2nd %s'%config_2nd
                arg_output_text = arg_output_text + ' --fig_fname_lab_2nd %s'%fig_fname_lab_2nd
                arg_output_text = arg_output_text + ' --thin_2nd %i'%th['dx_2nd']
                arg_output_text = arg_output_text + ' --secdataset_proc "%s"'%secdataset_proc
                arg_output_text = arg_output_text + ' --fname_lst_2nd  "$flist2"'
                arg_output_text = arg_output_text + ' --clim_pair %s'%clim_pair

            arg_output_text = arg_output_text + " --justplot_date_ind '%s'"%time_datetime[ti].strftime(date_fmt)
            arg_output_text = arg_output_text + " --justplot_secdataset_proc '%s'"%justplot_secdataset_proc
            arg_output_text = arg_output_text + " --justplot_z_meth_zz '%s'"%justplot_z_meth_zz
            arg_output_text = arg_output_text + ' --justplot True'       
            arg_output_text = arg_output_text + '\n\n\n'       
            fid = open(fig_out_name + '.txt','w')
            fid.write(arg_output_text)
            fid.close()
            
            print(fig_out_name + '.png')
            print(fig_out_name + '.txt')

        except:
            pdb.set_trace()



    ###########################################################################
    # Inner functions defined
    ###########################################################################

    init_timer.append((datetime.now(),'Inner functions created'))

    
    if verbose_debugging: print('Inner functions created ', datetime.now())

    cur_xlim = xlim
    cur_ylim = ylim

    # only load data when needed
    reload_map, reload_ew, reload_ns, reload_hov, reload_ts = True,True,True,True,True


    if justplot: 
        secdataset_proc = just_plt_vals[just_plt_cnt][0]
        tmp_date_in_ind = just_plt_vals[just_plt_cnt][1]
        z_meth = just_plt_vals[just_plt_cnt][2]
        zz = just_plt_vals[just_plt_cnt][3]


    interp1d_wgtT, interp1d_wgtT_2nd = None, None
    interp1d_ZwgtT = {}
    interp1d_ZwgtT['Dataset 1'] = {}
    interp1d_ZwgtT['Dataset 2'] = {}
    
    if verbose_debugging: print('Create interpolation weights ', datetime.now())
    if z_meth_default == 'z_slice':
        interp1d_ZwgtT['Dataset 1'][0] = interp1dmat_create_weight(grid_dict['Dataset 1']['gdept'],0)

        if config_2nd is None:
            interp1d_ZwgtT['Dataset 2'] = interp1d_ZwgtT['Dataset 1']
        else:
            interp1d_ZwgtT['Dataset 2'][0] = interp1dmat_create_weight(grid_dict['Dataset 2']['gdept'],0)



    if verbose_debugging: print('Interpolation weights created', datetime.now())
    init_timer.append((datetime.now(),'Interpolation weights created'))


    if verbose_debugging: print('Start While Loop', datetime.now())
    #if verbose_debugging: print('')
    #if verbose_debugging: print('')
    if verbose_debugging: print('')

    # initialise button press location
    tmp_press = [(0.5,0.5,)]
    press_ginput = [(0.5,0.5,)]

    hov_y = np.array(0)


    stage_timer = {}
    stage_timer_name = {}
    for i_i in range(12+1):
        stage_timer[i_i] = datetime.now()
        stage_timer_name[i_i] = None
    


    init_timer.append((datetime.now(),'Starting While Loop'))
   
    if verbose_debugging:
        print()
        
        for i_i in range(1,len(init_timer)):print('Initialisation time %02i - %02i: %s - %s - %s '%(i_i-1,i_i,init_timer[i_i][0] - init_timer[i_i-1][0], init_timer[i_i-1][1], init_timer[i_i][1]))
        print()
    print('Initialisation: total: %s'%(init_timer[-1][0] - init_timer[0][0]))
    if verbose_debugging:print()

    secondary_fig = None


    while ii is not None:
        # try, exit on error
        stage_timer[3] = datetime.now() # start while loop
        stage_timer_name[3] = 'Start loop'

        
        #try:
        if True: 
            # extract plotting data (when needed), and subtract off difference files if necessary.

            if verbose_debugging: print('Set current data set (set of nc files) for ii = %s, jj = %s, zz = %s'%(ii,jj,zz), datetime.now())
            if verbose_debugging: print('Convert coordinates for config_2nd', datetime.now())
            global ii_2nd_ind, jj_2nd_ind, dd_2nd_ind, ew_ii_2nd_ind,ew_jj_2nd_ind,ns_ii_2nd_ind,ns_jj_2nd_ind,ew_jjdd_2nd_ind,ns_dd_2nd_ind

            ii_2nd_ind, jj_2nd_ind = ii,jj
            ew_ii_2nd_ind, ew_jj_2nd_ind = None, None
            ns_ii_2nd_ind, ns_jj_2nd_ind = None, None

            ew_bl_ii_ind_final,ew_bl_jj_ind_final,ew_wgt = None, None, None
            ns_bl_ii_ind_final,ns_bl_jj_ind_final,ns_wgt = None, None, None
            if config_2nd is not None:
                if ((config.upper() == 'AMM15') & (config_2nd.upper() == 'AMM7')) | ((config.upper() == 'AMM7') & (config_2nd.upper() == 'AMM15')):


                    if ((config.upper() == 'AMM7') & (config_2nd.upper() == 'AMM15')):

                        lon_mat_rot, lat_mat_rot  = rotated_grid_from_amm15(nav_lon[jj,ii] ,nav_lat[jj,ii])
                        ew_lon_mat_rot, ew_lat_mat_rot  = rotated_grid_from_amm15(nav_lon[jj,:],nav_lat[jj,:])
                        ns_lon_mat_rot, ns_lat_mat_rot  = rotated_grid_from_amm15(nav_lon[:,ii],nav_lat[:,ii])

                        tmp_lon_arr = lon_rotamm15
                        tmp_lat_arr = lat_rotamm15

                        tmp_lon = lon_mat_rot
                        tmp_lat = lat_mat_rot
                        
                        ns_tmp_lon_arr = ns_lon_mat_rot
                        ns_tmp_lat_arr = ns_lat_mat_rot
                        ew_tmp_lon_arr = ew_lon_mat_rot
                        ew_tmp_lat_arr = ew_lat_mat_rot


                    elif ((config.upper() == 'AMM15') & (config_2nd.upper() == 'AMM7')):

                        tmp_lon_arr = lon
                        tmp_lat_arr = lat

                        tmp_lon = nav_lon[jj,ii]
                        tmp_lat = nav_lat[jj,ii]
                        
                        ns_tmp_lon_arr = ns_lon_mat_rot = nav_lon[:,ii]
                        ns_tmp_lat_arr = ns_lat_mat_rot = nav_lat[:,ii]
                        ew_tmp_lon_arr = ew_lon_mat_rot = nav_lon[jj,:]
                        ew_tmp_lat_arr = ew_lat_mat_rot = nav_lat[jj,:]
                    
                    
                    (ii_2nd_ind,jj_2nd_ind,
                    ew_ii_2nd_ind,ew_jj_2nd_ind,
                    ns_ii_2nd_ind,ns_jj_2nd_ind, 
                    ew_bl_ii_ind_final,ew_bl_jj_ind_final,ew_wgt, 
                    ns_bl_ii_ind_final,ns_bl_jj_ind_final,ns_wgt) = regrid_iijj_ew_ns(tmp_lon,tmp_lat,
                        tmp_lon_arr, tmp_lat_arr, 
                        ew_tmp_lon_arr,ew_tmp_lat_arr,
                        ns_tmp_lon_arr,ns_tmp_lat_arr,
                        th['dx_2nd'],th['y0_2nd'],th['y1_2nd'],regrid_meth)
                    
                
            if verbose_debugging: print('Reload data for ii = %s, jj = %s, zz = %s'%(ii,jj,zz), datetime.now())
            if verbose_debugging: print('Reload map, ew, ns, hov, ts',reload_map,reload_ew,reload_ns,reload_hov,reload_ts, datetime.now())
            prevtime = datetime.now()
            datstarttime = prevtime

            
            
            stage_timer[4] = datetime.now() # start data instance load, finished converting data location from config to config2
            stage_timer_name[4] = 'Load Instance'


            #### Load data
            ####    (if necess)
            ###################################################################################################
            ###          Preload data
            ###################################################################################################

            if preload_data:
                #print('reload_data_instances:',var,preload_data_var,(data_inst_1 is None),(preload_data_ti != ti),(preload_data_var != var))
                #print('- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - ')

                # if data_inst_1 is None (i.e. first loop), or
                #       if the time has changed, or
                #       if the variable has changed
                if  (data_inst_1 is None)|(preload_data_ti != ti)|(preload_data_var != var)|(preload_data_ldi != ldi):
                    data_inst_1,data_inst_2,preload_data_ti,preload_data_var,preload_data_ldi= reload_data_instances(var,th,ldi,ti,var_grid, xarr_dict, grid_dict,var_dim,load_2nd_files)

                    # For T Diff
                    data_inst_1_Tm1,data_inst_2_Tm1 = None,None
                    preload_data_ti_Tm1,preload_data_var_Tm1,preload_data_ldi_Tm1 = 0.5,'None',0.5
                    Time_Diff_cnt = 0



            ###################################################################################################
            ### Status of buttons
            ###################################################################################################

            if ti == 0:
                func_but_text_han['T Diff'].set_color('0.5')
            else:
                if Time_Diff:
                    func_but_text_han['T Diff'].set_color('darkgreen')

                    if (data_inst_1_Tm1 is None)|(preload_data_ti_Tm1 != (ti-1))|(preload_data_var_Tm1 != var)|(preload_data_ldi_Tm1 != ldi):

                        (data_inst_1_Tm1,data_inst_2_Tm1,
                        preload_data_ti_Tm1,preload_data_var_Tm1,preload_data_ldi_Tm1) = reload_data_instances(var,th,ldi,ti-1,
                                var_grid, xarr_dict, grid_dict,var_dim,load_2nd_files)

                    #pdb.set_trace()
                    if Time_Diff_cnt == 0:
                        data_inst_1 = data_inst_1 - data_inst_1_Tm1
                        data_inst_2 = data_inst_2 - data_inst_2_Tm1
                        Time_Diff_cnt -= 1
                    func_but_text_han['Clim: sym'].set_color('r')
                    #curr_cmap = scnd_cmap
                    clim_sym_but = 1
                    #clim_sym_but_norm_val = clim_sym
                    clim_sym = True

                    reload_map = True
                    reload_ew = True
                    reload_ns = True

                else:
                    func_but_text_han['T Diff'].set_color('k')
                    if (data_inst_1_Tm1 is not None):

                        if Time_Diff_cnt == -1:
                            #if (preload_data_ti_Tm1 == (ti-1))|(preload_data_var_Tm1 == var)|(preload_data_ldi_Tm1 == ldi):
                            data_inst_1 = data_inst_1 + data_inst_1_Tm1
                            data_inst_2 = data_inst_2 + data_inst_2_Tm1
                            Time_Diff_cnt += 1

                        func_but_text_han['Clim: sym'].set_color('k')
                        clim_sym_but = 0
                        
                        reload_map = True
                        reload_ew = True
                        reload_ns = True

                        






            
            ###################################################################################################
            ### Slice data for plotting 
            ###################################################################################################

            stage_timer[5] = datetime.now() # start data dataload
            stage_timer_name[5] = 'Slice data'
            if reload_map:
                map_dat_1,map_dat_2,map_x,map_y = reload_map_data_comb(var,ldi,ti,z_meth,zz,zi, data_inst_1, data_inst_2,var_dim, interp1d_ZwgtT,grid_dict,nav_lon,nav_lat,regrid_params,regrid_meth,th,config_2nd,load_2nd_files)
                reload_map = False

                if do_grad == 1:
                    map_dat_1 = field_gradient_2d(map_dat_1, th['dx']*grid_dict['Dataset 1']['e1t'],th['dx']*grid_dict['Dataset 1']['e2t']) # scale up widths between grid boxes
                    map_dat_2 = field_gradient_2d(map_dat_2, th['dx']*grid_dict['Dataset 1']['e1t'],th['dx']*grid_dict['Dataset 1']['e2t']) # map 2 aleady on map1 grid, so use grid_dict['Dataset 1']['e1t'] not grid_dict['Dataset 2']['e1t']


            if verbose_debugging: print('Reloaded map data for ii = %s, jj = %s, zz = %s'%(ii,jj,zz), datetime.now(),'; dt = %s'%(datetime.now()-prevtime))
            prevtime = datetime.now()

            if reload_ew:
                if var_dim[var] == 4:
                    ew_slice_dat_1,ew_slice_dat_2,ew_slice_x, ew_slice_y = reload_ew_data_comb(ii,jj,ti,th, data_inst_1, data_inst_2, nav_lon, nav_lat, grid_dict, regrid_meth,ew_ii_2nd_ind,ew_jj_2nd_ind, ew_bl_jj_ind_final,ew_bl_ii_ind_final,ew_wgt,load_2nd_files,config_2nd)
                reload_ew = False

                if var_dim[var] == 4:
                    if do_grad == 1:
                        ew_slice_dat_1, ew_slice_dat_2 = grad_horiz_ew_data(th,grid_dict,jj, ew_slice_dat_1,ew_slice_dat_2)
                    if do_grad == 2:
                        ew_slice_dat_1, ew_slice_dat_2 = grad_vert_ew_data(ew_slice_dat_1,ew_slice_dat_2,ew_slice_y)

            if verbose_debugging: print('Reloaded  ew data for ii = %s, jj = %s, zz = %s'%(ii,jj,zz), datetime.now(),'; dt = %s'%(datetime.now()-prevtime))
            prevtime = datetime.now()

            if reload_ns:
                if var_dim[var] == 4:               
                    ns_slice_dat_1,ns_slice_dat_2,ns_slice_x, ns_slice_y = reload_ns_data_comb(ii,jj,ti,th, data_inst_1, data_inst_2, nav_lon, nav_lat, grid_dict, regrid_meth, ns_ii_2nd_ind,ns_jj_2nd_ind, ns_bl_jj_ind_final,ns_bl_ii_ind_final,ns_wgt,load_2nd_files,config_2nd)
                reload_ns = False

                if var_dim[var] == 4:   
                    if do_grad == 1:
                        ns_slice_dat_1, ns_slice_dat_2 = grad_horiz_ns_data(th,grid_dict,ii, ns_slice_dat_1,ns_slice_dat_2)
                    if do_grad == 2:
                        ns_slice_dat_1, ns_slice_dat_2 = grad_vert_ns_data(ns_slice_dat_1,ns_slice_dat_2,ns_slice_y)
                  

            if verbose_debugging: print('Reloaded  ns data for ii = %s, jj = %s, zz = %s'%(ii,jj,zz), datetime.now(),'; dt = %s'%(datetime.now()-prevtime))
            prevtime = datetime.now()
            
            if reload_hov:
                if hov_time:
                    if var_dim[var] == 4:
                        hov_dat_1,hov_dat_2,hov_x,hov_y = reload_hov_data_comb(var,var_mat,var_grid,deriv_var,ldi,th, time_datetime, ii,jj,ii_2nd_ind,jj_2nd_ind,nz,ntime, grid_dict,xarr_dict,load_2nd_files,config_2nd)

                        if do_grad == 2:
                            hov_dat_1,hov_dat_2 = grad_vert_hov_data(hov_dat_1,hov_dat_2,hov_y)

                else:
                    
                    hov_x = time_datetime
                    hov_y =  grid_dict['Dataset 1']['gdept'][:,jj,ii]
                    hov_dat_1 = np.ma.zeros((hov_y.shape+hov_x.shape))*np.ma.masked
                    hov_dat_2 = np.ma.zeros((hov_y.shape+hov_x.shape))*np.ma.masked
                reload_hov = False

            if verbose_debugging: print('Reloaded hov data for ii = %s, jj = %s, zz = %s'%(ii,jj,zz), datetime.now(),'; dt = %s'%(datetime.now()-prevtime))
            prevtime = datetime.now()
            if reload_ts:
                if hov_time:
                    ts_dat_1, ts_dat_2,ts_x = reload_ts_data_comb(var,var_dim,var_grid,ii,jj,ii_2nd_ind,jj_2nd_ind,ldi,hov_dat_1,hov_dat_2,hov_y,time_datetime,z_meth,zz,xarr_dict,grid_dict,th,var_mat,deriv_var,nz,ntime,config_2nd,load_2nd_files)
                else:
                    ts_x = time_datetime
                    ts_dat_1 = np.ma.ones(ntime)*np.ma.masked
                    ts_dat_2 = np.ma.ones(ntime)*np.ma.masked
                reload_ts = False
                

            if verbose_debugging: print('Reloaded  ts data for ii = %s, jj = %s, zz = %s'%(ii,jj,zz), datetime.now(),'; dt = %s'%(datetime.now()-prevtime))
            prevtime = datetime.now()

            print('Reloaded all data for ii = %s, jj = %s, zz = %s'%(ii,jj,zz), datetime.now(),'; dt = %s'%(datetime.now()-datstarttime))


            stage_timer[6] = datetime.now() #  dataload reloaded
            stage_timer_name[6] = 'Data sliced'



            
            ###################################################################################################
            ### Check colormaps 
            ###################################################################################################
            
            if verbose_debugging: print('Choose cmap based on secdataset_proc:',secdataset_proc, datetime.now())

            # Choose the colormap depending on which dataset being shown
            #if secdataset_proc in ['Dat1-Dat2','Dat2-Dat1']:
            if (secdataset_proc in ['Dat1-Dat2','Dat2-Dat1']) | (clim_sym_but == 1):
                curr_cmap = scnd_cmap
                clim_sym = True
            elif secdataset_proc in ['Dataset 1','Dataset 2']:
                if col_scl == 0:
                    curr_cmap = base_cmap
                elif col_scl == 1:
                    curr_cmap = base_cmap_high
                elif col_scl == 2:
                    curr_cmap = base_cmap_low
                clim_sym = False
            else:
                print(secdataset_proc)
                pdb.set_trace()

            
            
            ###################################################################################################
            ### Choose which dataset to use
            ###################################################################################################

            pax = []        
            map_dat = map_dat_1
            if var_dim[var] == 4:
                ns_slice_dat = ns_slice_dat_1
                ew_slice_dat = ew_slice_dat_1
                hov_dat = hov_dat_1
            ts_dat = ts_dat_1

            if load_2nd_files:
                if secdataset_proc == 'Dataset 1':
                    map_dat = map_dat_1
                    if var_dim[var] == 4:
                        ns_slice_dat = ns_slice_dat_1
                        ew_slice_dat = ew_slice_dat_1
                        hov_dat = hov_dat_1
                    ts_dat = ts_dat_1
                elif secdataset_proc == 'Dataset 2':
                    map_dat = map_dat_2
                    if var_dim[var] == 4:
                        ns_slice_dat = ns_slice_dat_2
                        ew_slice_dat = ew_slice_dat_2
                        hov_dat = hov_dat_2
                    ts_dat = ts_dat_2
                elif secdataset_proc == 'Dat1-Dat2':
                    map_dat = map_dat_1 - map_dat_2
                    if var_dim[var] == 4:
                        ns_slice_dat = ns_slice_dat_1 - ns_slice_dat_2
                        ew_slice_dat = ew_slice_dat_1 - ew_slice_dat_2
                        hov_dat = hov_dat_1 - hov_dat_2
                    ts_dat = ts_dat_1 - ts_dat_2
                elif secdataset_proc == 'Dat2-Dat1':
                    map_dat = map_dat_2 - map_dat_1
                    if var_dim[var] == 4:
                        ns_slice_dat = ns_slice_dat_2 - ns_slice_dat_1
                        ew_slice_dat = ew_slice_dat_2 - ew_slice_dat_1
                        hov_dat = hov_dat_2 - hov_dat_1
                    ts_dat = ts_dat_2 - ts_dat_1
            

            ###################################################################################################
            ### Replot data 
            ###################################################################################################

            
            stage_timer[7] = datetime.now() #  Starting Plotting data
            stage_timer_name[7] = 'Plot Data '



            if verbose_debugging: print("Do pcolormesh for ii = %i,jj = %i,ti = %i,zz = %i, var = '%s'"%(ii,jj, ti, zz,var), datetime.now())
            pax.append(ax[0].pcolormesh(map_x,map_y,map_dat,cmap = curr_cmap,norm = climnorm))
            if var_dim[var] == 4:
                pax.append(ax[1].pcolormesh(ew_slice_x,ew_slice_y,ew_slice_dat,cmap = curr_cmap,norm = climnorm))
                pax.append(ax[2].pcolormesh(ns_slice_x,ns_slice_y,ns_slice_dat,cmap = curr_cmap,norm = climnorm))
                pax.append(ax[3].pcolormesh(hov_x,hov_y,hov_dat,cmap = curr_cmap,norm = climnorm))
            if load_2nd_files == False:
                tsax = ax[4].plot(ts_x,ts_dat,'r')
                tsax2 = ax[4].plot(ts_x,ts_dat,'r')
            elif load_2nd_files:
                if secdataset_proc == 'Dat1-Dat2':
                    tsax  = ax[4].plot(ts_x,ts_dat_1 - ts_dat_2,'tab:brown')
                    tsax2 = ax[4].plot(ts_x,ts_dat_1*0, color = '0.5', ls = '--')
                elif secdataset_proc == 'Dat2-Dat1':
                    tsax  = ax[4].plot(ts_x,ts_dat_2 - ts_dat_1,'g')
                    tsax2 = ax[4].plot(ts_x,ts_dat_1*0, color = '0.5', ls = '--')
                elif secdataset_proc == 'Dataset 1':
                    tsax   = ax[4].plot(ts_x,ts_dat_1,'r')
                    tsax2 = ax[4].plot(ts_x,ts_dat_2,'b', lw = 0.5)
                elif secdataset_proc == 'Dataset 2':
                    tsax   = ax[4].plot(ts_x,ts_dat_2,'b')
                    tsax2 = ax[4].plot(ts_x,ts_dat_1,'r', lw = 0.5)

            
            ###################################################################################################
            ### Title String 
            ###################################################################################################
            
            stage_timer[8] = datetime.now() #  Plotted data
            stage_timer_name[8] = 'Data Plotted'

            nice_lev = ''
                
            if z_meth in ['z_slice','z_index']:nice_lev = '%i m'%zz
            elif z_meth == 'ss':nice_lev = 'Surface'
            elif z_meth == 'nb':nice_lev = 'Near-Bed'
            elif z_meth == 'df':nice_lev = 'Surface-Bed'
            elif z_meth == 'zm':nice_lev = 'Depth-Mean'

            if var_dim[var] == 4:  
                map_title_str = '%s (%s); %s %s'%(nice_varname_dict[var],nice_lev,lon_lat_to_str(nav_lon[jj,ii],nav_lat[jj,ii])[0],time_datetime[ti])
            elif var_dim[var] == 3:
                map_title_str = '%s; %s %s'%(nice_varname_dict[var],lon_lat_to_str(nav_lon[jj,ii],nav_lat[jj,ii])[0],time_datetime[ti])

            ax[0].set_title(map_title_str)
            

            ###################################################################################################
            ### add colorbars axes and colorbars
            ###################################################################################################

            if verbose_debugging: print('add colorbars', datetime.now(), 'len(ax):',len(ax))            
            cax = []      


            cbarax = []      
            cbarax.append(fig.add_axes([leftgap + (axwid - cbwid - cbgap) + cbgap, 0.1,cbwid,  0.8]))
            if var_dim[var] == 4:  
                cbarax.append(fig.add_axes([leftgap + (axwid - cbwid - cbgap) + wgap + axwid - cbwid - cbgap + cbgap,0.73, cbwid,  0.17]))
                cbarax.append(fig.add_axes([leftgap + (axwid - cbwid - cbgap) + wgap + axwid - cbwid - cbgap + cbgap,0.52, cbwid,  0.17]))
                cbarax.append(fig.add_axes([leftgap + (axwid - cbwid - cbgap) + wgap + axwid - cbwid - cbgap + cbgap,0.31, cbwid,  0.17]))


            cax = []      


            if var_dim[var] == 4:  
                for ai in [0,1,2,3]: cax.append(plt.colorbar(pax[ai], ax = ax[ai], cax = cbarax[ai]))
            elif var_dim[var] == 3:
                for ai in [0]: cax.append(plt.colorbar(pax[ai], ax = ax[ai], cax = cbarax[ai]))
            if verbose_debugging: print('added colorbars', datetime.now(), 'len(ax):',len(ax),'len(cax):',len(cax))
            # apply xlim/ylim if keyword set

            ###################################################################################################
            ### Set x/ylims
            ###################################################################################################


            if cur_xlim is not None:ax[0].set_xlim(cur_xlim)
            if cur_ylim is not None:ax[0].set_ylim(cur_ylim)
            if cur_xlim is not None:ax[1].set_xlim(cur_xlim)
            if cur_ylim is not None:ax[2].set_xlim(cur_ylim)
            if tlim is not None:ax[3].set_xlim(tlim)
            if tlim is not None:ax[4].set_xlim(tlim)
            #pdb.set_trace()
            #reset ylim to time series to data min max
            ax[4].set_xlim(ax[3].get_xlim())
            

            if load_2nd_files == False:
                ax[4].set_ylim(ts_dat.min(),ts_dat.max())
            elif load_2nd_files:
                if secdataset_proc == 'Dat1-Dat2':
                    ax[4].set_ylim((ts_dat_1 - ts_dat_2).min(),(ts_dat_1 - ts_dat_2).max())
                elif secdataset_proc == 'Dat2-Dat1':
                    ax[4].set_ylim((ts_dat_2 - ts_dat_1).min(),(ts_dat_2 - ts_dat_1).max())
                elif secdataset_proc in ['Dataset 1','Dataset 2']:
                    ax[4].set_ylim(np.ma.array([ts_dat_1,ts_dat_2]).min(),np.ma.array([ts_dat_1,ts_dat_2]).max())



            if verbose_debugging: print('Set x y lims', datetime.now())

            # set minimum depth if keyword set
            zlim_min = 1
            if zlim_max == None:
                tmpew_xlim = ax[1].get_xlim()
                tmpns_xlim = ax[2].get_xlim()
                tmpew_visible_ind = (ew_slice_x>=tmpew_xlim[0]) & (ew_slice_x<=tmpew_xlim[1]) 
                tmpns_visible_ind = (ns_slice_x>=tmpns_xlim[0]) & (ns_slice_x<=tmpns_xlim[1]) 


                ax[1].set_ylim([ew_slice_y[:,tmpew_visible_ind].max(),zlim_min])
                ax[2].set_ylim([ns_slice_y[:,tmpns_visible_ind].max(),zlim_min])
                ax[3].set_ylim([hov_y.max(),zlim_min])
            else:
                ax[1].set_ylim([zlim_max,zlim_min])
                ax[2].set_ylim([zlim_max,zlim_min])
                ax[3].set_ylim([np.minimum(zlim_max,hov_y.max()),zlim_min])


        
            ###################################################################################################
            ### add color lims
            ###################################################################################################


            stage_timer[9] = datetime.now() #  starting clims
            stage_timer_name[9] = 'Starting clim'

            if verbose_debugging: print('Reset colour limits', datetime.now())
            try:


                if load_2nd_files & (clim_pair == True)&(secdataset_proc not in ['Dat1-Dat2','Dat2-Dat1']) :

                    # if no xlim present using those from the map.
                    tmpxlim = cur_xlim
                    tmpylim = cur_ylim
                    if cur_xlim is None: tmpxlim = ax[0].get_xlim()#np.array([nav_lon.min(), nav_lon.max()])    
                    if cur_ylim is None: tmpylim = ax[0].get_ylim()#np.array([nav_lat.min(), nav_lat.max()])    

                    map_dat_reg_mask_1 = (nav_lon>tmpxlim[0]) & (nav_lon<tmpxlim[1]) & (nav_lat>tmpylim[0]) & (nav_lat<tmpylim[1])
                    #map_dat_reg_mask_2 = (nav_lon_2nd>xlim[0]) & (nav_lon_2nd<xlim[1]) & (nav_lat_2nd>ylim[0]) & (nav_lat_2nd<ylim[1])
                    tmp_map_dat_1 = map_dat_1[map_dat_reg_mask_1]
                    #tmp_map_dat_2 = map_dat_2[map_dat_reg_mask_2]
                    if map_dat_1.size != map_dat_2.size:
                        print('clim exception save, map 1 and 2 different size')
                        pdb.set_trace()
                    tmp_map_dat_2 = map_dat_2[map_dat_reg_mask_1]

                    tmp_map_dat_1 = tmp_map_dat_1[tmp_map_dat_1.mask == False]
                    tmp_map_dat_2 = tmp_map_dat_2[tmp_map_dat_2.mask == False]

                    tmp_map_perc_1 = np.ma.masked
                    tmp_map_perc_2 = np.ma.masked

                    if len(tmp_map_dat_1)>0: tmp_map_perc_1 = np.percentile(tmp_map_dat_1,(5,95))
                    if len(tmp_map_dat_2)>0: tmp_map_perc_2 = np.percentile(tmp_map_dat_2,(5,95))
                    tmp_map_perc = np.ma.append(tmp_map_perc_1,tmp_map_perc_2)

                    map_clim = np.ma.array([tmp_map_perc.min(),tmp_map_perc.max()])


                    if clim_sym: map_clim = np.ma.array([-1,1])*np.abs(map_clim).max()
                    if map_clim.mask.any() == False: set_clim_pcolor(map_clim, ax = ax[0])

                    
                    # only apply to ns and ew slices, and hov if 3d variable. 

                    if var_dim[var] == 4:

                        ew_dat_reg_mask_1 = (ew_slice_x>tmpxlim[0]) & (ew_slice_x<tmpxlim[1]) 
                        ns_dat_reg_mask_1 = (ns_slice_x>tmpylim[0]) & (ns_slice_x<tmpylim[1])

                        tmp_ew_dat_1 = ew_slice_dat_1[:,ew_dat_reg_mask_1]
                        tmp_ew_dat_2 = ew_slice_dat_2[:,ew_dat_reg_mask_1]
                        tmp_ns_dat_1 = ns_slice_dat_1[:,ns_dat_reg_mask_1]
                        tmp_ns_dat_2 = ns_slice_dat_2[:,ns_dat_reg_mask_1]
                       
                        tmp_hov_dat_1 = hov_dat_1.copy()
                        tmp_hov_dat_2 = hov_dat_2.copy()

                        tmp_ew_dat_1 = tmp_ew_dat_1[tmp_ew_dat_1.mask == False]
                        tmp_ns_dat_1 = tmp_ns_dat_1[tmp_ns_dat_1.mask == False]
                        tmp_hov_dat_1 = tmp_hov_dat_1[tmp_hov_dat_1.mask == False]
                        tmp_ew_dat_2 = tmp_ew_dat_2[tmp_ew_dat_2.mask == False] 
                        tmp_ns_dat_2 = tmp_ns_dat_2[tmp_ns_dat_2.mask == False]
                        tmp_hov_dat_2 = tmp_hov_dat_2[tmp_hov_dat_2.mask == False]


                        
                        tmp_ew_perc_1,tmp_ns_perc_1,tmp_hov_perc_1 = [np.ma.masked for i_i in range(3)]
                        tmp_ew_perc_2,tmp_ns_perc_2,tmp_hov_perc_2 = [np.ma.masked for i_i in range(3)]

                        if len(tmp_ew_dat_1)>0: tmp_ew_perc_1 = np.percentile(tmp_ew_dat_1,(5,95))
                        if len(tmp_ns_dat_1)>0: tmp_ns_perc_1 = np.percentile(tmp_ns_dat_1,(5,95))
                        if len(tmp_hov_dat_1)>0: tmp_hov_perc_1 = np.percentile(tmp_hov_dat_1,(5,95))

                        if len(tmp_ew_dat_2)>0: tmp_ew_perc_2 = np.percentile(tmp_ew_dat_2,(5,95))
                        if len(tmp_ns_dat_2)>0: tmp_ns_perc_2 = np.percentile(tmp_ns_dat_2,(5,95))
                        if len(tmp_hov_dat_2)>0: tmp_hov_perc_2 = np.percentile(tmp_hov_dat_2,(5,95))

                        tmp_ew_perc = np.ma.append(tmp_ew_perc_1,tmp_ew_perc_2)
                        tmp_ns_perc = np.ma.append(tmp_ns_perc_1,tmp_ns_perc_2)
                        tmp_hov_perc = np.ma.append(tmp_hov_perc_1,tmp_hov_perc_2)

                        ew_clim = np.ma.array([tmp_ew_perc.min(),tmp_ew_perc.max()])
                        ns_clim = np.ma.array([tmp_ns_perc.min(),tmp_ns_perc.max()])
                        hov_clim = np.ma.array([tmp_hov_perc.min(),tmp_hov_perc.max()])



                        if clim_sym: ew_clim = np.ma.array([-1,1])*np.abs(ew_clim).max()
                        if clim_sym: ns_clim = np.ma.array([-1,1])*np.abs(ns_clim).max()
                        if clim_sym: hov_clim = np.ma.array([-1,1])*np.abs(hov_clim).max()

                        if ew_clim.mask.any() == False: set_clim_pcolor(ew_clim, ax = ax[1])
                        if ns_clim.mask.any() == False: set_clim_pcolor(ns_clim, ax = ax[2])
                        if hov_clim.mask.any() == False: set_clim_pcolor(hov_clim, ax = ax[3])
                        #When using the log scale, the colour set_clim seems linked, so all panels get set to the limits of the final set_perc_clim_pcolor call..
                        #   therefore repeat set_perc_clim_pcolor of the map, so the hovmuller colour limit is not the final one. 


                    if map_clim.mask.any() == False: set_clim_pcolor(map_clim, ax = ax[0])

        
                else:
                    if (clim is None)| (secdataset_proc in ['Dat1-Dat2','Dat2-Dat1']):
                        for tmpax in ax[:-1]:set_perc_clim_pcolor_in_region(5,95, ax = tmpax,sym = clim_sym)
                        #When using the log scale, the colour set_clim seems linked, so all panels get set to the limits of the final set_perc_clim_pcolor call..
                        #   therefore repeat set_perc_clim_pcolor of the map, so the hovmuller colour limit is not the final one. 
                        set_perc_clim_pcolor_in_region(5,95, ax = ax[0],sym = clim_sym)

                    elif clim is not None:
                        if len(clim)>2:
                            for ai,tmpax in enumerate(ax):set_clim_pcolor((clim[2*ai:2*ai+1+1]), ax = tmpax)
                            set_clim_pcolor((clim[:2]), ax = ax[0])
                        elif len(clim)==2:
                            for ai,tmpax in enumerate(ax):set_clim_pcolor((clim), ax = tmpax)
                            set_clim_pcolor((clim), ax = ax[0])
            except:
                print("An exception occured - probably 'IndexError: cannot do a non-empty take from an empty axes.'")
                pdb.set_trace()
        

            stage_timer[10] = datetime.now() #  set clims
            stage_timer_name[10] = 'Set clim'

    
            ###################################################################################################
            ### add current loc lines
            ###################################################################################################

            if verbose_debugging: print('Plot location lines for ii = %s, jj = %s, zz = %s'%(ii,jj,zz), datetime.now())
            
            ## add lines to show current point. 
            # using plot for the map to show lines if on a rotated grid (amm15) etc.
            cs_plot_1 = ax[0].plot(nav_lon[jj,:],nav_lat[jj,:],color = '0.5', alpha = 0.5) 
            cs_plot_2 = ax[0].plot(nav_lon[:,ii],nav_lat[:,ii],color = '0.5', alpha = 0.5)
            cs_line = []
            # using axhline, axvline, for slices, hov, time series
            cs_line.append(ax[1].axvline(nav_lon[jj,ii],color = '0.5', alpha = 0.5))
            cs_line.append(ax[2].axvline(nav_lat[jj,ii],color = '0.5', alpha = 0.5))
            cs_line.append(ax[3].axvline(time_datetime_since_1970[ti],color = '0.5', alpha = 0.5))
            cs_line.append(ax[4].axvline(time_datetime_since_1970[ti],color = '0.5', alpha = 0.5))
            cs_line.append(ax[1].axhline(zz,color = '0.5', alpha = 0.5))
            cs_line.append(ax[2].axhline(zz,color = '0.5', alpha = 0.5))
            cs_line.append(ax[3].axhline(zz,color = '0.5', alpha = 0.5))


            
            ###################################################################################################
            ### add dataset labels
            ###################################################################################################

            if fig_fname_lab: tsaxtx1.set_text(fig_fname_lab)

            if load_2nd_files:                
     
                if secdataset_proc == 'Dat1-Dat2':
                    tsaxtx3.set_text('Dat1-Dat2')
                    tsaxtx3.set_color('tab:brown')
                elif secdataset_proc == 'Dat2-Dat1':
                    tsaxtx3.set_text('Dat2-Dat1')
                    tsaxtx3.set_color('g')
                else:
                    tsaxtx3.set_text(' ')
                    tsaxtx3.set_color('w')


            
            ###################################################################################################
            ### add contours
            ###################################################################################################
            conax = [] # define it outside if statement
            if do_cont:


                contcols, contlws, contalphas = '0.5',0.5,0.5
                cont_val_lst = []
                
                for tmpcax in cax:cont_val_lst.append(get_colorbar_values(tmpcax))
                
                conax.append(ax[0].contour(map_x,map_y,map_dat,cont_val_lst[0], colors = contcols, linewidths = contlws, alphas = contalphas))
                if var_dim[var] == 4: 
                    #nz = ns_slice_y.shape[0]
                    conax.append(ax[1].contour(np.tile(ew_slice_x,(nz,1)),ew_slice_y,ew_slice_dat,cont_val_lst[1], colors = contcols, linewidths = contlws, alphas = contalphas))
                    conax.append(ax[2].contour(np.tile(ns_slice_x,(nz,1)),ns_slice_y,ns_slice_dat,cont_val_lst[2], colors = contcols, linewidths = contlws, alphas = contalphas))
                    if hov_time & ntime>1:
                        
                        conax.append(ax[3].contour(hov_x,hov_y,hov_dat,cont_val_lst[3], colors = contcols, linewidths = contlws, alphas = contalphas))


            ###################################################################################################
            ### Redraw canvas
            ###################################################################################################
            if verbose_debugging: print('Canvas draw', datetime.now())

            stage_timer[11] = datetime.now() #  redraw
            stage_timer_name[11] = 'Redraw'

            fig.canvas.draw()
            if verbose_debugging: print('Canvas flush', datetime.now())
            fig.canvas.flush_events()
            if verbose_debugging: print('Canvas drawn and flushed', datetime.now())

            # set current axes to hidden full screen axes for click interpretation
            plt.sca(clickax)
            
    
            ###################################################################################################
            ### Runtime stats
            ###################################################################################################

            stage_timer[12] = datetime.now() #  redrawn
            stage_timer_name[12] = 'Redrawn'

            if stage_timer_name[1] is not None:
                if verbose_debugging:
                    print()
                    for i_i in range(2,12+1):print('Stage time %02i - %02i: %s - %s - %s '%(i_i-1,i_i,stage_timer[i_i] - stage_timer[i_i-1], stage_timer_name[i_i-1], stage_timer_name[i_i]))
                    print()
            
                print('Stage time 1 - 12: %s'%(stage_timer[12] - stage_timer[1]))
                if verbose_debugging: print()

            
            #await click with ginput
            if verbose_debugging: print('Waiting for button press', datetime.now())
            if verbose_debugging: print('mode', mode,'mouse_in_Click',mouse_in_Click,datetime.now())
            

            ###################################################################################################
            ### if click mode, ginput
            ###################################################################################################

            
            if secondary_fig is not None:
                #while plt.fignum_exists(figts.number):
                #    time.sleep(1)
                if secondary_fig:
                    time.sleep(5)
                    secondary_fig = False

            if mode == 'Loop':
                if mouse_in_Click:
                    mode = 'Click'
                    but_name = 'Click'
                    func_but_text_han['Click'].set_color('gold')
                    func_but_text_han['Loop'].set_color('k')
            if mode == 'Click':
                #if verbose_debugging: print('mode Click, check justplot:',justplot, datetime.now())
                if justplot == False:
                    
                    #if verbose_debugging: print('justplot false, ginput:',justplot, datetime.now())
                    
                    tmp_press = plt.ginput(1)
            # if tmp_press is empty (button press detected from another window, persist previous location. 
            #    Previously a empty array led to a continue, which led to the bug where additional colorbar were added
            if len(tmp_press) == 0:
                press_ginput = press_ginput
                button_press = False
            else:
                press_ginput = tmp_press
                button_press = True


            print('button_press',button_press)
            if verbose_debugging: print('')
            if verbose_debugging: print('')
            if verbose_debugging: print('')
            if verbose_debugging: print('Button pressed!', datetime.now())

            stage_timer[1] = datetime.now() # after button pressed
            stage_timer_name[1] = 'Button Pressed'

            ###################################################################################################
            ### Find where clicked
            ###################################################################################################

            clii,cljj = press_ginput[0][0],press_ginput[0][1]
                
            
            ###################################################################################################
            ### If justplot, hijack code
            ###################################################################################################

            if justplot:
                save_figure_funct()

                if just_plt_cnt == len(just_plt_vals): return 


                clii,cljj  = 0,0
                secdataset_proc = just_plt_vals[just_plt_cnt][0]
                tmp_date_in_ind = just_plt_vals[just_plt_cnt][1]
                z_meth = just_plt_vals[just_plt_cnt][2]
                zz = just_plt_vals[just_plt_cnt][3]
                reload_map = just_plt_vals[just_plt_cnt][4]
                reload_ew = just_plt_vals[just_plt_cnt][5]
                reload_ns = just_plt_vals[just_plt_cnt][6]
                reload_hov = just_plt_vals[just_plt_cnt][7]
                reload_TS = just_plt_vals[just_plt_cnt][8]


                jp_date_in_ind_datetime = datetime.strptime(tmp_date_in_ind,date_fmt)
                jp_date_in_ind_datetime_timedelta = np.array([(ss - jp_date_in_ind_datetime).total_seconds() for ss in time_datetime])
                ti = np.abs(jp_date_in_ind_datetime_timedelta).argmin()
                if verbose_debugging: print('Setting justplot secdataset_proc: %s'%(secdataset_proc), datetime.now())
                if verbose_debugging: print('Setting justplot ti from date_in_ind (%s): ti = %i (%s). '%(date_in_ind,ti, time_datetime[ti]), datetime.now())
                if verbose_debugging: print('Setting just_plt_vals: ',just_plt_vals[just_plt_cnt], datetime.now())
                just_plt_cnt += 1


            
            ###################################################################################################
            ### get and set current xylims
            ###################################################################################################



            if verbose_debugging: print("selected clii = %f,cljj = %f"%(clii,cljj))

            #get click location, and current axis limits for ax[0], and set them
            # defunct? was trying to allow zooming
            cur_xlim = np.array(ax[0].get_xlim())
            cur_ylim = np.array(ax[0].get_ylim())

            ax[0].set_xlim(cur_xlim)
            ax[0].set_ylim(cur_ylim)



            
            
            ###################################################################################################
            ### Get click coords
            ###################################################################################################
            #find clicked axes:
            is_in_axes = False
            
            # convert the mouse click into data indices, and report which axes was clicked
            sel_ax,sel_ii,sel_jj,sel_ti,sel_zz = indices_from_ginput_ax(ax,clii,cljj, th,ew_line_x = nav_lon[jj,:],ew_line_y = nav_lat[jj,:],ns_line_x = nav_lon[:,ii],ns_line_y = nav_lat[:,ii])

                
                
            if verbose_debugging: print("selected sel_ax = %s,sel_ii = %s,sel_jj = %s,sel_ti = %s,sel_zz = %s"%(sel_ax,sel_ii,sel_jj,sel_ti,sel_zz))

            #print(sel_ax,sel_ii,sel_jj,sel_ti,sel_zz )

            if sel_ax is not None :  is_in_axes = True 

            
            ###################################################################################################
            ### If axes clicked, change ind, decide what data to reload
            ###################################################################################################
            if verbose_debugging: print('Interpret Mouse click: figure axes, location change', datetime.now())

            if sel_ax == 0:               
                ii = sel_ii
                jj = sel_jj

                # and reload slices, and hovmuller/time series
                reload_ew = True
                reload_ns = True
                reload_hov = True
                reload_ts = True

            elif sel_ax in [1]: 
                ii = sel_ii
                # if in ew slice, change ns slice, and hov/time series
                
                reload_ns = True
                reload_hov = True
                reload_ts = True
                
            elif sel_ax in [2]:
                jj = sel_jj
                # if in ns slice, change ew slice, and hov/time series

                reload_ew = True
                reload_hov = True
                reload_ts = True

            elif sel_ax in [3]:
                # if in hov/time series, change map, and slices

                # re calculate depth values, as y scale reversed, 
                zz = sel_zz
                z_meth = z_meth_default
                
                if z_meth_default == 'z_index':
                    zi = np.abs(grid_dict['Dataset 1']['gdept'][:,jj,ii] - sel_zz).argmin()

                
                reload_map = True
                reload_ts = True

            elif sel_ax in [4]:
                # if in hov/time series, change map, and slices
                ti = sel_ti
                
                reload_map = True
                reload_ew = True
                reload_ns = True
   
            
            if mode == 'Loop':
                ti+=1
                if ti == ntime: 
                    ti = 0
                    #mode = 'Click'
                    #pdb.set_trace()
                    

                    
            
            if verbose_debugging: print('Decide what to reload', datetime.now())

            if verbose_debugging: print("selected ii = %s,jj = %s,ti = %s,zz = %s"%(ii,jj,ti,zz))

            # if in button, change variables. 
            if verbose_debugging: print('Interpret Mouse click: Change Variable', datetime.now())

            
            
            ###################################################################################################
            ### If var clicked, change var
            ###################################################################################################


            
            for but_name in but_extent.keys():
                
                but_pos_x0,but_pos_x1,but_pos_y0,but_pos_y1 = but_extent[but_name]
                if (clii >= but_pos_x0) & (clii <= but_pos_x1) & (cljj >= but_pos_y0) & (cljj <= but_pos_y1):
                    is_in_axes = True
                    if but_name in var_but_mat:
                        var = but_name


                        if var_dim[var] == 3:
                            z_meth = z_meth_default

                            func_but_text_han['Depth level'].set_color('r')
                            func_but_text_han['Surface'].set_color('k')
                            func_but_text_han['Near-Bed'].set_color('k')
                            func_but_text_han['Surface-Bed'].set_color('k')
                            func_but_text_han['Depth-Mean'].set_color('k')
                        
                        for vi,var_dat in enumerate(var_but_mat): but_text_han[var_dat].set_color('k')
                        but_text_han[but_name].set_color('r')
                        fig.canvas.draw()
                        
                        climnorm = None 

                        reload_map = True
                        reload_ew = True
                        reload_ns = True
                        reload_hov = True
                        reload_ts = True

            ###################################################################################################
            ### If function clicked, call function
            ###################################################################################################

            if verbose_debugging: print('Interpret Mouse click: Functions', datetime.now())
            for but_name in func_but_extent.keys():
                
                but_pos_x0,but_pos_x1,but_pos_y0,but_pos_y1 = func_but_extent[but_name]
                if (clii >= but_pos_x0) & (clii <= but_pos_x1) & (cljj >= but_pos_y0) & (cljj <= but_pos_y1):
                    is_in_axes = True
                    print(but_name)
                    if but_name in 'Reset zoom':
                        # set xlim and ylim to max size possible from nav_lat and nav_lon
                        cur_xlim = np.array([nav_lon.min(),nav_lon.max()])
                        cur_ylim = np.array([nav_lat.min(),nav_lat.max()])
                        zlim_max = None
                    elif but_name in 'Zoom':
                        # use ginput to take two clicks as zoom region. 
                        # only coded for main axes
                        
                        plt.sca(clickax)
                        tmpzoom0 = plt.ginput(1)
                        zoom0_ax,zoom0_ii,zoom0_jj,zoom0_ti,zoom0_zz = indices_from_ginput_ax(ax,tmpzoom0[0][0],tmpzoom0[0][1], th,ew_line_x = nav_lon[jj,:],ew_line_y = nav_lat[jj,:],ns_line_x = nav_lon[:,ii],ns_line_y = nav_lat[:,ii])
                        if zoom0_ax in [1,2,3]:
                            zlim_max = zoom0_zz
                        elif zoom0_ax in [0]:
                            tmpzoom1 = plt.ginput(1)
                            zoom1_ax,zoom1_ii,zoom1_jj,zoom1_ti,zoom1_zz = indices_from_ginput_ax(ax,tmpzoom1[0][0],tmpzoom1[0][1], th,ew_line_x = nav_lon[jj,:],ew_line_y = nav_lat[jj,:],ns_line_x = nav_lon[:,ii],ns_line_y = nav_lat[:,ii])
                                
                            if verbose_debugging: print(zoom0_ax,zoom0_ii,zoom0_jj,zoom0_ti,zoom0_zz)
                            if verbose_debugging: print(zoom1_ax,zoom1_ii,zoom1_jj,zoom1_ti,zoom1_zz)
                            if verbose_debugging: print(cur_xlim)
                            if verbose_debugging: print(cur_ylim)
                            # if both clicks in main axes, use clicks for the new x and ylims
                            if (zoom0_ax is not None) & (zoom0_ax is not None):
                                if zoom0_ax == zoom1_ax:
                                    if zoom0_ax == 0:
                                        cur_xlim = np.array([nav_lon[zoom0_jj,zoom0_ii],nav_lon[zoom1_jj,zoom1_ii]])
                                        cur_ylim = np.array([nav_lat[zoom0_jj,zoom0_ii],nav_lat[zoom1_jj,zoom1_ii]])
                                        cur_xlim.sort()
                                        cur_ylim.sort()
                                        
                                            
                    elif but_name == 'Axis':
                        if axis_scale == 'Auto':

                            func_but_text_han['Axis'].set_text('Axis: Equal')
                            ax[0].axis('equal')
                            axis_scale = 'Equal'
                        elif axis_scale == 'Equal':

                            func_but_text_han['Axis'].set_text('Axis: Auto')
                            axis_scale = 'Auto'
                            ax[0].axis('auto')
                            #cur_xlim = np.array([nav_lon.min(),nav_lon.max()])
                            #cur_ylim = np.array([nav_lat.min(),nav_lat.max()])


                    elif but_name == 'Clim: Reset':
                        clim = None


                    elif but_name == 'TS Diag':
                        if figts is not None:
                            if plt.fignum_exists(figts.number):
                                plt.close(figts)
                            

                        #pdb.set_trace()
                        if button_press:
                        #if ts_diag_coord.mask.all() 
                        #    if ((ts_diag_coord == np.ma.array([ii,jj,ti])).all() == False):
                            secondary_fig = True
                            #pdb.set_trace()
                            tmp_T_data_1 = np.ma.masked_invalid(xarr_dict['Dataset 1']['T'][ldi].variables['votemper'][ti,:,th['y0']:th['y1']:th['dy'],th['x0']:th['x1']:th['dx']][:,jj,ii].load())
                            tmp_S_data_1 = np.ma.masked_invalid(xarr_dict['Dataset 1']['T'][ldi].variables['vosaline'][ti,:,th['y0']:th['y1']:th['dy'],th['x0']:th['x1']:th['dx']][:,jj,ii].load())
                            tmp_gdept_1 = grid_dict['Dataset 1']['gdept'][:,jj,ii]
                            tmp_mld1_data_1 = np.ma.masked
                            tmp_mld2_data_1 = np.ma.masked
                            if 'mld25h_1' in var_mat: tmp_mld1_data_1 = np.ma.masked_invalid(xarr_dict['Dataset 1']['T'][ldi].variables['mld25h_1'][ti,th['y0']:th['y1']:th['dy'],th['x0']:th['x1']:th['dx']][jj,ii].load())
                            if 'mld25h_2' in var_mat: tmp_mld2_data_1 = np.ma.masked_invalid(xarr_dict['Dataset 1']['T'][ldi].variables['mld25h_2'][ti,th['y0']:th['y1']:th['dy'],th['x0']:th['x1']:th['dx']][jj,ii].load())

                            tmp_T_data_2 = tmp_T_data_1.copy()*np.ma.masked
                            tmp_S_data_2 = tmp_S_data_1.copy()*np.ma.masked
                            tmp_mld1_data_2 = tmp_mld1_data_1.copy()*np.ma.masked
                            tmp_mld2_data_2 = tmp_mld2_data_1.copy()*np.ma.masked



                            if load_2nd_files:
                                if config_2nd is None:
                                    if 'votemper' in var_mat_2nd:tmp_T_data_2   = np.ma.masked_invalid(xarr_dict['Dataset 2']['T'][ldi].variables['votemper'][ti,:,th['y0']:th['y1']:th['dy'],th['x0']:th['x1']:th['dx']][:,jj,ii].load())
                                    if 'vosaline' in var_mat_2nd:tmp_S_data_2   = np.ma.masked_invalid(xarr_dict['Dataset 2']['T'][ldi].variables['vosaline'][ti,:,th['y0']:th['y1']:th['dy'],th['x0']:th['x1']:th['dx']][:,jj,ii].load())
                                    if 'mld25h_1' in var_mat_2nd:tmp_mld1_data_2 = np.ma.masked_invalid(xarr_dict['Dataset 2']['T'][ldi].variables['mld25h_1'][ti,th['y0']:th['y1']:th['dy'],th['x0']:th['x1']:th['dx']][jj,ii].load())
                                    if 'mld25h_2' in var_mat_2nd:tmp_mld2_data_2 = np.ma.masked_invalid(xarr_dict['Dataset 2']['T'][ldi].variables['mld25h_2'][ti,th['y0']:th['y1']:th['dy'],th['x0']:th['x1']:th['dx']][jj,ii].load())

                                    tmp_gdept_2 = tmp_gdept_1
                                else:
                                
                                    if 'votemper' in var_mat_2nd:tmp_T_data_2 = np.ma.masked_invalid(xarr_dict['Dataset 2']['T'][ldi].variables['votemper'][ti,:,th['y0_2nd']:th['y1_2nd']:th['dy_2nd'],th['x0_2nd']:th['x1_2nd']:th['dx_2nd']][:,jj_2nd_ind,ii_2nd_ind].load())
                                    if 'vosaline' in var_mat_2nd:tmp_S_data_2 = np.ma.masked_invalid(xarr_dict['Dataset 2']['T'][ldi].variables['vosaline'][ti,:,th['y0_2nd']:th['y1_2nd']:th['dy_2nd'],th['x0_2nd']:th['x1_2nd']:th['dx_2nd']][:,jj_2nd_ind,ii_2nd_ind].load())
                                    if 'mld25h_1' in var_mat_2nd:tmp_mld1_data_2 = np.ma.masked_invalid(xarr_dict['Dataset 2']['T'][ldi].variables['mld25h_1'][ti,th['y0_2nd']:th['y1_2nd']:th['dy_2nd'],th['x0_2nd']:th['x1_2nd']:th['dx_2nd']][jj_2nd_ind,ii_2nd_ind].load())
                                    if 'mld25h_2' in var_mat_2nd:tmp_mld2_data_2 = np.ma.masked_invalid(xarr_dict['Dataset 2']['T'][ldi].variables['mld25h_2'][ti,th['y0_2nd']:th['y1_2nd']:th['dy_2nd'],th['x0_2nd']:th['x1_2nd']:th['dx_2nd']][jj_2nd_ind,ii_2nd_ind].load())
                                    tmp_gdept_2 =  grid_dict['Dataset 2']['gdept'][:,jj_2nd_ind,ii_2nd_ind]               

                            
                            tmp_rho_data_1 = sw_dens(tmp_T_data_1,tmp_S_data_1)
                            tmp_rho_data_2 = sw_dens(tmp_T_data_2,tmp_S_data_2)

                            tmp_t_arr = np.arange(0,30,.1)
                            tmp_s_arr = np.arange(15,40,.1)

                            #tmp_t_mat,tmp_s_mat = np.meshgrid(tmp_t_arr,tmp_s_arr)
                            tmp_s_mat,tmp_t_mat = np.meshgrid(tmp_s_arr,tmp_t_arr)
                            tmp_rho_mat = sw_dens(tmp_t_mat,tmp_s_mat)
                            

                            figts = plt.figure()
                            figts.set_figheight(8)
                            figts.set_figwidth(6)
                            axsp = figts.add_axes([0.1, 0.10, 0.3,  0.75])
                            axts = figts.add_axes([0.5, 0.55, 0.4,  0.30])
                            plt.subplots_adjust(top=0.8,bottom=0.11,left=0.125,right=0.9,hspace=0.2,wspace=0.6)
                            axsp.plot(tmp_S_data_1,tmp_gdept_1,'g')                          
                            if load_2nd_files: axsp.plot(tmp_S_data_2,tmp_gdept_2,'g--')
                            axsp.axhline(tmp_mld1_data_1, color = '0.5')
                            axsp.axhline(tmp_mld2_data_1, color = '0.25')
                            axsp.axhline(tmp_mld1_data_2, color = '0.5', ls = '--')
                            axsp.axhline(tmp_mld2_data_2, color = '0.25', ls = '--')
                            axsp.spines['bottom'].set_color('g')
                            axsp.spines['top'].set_visible(False)
                            axsp.set_xlabel('Salinity')  
                            axsp.xaxis.label.set_color('g')
                            axsp.tick_params(axis = 'x',colors = 'g')
                            axsp.invert_yaxis()
                            #
                            axtp = axsp.twiny()
                            axtp.plot(tmp_T_data_1,tmp_gdept_1,'r')
                            if load_2nd_files: axtp.plot(tmp_T_data_2,tmp_gdept_2,'r--')
                            axtp.set_xlabel('Temperature')
                            axtp.spines['top'].set_color('r')
                            axtp.tick_params(axis = 'x',colors = 'r')
                            axtp.spines['bottom'].set_visible(False)
                            axtp.xaxis.label.set_color('r')
                            axrp = axsp.twiny()
                            axrp.plot(tmp_rho_data_1,tmp_gdept_1,'b', lw = 0.5)
                            if load_2nd_files: axrp.plot(tmp_rho_data_2,tmp_gdept_2,'b--', lw = 0.5)
                            axrp.set_xlabel('Density')
                            axrp.spines['top'].set_color('b')
                            axrp.tick_params(axis = 'x',colors = 'b')
                            axrp.spines['bottom'].set_visible(False)
                            axrp.xaxis.label.set_color('b')
                            axrp.spines['top'].set_position(('axes', 1.1))
                            #
                            axts.plot(tmp_S_data_1,tmp_T_data_1,'b')
                            if load_2nd_files: axts.plot(tmp_S_data_2,tmp_T_data_2,'b--')
                            axts.set_xlabel('Salinity')
                            axts.set_ylabel('Temperature')
                            tmprhoxlim = axts.get_xlim()
                            tmprhoylim = axts.get_ylim()
                            axts.contour(tmp_s_mat,tmp_t_mat,tmp_rho_mat, np.arange(0,50,0.1), colors = 'k', linewidths = 0.5, alphas = 0.5, linestyles = '--')
                            axts.set_xlim(tmprhoxlim)
                            axts.set_ylim(tmprhoylim)
                            figts_lab_str = '%s\n\n%s\n\n%s'%(lon_lat_to_str(nav_lon[jj,ii],nav_lat[jj,ii])[0],time_datetime[ti],fig_fname_lab)
                            if load_2nd_files: figts_lab_str = figts_lab_str + '\n\n%s\n(dashed)'%fig_fname_lab_2nd
                            plt.text(0.5, 0.1, figts_lab_str, fontsize=14, transform=figts.transFigure, ha = 'left', va = 'bottom')
                            figts.show()
                            #ts_diag_coord = np.ma.array([ii,jj,ti])

                    elif but_name == 'Clim: Zoom': 


                        plt.sca(clickax)
            
                        tmpczoom = plt.ginput(2)
                        clim = np.array([tmpczoom[0][1],tmpczoom[1][1]])
                        clim.sort()


                    elif but_name == 'Clim: Expand': 
                        clim = np.array(get_clim_pcolor(ax = ax[0]))
                        if climnorm is None:
                            clim = np.array([clim.mean() - clim.ptp(),clim.mean() + clim.ptp()])
                        else:
                            clim = np.log10(np.array([(10**clim).mean() - (10**clim).ptp(),(10**clim).mean() + (10**clim).ptp()]))
                        
                    
                    #elif but_name == 'Clim: perc': 
                    #    clim = None

                    


                    elif but_name == 'LD time':
                        ldi+=1
                        if ldi == nldi: ldi = 0
                        func_but_text_han['LD time'].set_text('LD time: %s'%ld_lab_mat[ldi])
                        reload_map = True
                        reload_ew = True
                        reload_ns = True
                        reload_hov = True
                        reload_ts = True



                    elif but_name == 'Fcst Diag':
                        if figfc is not None:
                            if plt.fignum_exists(figfc.number):
                                plt.close(figfc)
                            

                        #pdb.set_trace()
                        if button_press:
                            secondary_fig = True
                            fsct_hov_dat_1,fsct_hov_dat_2 = [ np.ma.zeros(((nldi,)+hov_dat_1.shape))*np.ma.masked  for ii in range(2) ]
                            fsct_hov_x = np.ma.zeros((nldi,)+hov_x.shape, dtype = 'object')*np.ma.masked
                            try:
                                ld_time_offset = [int(ss) for ss in ld_lab_mat]
                            except:
                                ld_time_offset = [int(ss*24 - 36) for ss in range(nldi)]

                            fsct_ts_dat_1, fsct_ts_dat_2 = [ np.ma.zeros(((nldi,)+ts_dat_1.shape))*np.ma.masked  for ii in range(2) ]
                            fsct_ts_x = np.ma.zeros((nldi,)+ts_x.shape, dtype = 'object')*np.ma.masked

                            fcdata_start = datetime.now()
                            print('Extracting forecast data:',fcdata_start)
                            
                            for fcst_ldi in range(nldi): fsct_hov_dat_1[fcst_ldi],fsct_hov_dat_2[fcst_ldi],fsct_hov_x[fcst_ldi],fsct_fcst_y = reload_hov_data_comb(var,var_mat,var_grid,deriv_var,fcst_ldi, th,time_datetime, ii,jj,ii_2nd_ind,jj_2nd_ind,nz,ntime, grid_dict,xarr_dict, load_2nd_files,config_2nd)
                            
                            for fcst_ldi in range(nldi): fsct_ts_dat_1[fcst_ldi], fsct_ts_dat_2[fcst_ldi],fsct_ts_x[fcst_ldi] = reload_ts_data_comb(var,var_dim,var_grid,ii,jj,ii_2nd_ind,jj_2nd_ind,fcst_ldi,fsct_hov_dat_1[fcst_ldi],fsct_hov_dat_2[fcst_ldi],hov_y,time_datetime,z_meth,zz,xarr_dict,grid_dict,th,var_mat,deriv_var,nz,ntime,config_2nd,load_2nd_files)
                            for fcst_ldi in range(nldi): fsct_hov_x[fcst_ldi] = fsct_hov_x[fcst_ldi] + timedelta(hours = ld_time_offset[fcst_ldi])
                            for fcst_ldi in range(nldi): fsct_ts_x[fcst_ldi] = fsct_ts_x[fcst_ldi] + timedelta(hours = ld_time_offset[fcst_ldi])
                            print('Extracted forecast data:',datetime.now(), datetime.now() - fcdata_start)
                            



                                
                            figfc_lab_str = '%s forecast diagram for \n%s'%(nice_varname_dict[var],lon_lat_to_str(nav_lon[jj,ii],nav_lat[jj,ii])[0])


                            if var_dim[var] == 4:  
                                figfc_lab_str = '%s (%s) forecast diagram\nfor %s'%(nice_varname_dict[var],nice_lev,lon_lat_to_str(nav_lon[jj,ii],nav_lat[jj,ii])[0])
                            elif var_dim[var] == 3:
                                figfc_lab_str = '%s forecast diagram\nfor %s'%(nice_varname_dict[var],lon_lat_to_str(nav_lon[jj,ii],nav_lat[jj,ii])[0])



                            figfc = plt.figure()
                            figfc.set_figheight(5)
                            figfc.set_figwidth(6)
                            figfc.suptitle(figfc_lab_str, fontsize = 16) 
                            axfc = []
                            if load_2nd_files:                       
                                figfc.set_figheight(8)    
                                axfc.append(plt.subplot(2,1,1))  
                                axfc.append(plt.subplot(2,1,2))
                                plt.subplots_adjust(top=0.875,bottom=0.11,left=0.125,right=0.9,hspace=0.2,wspace=0.6) 
                            else:
                                plt.subplots_adjust(top=0.825,bottom=0.11,left=0.125,right=0.9,hspace=0.2,wspace=0.6) 
                                axfc.append(plt.subplot(1,1,1))  
                                
                            axfc[0].plot(fsct_ts_x,fsct_ts_dat_1[:,:], '0.5' )                   
                            axfc[0].plot(fsct_ts_x[0,:],fsct_ts_dat_1[0,:],'ro' )            
                            axfc[0].plot(fsct_ts_x[-1,:],fsct_ts_dat_1[-1,:],'x', color = '0.5')
                            axfc[0].set_title(fig_fname_lab)
                            if load_2nd_files:       
                                axfc[1].plot(fsct_ts_x,fsct_ts_dat_2[:,:], '0.5' )                   
                                axfc[1].plot(fsct_ts_x[0,:],fsct_ts_dat_2[0,:],'ro' )
                                axfc[1].plot(fsct_ts_x[-1,:],fsct_ts_dat_2[-1,:],'x', color = '0.5')
                                axfc[1].set_title(fig_fname_lab_2nd)
                            figfc.show()

                        #pdb.set_trace()

                    elif but_name == 'Clim: pair':
                        if clim_pair:
                            func_but_text_han['Clim: pair'].set_color('k')
                            clim_pair = False
                        else:
                            func_but_text_han['Clim: pair'].set_color('gold')
                            clim_pair = True

                    elif but_name == 'Clim: sym':
                        if clim_sym_but == 0:
                            func_but_text_han['Clim: sym'].set_color('r')
                            #curr_cmap = scnd_cmap
                            clim_sym_but = 1
                            #clim_sym_but_norm_val = clim_sym
                            clim_sym = True
                            
                        elif clim_sym_but == 1:
                            func_but_text_han['Clim: sym'].set_color('k')
                            clim_sym_but = 0
                            
                            
                            #curr_cmap = base_cmap
                            #func_but_text_han['ColScl'].set_text('Col: Linear')
                            #col_scl = 0
                            #clim_sym = clim_sym_but_norm_val
                            

                    elif but_name == 'Hov/Time':
                        if hov_time:
                            func_but_text_han['Hov/Time'].set_color('0.5')
                            hov_time = False
                        else:
                            func_but_text_han['Hov/Time'].set_color('darkgreen')
                            hov_time = True
                            reload_hov = True
                            reload_ts = True

                    elif but_name == 'regrid_meth':
                        if regrid_meth == 1:
                            func_but_text_han['regrid_meth'].set_text('Regrid: Bilin')
                            regrid_meth = 2
                            reload_map = True
                            reload_ew = True
                            reload_ns = True
                        elif regrid_meth == 2:
                            func_but_text_han['regrid_meth'].set_text('Regrid: NN')
                            regrid_meth = 1
                            reload_map = True
                            reload_ew = True
                            reload_ns = True

                    elif but_name == 'Contours':
                        if do_cont:
                            func_but_text_han['Contours'].set_color('k')
                            do_cont = False
                        else:
                            func_but_text_han['Contours'].set_color('darkgreen')
                            do_cont = True


                    elif but_name == 'Grad':
                        if do_grad == 0:
                            func_but_text_han['Grad'].set_color('darkgreen')
                            func_but_text_han['Grad'].set_text('Horiz Grad')
                            do_grad = 1
                            reload_map = True
                            reload_ew = True
                            reload_ns = True
                            reload_hov = True
                            reload_ts = True
                        elif do_grad == 1:
                            func_but_text_han['Grad'].set_color('gold')
                            func_but_text_han['Grad'].set_text('Vert Grad')

                            do_grad = 2
                            reload_map = True
                            reload_ew = True
                            reload_ns = True
                            reload_hov = True
                            reload_ts = True
                        elif do_grad == 2:
                            func_but_text_han['Grad'].set_color('0.5')
                            func_but_text_han['Grad'].set_text('Grad')

                            do_grad = 0
                            reload_map = True
                            reload_ew = True
                            reload_ns = True
                            reload_hov = True
                            reload_ts = True
 

                    elif but_name == 'T Diff':

                        if ti == 0:
                            func_but_text_han['T Diff'].set_color('0.5')
                        else:
                            if Time_Diff:
                                Time_Diff = False
                                func_but_text_han['T Diff'].set_color('k')
                            else:
                                Time_Diff = True
                                func_but_text_han['T Diff'].set_color('darkgreen')


                        """
                        if ti == 0:
                            func_but_text_han['T Diff'].set_color('0.5')
                        else:
                            if Time_Diff:
                                Time_Diff = False
                                func_but_text_han['T Diff'].set_color('k')
                                
                                if (data_inst_1_Tm1 is None)|(preload_data_ti_Tm1 == (ti-1))|(preload_data_var_Tm1 == var)|(preload_data_ldi_Tm1 == ldi):
                                    data_inst_1 = data_inst_1 + data_inst_1_Tm1
                                    data_inst_2 = data_inst_2 + data_inst_2_Tm1

                                
                                reload_map = True
                                reload_ew = True
                                reload_ns = True
                            else:
                                Time_Diff = True
                                func_but_text_han['T Diff'].set_color('darkgreen')

                                if (data_inst_1_Tm1 is None)|(preload_data_ti_Tm1 != (ti-1))|(preload_data_var_Tm1 != var)|(preload_data_ldi_Tm1 != ldi):

                                    (data_inst_1_Tm1,data_inst_2_Tm1,
                                    preload_data_ti_Tm1,preload_data_var_Tm1,preload_data_ldi_Tm1) = reload_data_instances(var,th,ldi,ti-1,
                                            var_grid, xarr_dict, grid_dict,var_dim,load_2nd_files)


                                data_inst_1 = data_inst_1 - data_inst_1_Tm1
                                data_inst_2 = data_inst_2 - data_inst_2_Tm1
                                
                                reload_map = True
                                reload_ew = True
                                reload_ns = True
                                
                                '''
                                reload_map = True
                                reload_ew = True
                                reload_ns = True
                                reload_hov = True
                                reload_ts = True
                                '''
                        """

                    elif but_name == 'ColScl':
                        if secdataset_proc in ['Dataset 1','Dataset 2']:
                            if col_scl == 0:
                                func_but_text_han['ColScl'].set_text('Col: High')
                                col_scl = 1
                                curr_cmap = base_cmap_high
                            elif col_scl == 1:
                                func_but_text_han['ColScl'].set_text('Col: Low')
                                curr_cmap = base_cmap_low
                                col_scl = 2
                            elif col_scl == 2:
                                func_but_text_han['ColScl'].set_text('Col: Linear')
                                curr_cmap = base_cmap
                                col_scl = 0
                        else:
                            curr_cmap = scnd_cmap


                    
                    elif but_name in secdataset_proc_list:
                        secdataset_proc = but_name
                        func_but_text_han['Dat1-Dat2'].set_color('k')
                        func_but_text_han['Dat2-Dat1'].set_color('k')
                        func_but_text_han['Dataset 1'].set_color('k')
                        func_but_text_han['Dataset 2'].set_color('k')
                        func_but_text_han[but_name].set_color('darkgreen')


                    elif but_name in ['Surface','Near-Bed','Surface-Bed','Depth-Mean']:
                        if var_dim[var] == 4:
                            
                            if but_name == 'Surface':z_meth = 'ss'
                            if but_name == 'Near-Bed': z_meth = 'nb'
                            if but_name == 'Surface-Bed': z_meth = 'df'
                            if but_name == 'Depth-Mean': z_meth = 'zm'
                            reload_map = True
                            reload_ts = True

                            func_but_text_han['Depth level'].set_color('k')
                            func_but_text_han['Surface'].set_color('k')
                            func_but_text_han['Near-Bed'].set_color('k')
                            func_but_text_han['Surface-Bed'].set_color('k')
                            func_but_text_han['Depth-Mean'].set_color('k')
                            func_but_text_han[but_name].set_color('r')
                            fig.canvas.draw()

                    elif but_name in ['Depth level']:
                        func_but_text_han['Depth level'].set_color('k')
                        func_but_text_han['Surface'].set_color('k')
                        func_but_text_han['Near-Bed'].set_color('k')
                        func_but_text_han['Surface-Bed'].set_color('k')
                        func_but_text_han['Depth-Mean'].set_color('k')
                        func_but_text_han[but_name].set_color('r')
                        z_meth = z_meth_default    
                        reload_map = True
                        reload_ts = True
                    elif but_name in ['Save Figure']:                        
                        save_figure_funct()

                    elif but_name in mode_name_lst:
                        if mode == 'Loop': 
                            mouse_in_Click = False
                        mode = but_name
                        func_but_text_han['Click'].set_color('k')
                        func_but_text_han['Loop'].set_color('k')
                        func_but_text_han[mode].set_color('gold')
                        reload_map = True
                        reload_ew = True
                        reload_ns = True
                        reload_hov = False
                        reload_ts = False
                    elif but_name in 'Quit':
                        print('Closing')
                        print('')
                        print('')
                        print('')
                        return
                    else:
                        print(but_name)
                        print('No function for but_name')
                        pdb.set_trace()
                    print(clim)
                        
                        

            plt.sca(ax[0])
                    
            
            ###################################################################################################
            ### remove contours, colorbars, images, lines, text, ready for next cycle
            ###################################################################################################

            
            if verbose_debugging: print('Interpret Mouse click: remove lines and axes', datetime.now())
            #pdb.set_trace()
            #print(ii,jj, ti, zz,var)
            print("selected ii = %i,jj = %i,ti = %i,zz = %i, var = '%s'"%(ii,jj, ti, zz,var))
            # after selected indices and vareiabels, delete plots, ready for next cycle
            for tmp_cax in cax:tmp_cax.remove()


            for tmp_pax in pax:tmp_pax.remove()
            for tmp_cs_line in cs_line:tmp_cs_line.remove()
            rem_loc = tsax.pop(0)
            rem_loc.remove()


            rem_loc2 = tsax2.pop(0)
            rem_loc2.remove()


            cs_plot_1_pop = cs_plot_1.pop()
            cs_plot_1_pop.remove()
            cs_plot_2_pop = cs_plot_2.pop()
            cs_plot_2_pop.remove()

            
            # remove contour before next iteration
            for tmpconax in conax:
                for c in tmpconax.collections: 
                    c.remove()

            
            # sometime when it crashes, it adds additional colorbars. WE can catch this be removing any colorbars from the figure... 
            #   however, this doesn't reset the axes size, so when the new colorbar is added, the axes is reduced in size. 
            #   maybe better to specify axes and colobar location, rathar than using subplot, and colorbar().
            for child in fig.get_children():
                child.__class__.__name__
                if child.get_label() == '<colorbar>': child.remove()
            
            if verbose_debugging: print('Cycle', datetime.now())

            stage_timer[2] = datetime.now() # after end of cycle
            stage_timer_name[2] = 'Cycle ended'


def main():
    

    nemo_slice_zlev_helptext=textwrap.dedent('''\
    Interactive NEMO ncfile viewer.
    ===============================
    Developed by Jonathan Tinker Met Office, UK, December 2023
    ==========================================================
    
    When calling from the command line, it uses a mix of positional values, and keyword value pairs, via argparse.

    The first two positional keywords are the NEMO configuration "config", 
    and the second is the list of input file names "fname_lst"
    
    config: should be AMM7, AMM15, CO9p2, ORCA025, ORCA12. Other configurations will be supported soon. 
    fname_lst: supports wild cards, but should be  enclosed in quotes.
    e.g.
    python NEMO_nc_slevel_viewer_dev.py amm15 "/directory/to/some/files/prodm_op_am-dm.gridT*-36.nc" 

    if using a variable in the file list use:


    fig_fname_lab=dataset1
    fig_fname_lab_2nd=dataset1


    flist1=$(echo "/directory/to/some/files/${fig_fname_lab}/prodm_op_am-dm.gridT*-36.nc)
    flist2=$(echo "/directory/to/some/files/${fig_fname_lab_2nd}/prodm_op_am-dm.gridT*-36.nc)

    Optional arguments are give as keyword value pairs, with the keyword following a double hypen.
    We will list the most useful options first.

    --zlim_max - maximum depth to show, often set to 200. Default is None
    
    --fname_lst_2nd - secondary file list, to show the different between two sets of files. 
        Enclose in quotes. Make sure this has the same number of files, with the same dates as 
        fname_lst. This will be checked in later upgrades, but will currently fail if the files
        are inconsistent

    --config_2nd - it is now possible to compare two differnt amm7 and amm15 data, although there is currently reduced functionality (to be added)

    --U_fname_lst - specify a consistent set of U and V files, to calculate a drived variable current magintude. 
        assumes the variable vozocrtx is present. Later upgrade will allow the plotting of vectors, 
        and to handle other current variable names. Must have both U_fname_lst and V_fname_lst.
    --V_fname_lst - specify a consistent set of U and V files, to calculate a drived variable current magintude. 
        assumes the variable vomecrty is present. Later upgrade will allow the plotting of vectors, 
        and to handle other current variable names. Must have both U_fname_lst and V_fname_lst.
        
    --U_fname_lst_2nd as above for a second data set
    --V_fname_lst_2nd as above for a second data set
    
    --ii            initial ii value
    --jj            initial jj value
    --ti            initial ti value
    --zz            initial zz value
    --lon           initial lon value
    --lat           initial lat value
    --date_ind      initial date value in '%Y%m%d' format, or a differnt format with --date_fmt
    --date_fmt      format for reading dates
    
    When displaying large datasets it can take a long time to load the file (connecting with xarray vis open_mfdataset). 
    When a button press requires new data to be display that can also take time. The slowest part to read new data is 
    when loading time series of data through files - uses in the hovmuller plots and the time series. There is a button
    to turn on and off reloading of these data, which can speed up the response. To speed up the initial display, 
    this can also be turned off at the command line with:
    
    --hov_time False


    Data Thinning
    =============
    To speed up handling of large files, you can "thin" the data, only loading every x row and column of the data:
        data[th['y0']:th['y1']:th['dy'],th['x0']:th['x1']:th['dx']]

    When commparing two data sets, you can thin them separately, with thin_2nd

    You can also thin how many files are read in, using thin_files, which skips files, in the file list,
    or thin_files_0 and thin_files_1 to start and end at files within the file list

    use the option --thin 5, --thin_2nd 5, --thin_files 5

    e.g.
    
    --thin      thin the data, to only load the xth row and column
    --thin_2nd  thin the data of the second data set, if of a differnt configuration.
    
    or thinned temporally, skipping some of the files: 
    
    --thin_files        thin the data, to only load the xth file
    --thin_files_0      thin the data, to only load the files after the xth
    --thin_files_1      thin the data, to only load the files before the xth
    
    It is also possible to only load a reduced region:
    
    --thin_x0   first row to load
    --thin_x1   last row to load
    --thin_y0   first column to load
    --thin_y1   last column to load
    
    --thin_x0_2nd   first row to load of the second data set, if of a differnt configuration.
    --thin_x1_2nd   last row to load of the second data set, if of a differnt configuration.
    --thin_y0_2nd   first column to load of the second data set, if of a differnt configuration.
    --thin_y1_2nd   last column to load of the second data set, if of a differnt configuration.
    
    It is possible to save figures, these will also have text files with the settings to recreate the figure
    at a higher resolution (more files, less thining) with just plot

    --fig_dir - directory for figure output
    --fig_lab - label to add to filesnames, so can compare runs.
    --fig_cutout - save full screen, or cut off the buttons - this is the defaulted to True

    --clim_sym use a symetrical colourbar -defaulted to False
    --clim_pair use the same color limits between datasets. Can be changed with a button click
    --use_cmocean - use cmocean colormaps -defaulted to False

    --verbose_debugging - prints out lots of statements at run time, to help debug -defaulted to False


    Planned upgrades:
    =================
    Plot current vectors.

    add density

    output ncfiles of data

    Using NEMO_nc_slevel_viewer.
    ============================

    
    Overview
    ========
    When the viewer loads, there is a series of variable buttons on the left hand side, fuction buttons on the right hand side, and subplots.
    The main subplot is on the left, which is  2d lon lat surface plot. The right hand plots (top to bottom) show a zonal and meridonial slice, 
    a hovmoller plot and a timeseries. The active location is showns as crosshairs on each subplot. 

    Changing the current location
    =============================
    You can change the horizontal location by clicking on the map, or the either of the slices. YOu can change the depth by clicking on the hovmuller plots, 
    and change the time by clicking on the time series. 

    The viewer initially shows the surface slice, and the viewer is in depth level mode (Note the Depth Level button is red on the right hand side). 
    When you change the depth by clicking on the hovmuller diagram, you take a z slice though AMM scoorinates, therefore the coastline 
    changes when you go deeper. If you want to see the surface, the bed, or the surface minus bed, you can click the buttons on the right hand side.
    these will change to red depending on your choice - remembering to click twice.  When you wnat to go back to the depth level, click back on depth level.
    
    
    Changing variables
    ==================
    You can change variables by clicking (twice) on the variable buttons on the left hand side. the current variable is in red. 3d variables are have black boxes
    2d variables have green boxes, derived variables have blue boxes
    
    Changing Datasets
    ==================
    You can load two data sets using --fname_lst_2nd, and then switch between the dataset, and show there differnce with the "Dataset 1", "Dataset 2", "Dat1-Dat2", "Dat2-Dat1" buttons.

    Loop and Click Modes
    ==================
    The default mode is "Click", to use the mouse to click the buttons, and figures... in this mode, the program awaits a mouse click to continue. 
    The other mode is "Loop", where the timeslices are looped throught. This mode does not await a mouse click to continue, 
    and so clickng on the other buttons will not exit this mode. Instead, we track the mouse location, and see when you point to the "Click" button, and wait.
    The next iteration will allow you to click on "Click" to continue. 
    
    Zooming
    =======

    You can zoom, by .
        1) clicking on the zoom button, 
        2) clicking on the map at the bottom left hand point of your area of interest, 
        3) clicking on the map at the top right hand point of your area of interest, 
        4) clicking on some white space.

    You can reset the zoom by clicking Reset zoom, and the white space
    

    Colour Zooming
    ==============
    The default colormap limits are based on the 5th and 95th percentile value that occurs within the subplot.
    If you can want tighter colour limits you can zoom the colorbar, reset to the original default values, or zoom out.
    
    To zoom in on the colourbar
        1)  Click Clim: Zoom
        2)  Click on the colorbar of the map (left hand subplot) at the desired lower colour limit
        3)  Click on the desired upper colour limit of the colorbar.
        4)  Click on white space.

    To zoom out of the colorbar (double the colorbar range, with the same middle value)
        1) Click Clim: Expand
        2) Click whitespace
    
    To reset the default colorbar limits
        1) Click Clim: Reset
    
    Colourmap scaling
    =================
    You can set the colorbar to logarithmic or normal.
    However there appears to be a matplotlib bug with logarithmic colorbars
        All the colorbars share the same colour limits when in log scale. 

    It doesn't appear to work when comparing two sets of files.
    It doens't handle negative values very well. 
    


    Saving figures
    ==============
    You can take snap shots of the screen by clicking Save Figure, and then clicking white space. 
    Files will be saved in the dirertory given with the --fig_dir option.
    Figures will be named based on the variable, ii,jj, ti and zz location, and with a figure label
    given with the --fig_lab option. By default, the savedfigure will exclude the buttons. If you want
    the full screen (or the cut out is not optimised) use  the --fig_cutout False option.

    Just plotting
    =============
    When analysing large datasets, the loading and interactivity can be slow. thinnig the data allows 
    reasonable performance at reduce resolution. One approach is to use this low-res option to find 
    intersting features, then save the figure and the options in an text files. These can then be edited
    (e.g. reducing the thinning), and the viewer can be run in "justplot" mode, where it loads the data
    and saves the figures without any interactivity. This can even be run on spice.
    
    --justplot True                 Just plot mode
    --justplot_date_ind             additional dates to plot
    --justplot_secdataset_proc      datasets to plot
    --justplot_z_meth_zz            depths to plot

    Quit
    ====
    Click quit, then white space. The figure should close. 


    Developed by Jonathan Tinker Met Office, UK, December 2023
    ==========================================================
    
    ''')

    if sys.argv.__len__() > 1:

        #https://towardsdatascience.com/a-simple-guide-to-command-line-arguments-with-argparse-6824c30ab1c3
        parser = argparse.ArgumentParser(description='An interactive tool for plotting NEMO data',
            formatter_class=argparse.RawDescriptionHelpFormatter,  
            epilog=nemo_slice_zlev_helptext)



        parser.add_argument('config', type=str, help="AMM7, AMM15, CO9P2, ORCA025, ORCA025EXT or ORCA12")# Parse the argument
        parser.add_argument('fname_lst', type=str, help='Input file list, enclose in "" more than simple wild card')

        parser.add_argument('--zlim_max', type=int, required=False)
        parser.add_argument('--var', type=str)# Parse the argument

        parser.add_argument('--fname_lst_2nd', type=str, required=False, help='Input file list, enclose in "" more than simple wild card, Check this has the same number of files as the fname_lst')
        parser.add_argument('--config_2nd', type=str, required=False, help="Only AMM7, AMM15. No implemented CO9P2, ORCA025, ORCA025EXT or ORCA12")# Parse the argument

        parser.add_argument('--U_fname_lst', type=str, required=False, help='Input U file list for current magnitude. Assumes file contains vozocrtx, enclose in "" more than simple wild card')
        parser.add_argument('--V_fname_lst', type=str, required=False, help='Input U file list for current magnitude. Assumes file contains vomecrty, enclose in "" more than simple wild card')
        parser.add_argument('--U_fname_lst_2nd', type=str, required=False, help='Input U file list for current magnitude. Assumes file contains vozocrtx, enclose in "" more than simple wild card')
        parser.add_argument('--V_fname_lst_2nd', type=str, required=False, help='Input U file list for current magnitude. Assumes file contains vomecrty, enclose in "" more than simple wild card')


        parser.add_argument('--preload_data', type=str, required=False)
        parser.add_argument('--allow_diff_time', type=str, required=False)


        parser.add_argument('--thin', type=int, required=False)
        parser.add_argument('--thin_2nd', type=int, required=False)

        parser.add_argument('--thin_x0', type=int, required=False)
        parser.add_argument('--thin_x1', type=int, required=False)
        parser.add_argument('--thin_y0', type=int, required=False)
        parser.add_argument('--thin_y1', type=int, required=False)

        parser.add_argument('--thin_files', type=int, required=False)
        parser.add_argument('--thin_files_0', type=int, required=False)
        parser.add_argument('--thin_files_1', type=int, required=False)


        parser.add_argument('--xlim', type=float, required=False, nargs = 2)
        parser.add_argument('--ylim', type=float, required=False, nargs = 2)
        #parser.add_argument('--tlim', type=str, required=False)
        parser.add_argument('--clim', type=float, required=False, nargs = 8)

        parser.add_argument('--ii', type=int, required=False)
        parser.add_argument('--jj', type=int, required=False)
        parser.add_argument('--ti', type=int, required=False)
        parser.add_argument('--zz', type=int, required=False)

        parser.add_argument('--lon', type=float, required=False)
        parser.add_argument('--lat', type=float, required=False)
        parser.add_argument('--date_ind', type=str, required=False)
        parser.add_argument('--date_fmt', type=str, required=False)


        parser.add_argument('--fig_fname_lab', type=str, required=False)
        parser.add_argument('--fig_fname_lab_2nd', type=str, required=False)
        parser.add_argument('--z_meth', type=str, help="z_slice, ss, nb, df, zm, or z_index for z level models")# Parse the argument

        parser.add_argument('--secdataset_proc', type=str, required=False)

        parser.add_argument('--hov_time', type=str, required=False)
        parser.add_argument('--do_cont', type=str, required=False)
        parser.add_argument('--do_grad', type=int, required=False)

        parser.add_argument('--clim_sym', type=str, required=False)
        parser.add_argument('--clim_pair', type=str, required=False)
        parser.add_argument('--use_cmocean', type=str, required=False)

        parser.add_argument('--ld_lst', type=str, required=False)
        parser.add_argument('--ld_lab_lst', type=str, required=False)
        parser.add_argument('--ld_nctvar', type=str, required=False)



        parser.add_argument('--fig_dir', type=str, required=False, help = 'if absent, will default to $PWD/tmpfigs')
        parser.add_argument('--fig_lab', type=str, required=False, help = 'if absent, will default to figs')
        parser.add_argument('--fig_cutout', type=str, required=False)
        #parser.add_argument('--fig_cutout', type=str, required=False)
        
        parser.add_argument('--justplot', type=str, required=False)
        parser.add_argument('--justplot_date_ind', type=str, required=False, help = 'comma separated values')
        parser.add_argument('--justplot_z_meth_zz', type=str, required=False, help = 'comma separated values, replace space with underscore - e.g. "Dataset_1"')
        parser.add_argument('--justplot_secdataset_proc', type=str, required=False, help = 'comma separated values')

        parser.add_argument('--verbose_debugging', type=str, required=False)


        args = parser.parse_args()# Print "Hello" + the user input argument


        
        # Handling of Bool variable types
        #



        if args.preload_data is None:
            preload_data_in=True
        elif args.preload_data is not None:
            if args.preload_data.upper() in ['TRUE','T']:
                preload_data_in = bool(True)
            elif args.preload_data.upper() in ['FALSE','F']:
                preload_data_in = bool(False)
            else:                
                print(args.preload_data)
                pdb.set_trace()

        if args.allow_diff_time is None:
            allow_diff_time_in=False
        elif args.allow_diff_time is not None:
            if args.allow_diff_time.upper() in ['TRUE','T']:
                allow_diff_time_in = bool(True)
            elif args.allow_diff_time.upper() in ['FALSE','F']:
                allow_diff_time_in = bool(False)
            else:                
                print(args.allow_diff_time)
                pdb.set_trace()

        if args.clim_sym is None:
            clim_sym_in=False
        elif args.clim_sym is not None:
            if args.clim_sym.upper() in ['TRUE','T']:
                clim_sym_in = bool(True)
            elif args.clim_sym.upper() in ['FALSE','F']:
                clim_sym_in = bool(False)
            else:                
                print(args.clim_sym)
                pdb.set_trace()

        if args.clim_pair is None:
            clim_pair_in=True
        elif args.clim_pair is not None:
            if args.clim_pair.upper() in ['TRUE','T']:
                clim_pair_in = bool(True)
            elif args.clim_pair.upper() in ['FALSE','F']:
                clim_pair_in = bool(False)
            else:                
                print(args.clim_pair)
                pdb.set_trace()

        if args.hov_time is None:
            hov_time_in=False
        elif args.hov_time is not None:
            if args.hov_time.upper() in ['TRUE','T']:
                hov_time_in = bool(True)
            elif args.hov_time.upper() in ['FALSE','F']:
                hov_time_in = bool(False)
            else:                
                print(args.hov_time)
                pdb.set_trace()

        if args.fig_cutout is None:
            fig_cutout_in=True
        elif args.fig_cutout is not None:
            if args.fig_cutout.upper() in ['TRUE','T']:
                fig_cutout_in = bool(True)
            elif args.fig_cutout.upper() in ['FALSE','F']:
                fig_cutout_in = bool(False)
            else:                
                print(args.fig_cutout)
                pdb.set_trace()

        if args.justplot is None:
            justplot_in=False
        elif args.justplot is not None:
            if args.justplot.upper() in ['TRUE','T']:
                justplot_in = bool(True)
            elif args.justplot.upper() in ['FALSE','F']:
                justplot_in = bool(False)
            else:                
                print(args.justplot)
                pdb.set_trace()

        if args.use_cmocean is None:
            use_cmocean_in=False
        elif args.use_cmocean is not None:
            if args.use_cmocean.upper() in ['TRUE','T']:
                use_cmocean_in = bool(True)
            elif args.use_cmocean.upper() in ['FALSE','F']:
                use_cmocean_in = bool(False)
            else:                
                print(args.use_cmocean)
                pdb.set_trace()

        if args.verbose_debugging is None:
            verbose_debugging_in=False
        elif args.verbose_debugging is not None:
            if args.verbose_debugging.upper() in ['TRUE','T']:
                verbose_debugging_in = bool(True)
            elif args.verbose_debugging.upper() in ['FALSE','F']:
                verbose_debugging_in = bool(False)
            else:                
                print(args.verbose_debugging)
                pdb.set_trace()
 
        if args.do_grad is None:do_grad_in=0

        if args.do_cont is None:
            do_cont_in=False
        elif args.do_cont is not None:
            if args.do_cont.upper() in ['TRUE','T']:
                do_cont_in = bool(True)
            elif args.do_cont.upper() in ['FALSE','F']:
                do_cont_in = bool(False)
            else:                
                print(args.do_cont)
                pdb.set_trace()

        '''

        if args.boolvar is None:
            boolvar_in=True
        elif args.boolvar is not None:
            if args.boolvar.upper() in ['TRUE','T']:
                boolvar_in = bool(True)
            elif args.boolvar.upper() in ['FALSE','F']:
                boolvar_in = bool(False)
            else:                
                print(args.boolvar)
                pdb.set_trace()


        '''
        #set default values for None

        if args.fig_dir is None: args.fig_dir=script_dir + '/tmpfigs'
        if args.fig_lab is None: args.fig_lab='figs'
        if args.ld_nctvar is None: args.ld_nctvar='time_counter'



        if args.date_fmt is None: args.date_fmt='%Y%m%d'

        #print('justplot',args.justplot)

        if args.thin is None: args.thin=1
        if args.thin_2nd is None: args.thin_2nd=1
        if args.thin_files is None: args.thin_files=1
        if args.thin_files_0 is None: args.thin_files_0=0
        if args.thin_files_1 is None: args.thin_files_1=None

        if args.thin_x0 is None: args.thin_files_0=0
        if args.thin_x1 is None: args.thin_files_1=None
        if args.thin_y0 is None: args.thin_files_0=0
        if args.thin_y1 is None: args.thin_files_1=None

        #Deal with file lists
        print(args.fname_lst)
        fname_lst = glob.glob(args.fname_lst)
        fname_lst.sort()
        fname_lst_2nd = None
        U_fname_lst = None
        V_fname_lst = None
        U_fname_lst_2nd = None
        V_fname_lst_2nd = None

        if args.fname_lst_2nd is not None:fname_lst_2nd = glob.glob(args.fname_lst_2nd)
        if args.U_fname_lst is not None:U_fname_lst = glob.glob(args.U_fname_lst)
        if args.V_fname_lst is not None:V_fname_lst = glob.glob(args.V_fname_lst)
        if args.U_fname_lst_2nd is not None:U_fname_lst_2nd = glob.glob(args.U_fname_lst_2nd)
        if args.V_fname_lst_2nd is not None:V_fname_lst_2nd = glob.glob(args.V_fname_lst_2nd)

        if fname_lst_2nd is not None:fname_lst_2nd.sort()
        if U_fname_lst is not None:U_fname_lst.sort()
        if V_fname_lst is not None:V_fname_lst.sort()
        if U_fname_lst_2nd is not None:U_fname_lst_2nd.sort()
        if V_fname_lst_2nd is not None:V_fname_lst_2nd.sort()
        if len(fname_lst) == 0: 
            print('no files passed')
            pdb.set_trace()
    
        
        nemo_slice_zlev(fname_lst,zlim_max = args.zlim_max, config = args.config, config_2nd = args.config_2nd,
            U_fname_lst = U_fname_lst, V_fname_lst = V_fname_lst,
            fname_lst_2nd = fname_lst_2nd,
            U_fname_lst_2nd = U_fname_lst_2nd, V_fname_lst_2nd = V_fname_lst_2nd,
            clim_sym = clim_sym_in, clim = args.clim, clim_pair = clim_pair_in,hov_time = hov_time_in,
            allow_diff_time = allow_diff_time_in,preload_data = preload_data_in,
            do_grad = do_grad_in,do_cont = do_cont_in,
            use_cmocean = use_cmocean_in, date_fmt = args.date_fmt,
            justplot = justplot_in,justplot_date_ind = args.justplot_date_ind,
            justplot_secdataset_proc = args.justplot_secdataset_proc,
            justplot_z_meth_zz = args.justplot_z_meth_zz,
            fig_fname_lab = args.fig_fname_lab, fig_fname_lab_2nd = args.fig_fname_lab_2nd, 
            thin = args.thin, thin_2nd = args.thin_2nd,
            thin_files = args.thin_files, thin_files_0 = args.thin_files_0, thin_files_1 = args.thin_files_1, 
            thin_x0 = args.thin_x0, thin_x1 = args.thin_x1, thin_y0 = args.thin_y0, thin_y1 = args.thin_y1, 
            ii = args.ii, jj = args.jj, ti = args.ti, zz = args.zz, 
            lon_in = args.lon, lat_in = args.lat, date_in_ind = args.date_ind,
            var = args.var, z_meth = args.z_meth,
            xlim = args.xlim,ylim = args.ylim,
            secdataset_proc = args.secdataset_proc,
            ld_lst = args.ld_lst, ld_lab_lst = args.ld_lab_lst, ld_nctvar= args.ld_nctvar,
            fig_dir = args.fig_dir, fig_lab = args.fig_lab,fig_cutout = fig_cutout_in,
            verbose_debugging = verbose_debugging_in)


        exit()



if __name__ == "__main__":
    main()


