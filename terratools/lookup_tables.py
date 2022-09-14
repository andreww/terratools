import numpy as np
from .utils import norm_vals, int_linear
from scipy.interpolate import interp2d, interp1d
import os
import matplotlib.pyplot as plt




class SeismicLookupTable:
    def __init__(self,table_path):
        """
        Inputs: table_path = '/path/to/data/table/'

        Example: basalt = lookup_tables.SeismicLookupTable('/path/to/basalt/table.dat')
        """
        try:
            self.table=np.genfromtxt(f'{table_path}')
        except:
            self.table=np.genfromtxt(f'{table_path}',skip_header=1)


        self.P = self.table[:,0]
        self.T = self.table[:,1]
        self.pres=np.unique(self.table[:,0])
        self.temp=np.unique(self.table[:,1])
        self.n_uniq_p = len(self.pres)
        self.n_uniq_t = len(self.temp)
        self.t_max=np.max(self.temp)
        self.t_min=np.min(self.temp)
        self.p_max=np.max(self.pres)
        self.p_min=np.min(self.pres)
        self.pstep=np.size(self.temp)

        #Initialise arrays for storing table columns in Temp-Pressure space
        Vp=np.zeros((len(self.temp),len(self.pres)))
        Vs=np.zeros((len(self.temp),len(self.pres)))
        Vp_an=np.zeros((len(self.temp),len(self.pres)))
        Vs_an=np.zeros((len(self.temp),len(self.pres)))
        Vphi=np.zeros((len(self.temp),len(self.pres)))
        Dens=np.zeros((len(self.temp),len(self.pres)))
        Qs=np.zeros((len(self.temp),len(self.pres)))
        T_sol=np.zeros((len(self.temp),len(self.pres)))

        #Fill arrays with table data
        for i, p in enumerate(self.pres):
            Vp[:,i]=self.table[0+(i*self.pstep):self.pstep+(i*self.pstep),2]
            Vs[:,i]=self.table[0+(i*self.pstep):self.pstep+(i*self.pstep),3]
            Vp_an[:,i]=self.table[0+(i*self.pstep):self.pstep+(i*self.pstep),4]
            Vs_an[:,i]=self.table[0+(i*self.pstep):self.pstep+(i*self.pstep),5]
            Vphi[:,i]=self.table[0+(i*self.pstep):self.pstep+(i*self.pstep),6]
            Dens[:,i]=self.table[0+(i*self.pstep):self.pstep+(i*self.pstep),7]
            Qs[:,i]=self.table[0+(i*self.pstep):self.pstep+(i*self.pstep),8]
            T_sol[:,i]=self.table[0+(i*self.pstep):self.pstep+(i*self.pstep),9]


        #Creat dictionary which holds the interpolator objects
        self.fields = {'vp': [2, Vp, 'km/s'], 'vs': [3,Vs, 'km/s'], 'vp_ani': [4, Vp_an, 'km/s'],
                      'vs_ani': [5, Vs_an, 'km/s'], 'vphi': [6, Vphi, 'km/s'],
                      'density': [7, Dens, '$kg/m^3$'], 'qs': [8, Qs, 'Hz'], 't_sol': [9, T_sol, 'K']}


        #Setup interpolator objects. These can be used for rapid querying of many individual points
        self.vp_interp = interp2d(self.pres,self.temp,Vp)
        self.vs_interp = interp2d(self.pres,self.temp,Vs)
        self.vp_an_interp = interp2d(self.pres,self.temp,Vp_an)
        self.vs_an_interp = interp2d(self.pres,self.temp,Vs_an)
        self.vphi_interp = interp2d(self.pres,self.temp,Vphi)
        self.density_interp = interp2d(self.pres,self.temp,Dens)
        self.qs_interp = interp2d(self.pres,self.temp,Qs)
        self.t_sol_interp = interp2d(self.pres,self.temp,T_sol)


#################################################
#Need to get temp, pres, comp at given point.
#Pressure could come from PREM or from simulation
#Comp will be in 3 component mechanical mixture
#We will then find the
#################################################

    def get_vals(self,pval,tval):
        """
        Inputs: pval=pressure at point
                tval=temperature at point
        Returns: Vp, Vs, Vp_an, Vs_an, Vphi, Dens
        For a given temperature and pressure, find the locations of the
        upper and lower bounds in a seismic conversion table.

        Example: vp, vs, vp_an, vs_an, vphi, dens = basalt.get_vals(P,T)
         """


        #First we find the upper and lower pressure bounds
        #Include some catches in case given pressure is out of bounds
        if pval<np.min(self.table[:,0]):
            print(f'#Error - Pressure {pval} less than minimum value in lookup tables')
            pu=np.min(self.table[:,0])
            pl=pu
        elif pval>np.max(self.table[:,0]):
            print(f'#Warning - Pressure {pval} exceeds maximum value in lookup tables')
            pu=np.max(self.table[:,0])
            pl=pu
        else:
            #Find the lower (pl) and upper (pu) bounds of pressure
            ipx = np.where(np.abs(self.table[:,0]-pval) == np.min(np.abs(self.table[:,0]-pval)))[0]
            if self.table[ipx[0],0]-pval < 0 :
                pl=self.table[ipx[0],0] ; pu=self.table[ipx[0]+self.pstep,0]
            else:
                pl=p2=self.table[ipx[0]-self.pstep,0] ; pu=self.table[ipx[0],0]



        #Now find upper and lower temperature bounds
        #Include catches in case given temp is out of bounds
        if tval<np.min(self.table[:,1]):
            print(f'#Warning - Temperature {tval} less than minimum value in lookup tables')
            tu=np.min(self.table[:,1])
            tl=tu
        elif tval>np.max(self.table[:,1]):
            print(f'#Warning - Temperature {tval} exceeds maximum value in lookup tables')
            tu=np.max(self.table[:,1])
            tl=tu
        else:
            #Find the lower (tl) and upper (tu) bounds of temperature
            itx = np.where(np.abs(self.table[:,1]-tval) == np.min(np.abs(self.table[:,1]-tval)))[0]
            if self.table[itx[0],1]-tval < 0 :
                tl=self.table[itx[0],1] ; tu=self.table[itx[0]+1,1]
            else:
                tl=self.table[itx[0]-1,1] ; tu=self.table[itx[0],1]


        #Now find the 4 indices (pl,tl) (pl,tu) (pu,tl) (pu,tu)
        ipltl=np.intersect1d(np.where(self.table[:,0]==pl),np.where(self.table[:,1]==tl))
        ipltu=np.intersect1d(np.where(self.table[:,0]==pl),np.where(self.table[:,1]==tu))

        iputl=np.intersect1d(np.where(self.table[:,0]==pu),np.where(self.table[:,1]==tl))
        iputu=np.intersect1d(np.where(self.table[:,0]==pu),np.where(self.table[:,1]==tu))

        #Normalise input against bounds
        tnorm=norm_vals(tval,tu,tl)
        pnorm=norm_vals(pval,pu,pl)


        Vp=int_linear(self.table[ipltl,2],self.table[ipltu,2],
                self.table[iputl,2],self.table[iputu,2],tnorm,pnorm)
        Vs=int_linear(self.table[ipltl,3],self.table[ipltu,3],
                self.table[iputl,3],self.table[iputu,3],tnorm,pnorm)
        Vp_an=int_linear(self.table[ipltl,4],self.table[ipltu,4],
                self.table[iputl,4],self.table[iputu,4],tnorm,pnorm)
        Vs_an=int_linear(self.table[ipltl,5],self.table[ipltu,5],
                self.table[iputl,5],self.table[iputu,5],tnorm,pnorm)
        Vphi=int_linear(self.table[ipltl,6],self.table[ipltu,6],
                self.table[iputl,6],self.table[iputu,6],tnorm,pnorm)
        Dens=int_linear(self.table[ipltl,7],self.table[ipltu,7],
                self.table[iputl,7],self.table[iputu,7],tnorm,pnorm)

        return Vp, Vs, Vp_an, Vs_an, Vphi, Dens


    def interp_grid(self,press,temps,field):
        """
        Routine for re-gridding lookup tables into new pressure-temperature space
        Inputs: press = pressures
                temps = temperatures
                field = data field (eg. basalt.Vs)
        Returns: interpolated values of a given table property
                on a grid defined by press and temps

        eg. basalt.interp([pressures],[temperature],'Vs')
        """

        grid=interp2d(self.pres,self.temp,self.fields[field.lower()][1])

        return grid(press,temps)



    def interp_points(self,press,temps,field):
        """
        Inputs: press = pressures
                temps = temperatures (press and temps must be of equal length)
                prop   = property eg. Vs
        Returns:
        For a given table property (eg. Vs) return interpolated values
        for pressures and temperatures
        eg. basalt.interp_points(list(zip(pressures,temperature)),'Vs')
        """

        #If integers are passed in then convert to indexable lists
        press = [press] if type(press)==int or type(press)==float else press
        temps = [temps] if type(temps)==int or type(temps)==float else temps

        grid=interp2d(self.pres,self.temp,self.fields[field.lower()][1])


        out=np.zeros(len(press))
        for i in range(len(press)):
            out[i]=grid(press[i],temps[i])

        return out


    def plot_table(self, ax, field, cmap='viridis_r'):
        """
        Plots the lookup table as a grid with values coloured by
        value for the field given.

        Inputs: ax = matplotlib axis object to plot on.
                field = property to plot e.g. Vp.
                cmap = matplotlib colourmap. default is cividis

        Returns:

        """

        # get column index for field of interest
        units = self.fields[field.lower()][2]
        data = self.fields[field.lower()][1]

        # temperature on x axis
        data=data.transpose()
        print(data.shape)



        chart = ax.imshow(data, origin = 'lower', extent = [self.t_min, self.t_max, self.p_min, self.p_max],
                          cmap=cmap, aspect='auto')

        # chart = ax.tricontourf(self.P,self.T,self.table[:,i_field])

        plt.colorbar(chart, ax=ax, label=f'{field} ({units})')
        ax.set_xlabel('Temperature (K)')
        ax.set_ylabel('Pressure (Pa)')
        ax.set_title(f'P-T graph for {field}')
        ax.invert_yaxis()


    def plot_table_contour(self, ax, field, cmap='viridis_r'):
        """
        Plots the lookup table as contours using matplotlibs tricontourf.

        Inputs: ax = matplotlib axis object to plot on.
                field = property to plot e.g. Vp.
                cmap = matplotlib colourmap. default is cividis

        Returns:

        """

        # get column index for field of interest
        i_field = self.fields[field.lower()][0]
        units = self.fields[field.lower()][1]
        data = self.table[:,i_field]

        chart = ax.tricontourf(self.P,self.T,self.table[:,i_field], cmap=cmap)

        # chart = ax.tricontourf(self.P,self.T,self.table[:,i_field])

        plt.colorbar(chart, ax=ax, label=f'{field} ({units})')
        ax.set_ylabel('Temperature (K)')
        ax.set_xlabel('Pressure (Pa)')
        ax.set_title(f'P-T graph for {field}')


def harmonic_mean_comp(bas,lhz,hzb,bas_fr,lhz_fr,hzb_fr):
    """
    Input: bas = data for basaltic composition (eg. basalt.Vs)
           lhz = data for lherzolite composition
           hzb = data for harzburgite composition
           bas_fr = basalt fraction
           lhz_fr = lherzolite fraction
           hzb_fr = harzburgite fraction
    Returns: hmean = harmonic mean of input values

    bas, lhz, hzb must be of equal length
    This routine assumes 3 component mechanical mixture

    """
    m1=(1./bas)*bas_fr
    m2=(1./lhz)*lhz_fr
    m3=(1./hzb)*hzb_fr

    hmean=1/(m1+m2+m3)

    return hmean

def linear_interp_1d(vals1, vals2, c1, c2, cnew):
    """
    Inputs: v1 = data for composition 1
            v2 = data for composition 2
            c1 = C-value for composition 1
            c2 = C-value for composition 2
            cnew  = C-value(s) for new composition(s)

    Returns: interpolated values for compostions cnew
    """

    interpolated = interp1d(np.array([c1,c2]),[vals1.flatten(),vals2.flatten()],
                            fill_value='extrapolate',axis=0)


    return interpolated(cnew)
