from astropy.coordinates import SkyCoord, EarthLocation
import ast
from astropy.utils.data import clear_download_cache

clear_download_cache()
from astroplan import FixedTarget, is_observable, AltitudeConstraint, MoonSeparationConstraint, AtNightConstraint
from astroplan import Observer, moon_illumination, is_always_observable
from astroquery.mast import Catalogs
from colorama import Fore
import datetime
import os
import sys
import shutil
import numpy as np
import pandas as pd
import SPOCK_chilean.ETC as ETC
from SPOCK_chilean.txt_files import startup, flatexo_gany, flatexo_io, flatexo_euro, flatexo_calli
from SPOCK_chilean.txt_files import first_target, flatdawn, biasdark
from SPOCK_chilean import path_spock_chilean
from astropy.time import Time
from astropy.table import Table
from astropy import units as u
from astropy.utils import iers

iers.IERS_A_URL = 'https://datacenter.iers.org/data/9/finals2000A.all'  # 'http://maia.usno.navy.mil/ser7/finals2000A.all'#'ftp://cddis.gsfc.nasa.gov/pub/products/iers/finals2000A.all'


# iers.IERS_A_URL  ='ftp://cddis.gsfc.nasa.gov/pub/products/iers/finals2000A.all'
# from astroplan import download_IERS_A
# download_IERS_A()


class chilean_time:
    """ Create and check ACP plans for 10% of SSO's on-sky-time dedicated to chilean observations

    """

    def __init__(self, start_date, telescope):
        """

        Parameters
        ----------
        start_date : date
        """

        self.start_date = start_date
        self.Path = path_spock_chilean + '/../Plans_by_date/' + str(Time(start_date, out_subfmt='date').value)
        self.telescope = telescope
        self.path_night_blocks = path_spock_chilean + '/../Archive_night_blocks_chilean/' + \
                                 'night_blocks_' + str(telescope) + '_' + str(Time(start_date,
                                                                                   out_subfmt='date').value) + '.txt'
        self.location = EarthLocation.from_geodetic(-70.40300000000002 * u.deg, -24.625199999999996 * u.deg,
                                                    2635.0000000009704 * u.m)
        self.observatory = Observer(location=self.location, name="SSO", timezone="UTC")
        self.time_start = None
        self.time_end = None

    def make_ACP_plans(self, target_chilean):
        """ Make plans from basic information of each target

        Parameters
        ----------
        target_chilean : pd.DataFrame

        Returns
        -------
        txt files
            set of ACP format file required for the observations

        """

        try:
            os.mkdir(self.Path)
        except FileExistsError:
            print(Fore.GREEN + 'INFO: ' + Fore.BLACK + 'File for date '
                  + str(Time(self.start_date, out_subfmt='date')) + ' exists, overwriting')
            shutil.rmtree(self.Path)
            os.mkdir(self.Path)

        # constants
        autofocus = None
        waitlimit = 600
        afinterval = 60
        filters_used = []

        # sun  rise and sun set
        t_day_15 = Time(datetime.datetime.strptime(self.start_date, '%Y-%m-%d') + datetime.timedelta(hours=15))
        sun_set = self.observatory.sun_set_time(t_day_15, which='next')
        sun_rise = self.observatory.sun_rise_time(t_day_15, which='next')

        for i in range(0, len(target_chilean)):
            start_between_civil_nautical = Time((self.observatory.twilight_evening_nautical(Time(self.start_date),
                                                                                            which='next').jd
                                                 + self.observatory.twilight_evening_civil(Time(self.start_date),
                                                                                           which='next').jd) / 2,
                                                format='jd')

            end_between_nautical_civil = Time((self.observatory.twilight_morning_nautical(Time(self.start_date) + 1,
                                                                                          which='nearest').jd
                                               + self.observatory.twilight_morning_civil(Time(self.start_date) + 1,
                                                                                         which='nearest').jd) / 2,
                                              format='jd')
            if i < (len(target_chilean) - 1):
                chain = target_chilean['Name'][i + 1]
            else:
                chain = None

            if target_chilean['texp'][i] == 0:
                if self.telescope == "Callisto":
                    fwhm_mean = 1.2
                    airmass_mean = 1.1
                    texp = ETC.compute_texp_precision_mphot(Teff=target_chilean['Teff'][i],
                                                            distance=target_chilean['dist'][i],
                                                            seeing_mean=fwhm_mean, airmass_mean=airmass_mean,
                                                            camera='SPIRIT')

                else:
                    texp = self.etc_andor(target_chilean['Jmag'][i], target_chilean['SpT'][i],
                                          filt=target_chilean['Filter'][i])

            else:
                texp = target_chilean['texp'][i]

            coords = SkyCoord(frame='icrs', ra=target_chilean['RA'][i], dec=target_chilean['DEC'][i],
                              unit=(u.deg, u.deg), obstime=Time(self.start_date).iso)
            if i == 0:
                if target_chilean['Start'][0] < start_between_civil_nautical:
                    target_chilean['Start'][0] = start_between_civil_nautical.iso
                if target_chilean['End'][0] > end_between_nautical_civil:
                    target_chilean['End'][0] = end_between_nautical_civil.iso

                self.time_start = Time(target_chilean['Start'][0]).iso
                self.time_end = Time(target_chilean['End'][0]).iso

                save_night_blocks(target_chilean, self.start_date, self.telescope)

                if 'Io' in self.telescope:
                    startup(target_chilean['Name'][0], sun_set.iso, self.time_start, self.Path)
                    first_target(target_chilean['Name'][0], self.time_start, self.time_end, waitlimit,
                                 afinterval, autofocus,
                                 target_chilean['Counts'][0], target_chilean['Filter'][0], texp,
                                 coords.ra.hms[0], coords.ra.hms[1], coords.ra.hms[2], coords.dec.dms[0],
                                 coords.dec.dms[1],
                                 coords.dec.dms[2], chain, target_chilean['Gaia_ID'][0], self.Path)
                if 'Europa' in self.telescope:
                    startup(target_chilean['Name'][0], sun_set.iso, self.time_start, self.Path)
                    first_target(target_chilean['Name'][0], self.time_start, self.time_end, waitlimit,
                                 afinterval, autofocus,
                                 target_chilean['Counts'][0], target_chilean['Filter'][0], texp,
                                 coords.ra.hms[0], coords.ra.hms[1], coords.ra.hms[2], coords.dec.dms[0],
                                 coords.dec.dms[1],
                                 coords.dec.dms[2], chain, target_chilean['Gaia_ID'][0], self.Path)
                if 'Ganymede' in self.telescope:
                    startup(target_chilean['Name'][0], sun_set.iso, self.time_start, self.Path)
                    first_target(target_chilean['Name'][0], self.time_start, self.time_end, waitlimit,
                                 afinterval, autofocus,
                                 target_chilean['Counts'][0], target_chilean['Filter'][0], texp,
                                 coords.ra.hms[0], coords.ra.hms[1], coords.ra.hms[2], coords.dec.dms[0],
                                 coords.dec.dms[1],
                                 coords.dec.dms[2], chain, target_chilean['Gaia_ID'][0], self.Path)
                if 'Callisto' in self.telescope:
                    startup(target_chilean['Name'][0], sun_set.iso, self.time_start, self.Path)
                    first_target(target_chilean['Name'][0], self.time_start, self.time_end, waitlimit,
                                 afinterval, autofocus,
                                 target_chilean['Counts'][0], target_chilean['Filter'][0], texp,
                                 coords.ra.hms[0], coords.ra.hms[1], coords.ra.hms[2], coords.dec.dms[0],
                                 coords.dec.dms[1],
                                 coords.dec.dms[2], chain, target_chilean['Gaia_ID'][0], self.Path)

            if i > 0:

                if target_chilean['Start'][i] < start_between_civil_nautical:
                    target_chilean['Start'][i] = start_between_civil_nautical.iso
                if target_chilean['End'][i] > end_between_nautical_civil:
                    target_chilean['End'][i] = end_between_nautical_civil.iso

                self.time_start = Time(target_chilean['Start'][i]).iso
                self.time_end = Time(target_chilean['End'][i]).iso

                if i < (len(target_chilean) - 1):
                    first_target(target_chilean['Name'][i], self.time_start, self.time_end, waitlimit,
                                 afinterval, autofocus,
                                 target_chilean['Counts'][i], target_chilean['Filter'][i], texp,
                                 coords.ra.hms[0], coords.ra.hms[1], coords.ra.hms[2], coords.dec.dms[0],
                                 coords.dec.dms[1], coords.dec.dms[2], target_chilean['Name'][i + 1],
                                 target_chilean['Gaia_ID'][i], self.Path)

                if i == len(target_chilean) - 1:
                    first_target(target_chilean['Name'][i], self.time_start, self.time_end, waitlimit, afinterval,
                                 autofocus, target_chilean['Counts'][i], target_chilean['Filter'][i], texp,
                                 coords.ra.hms[0], coords.ra.hms[1], coords.ra.hms[2], coords.dec.dms[0],
                                 coords.dec.dms[1], coords.dec.dms[2], None, target_chilean['Gaia_ID'][i], self.Path)

            filters_used.append(target_chilean['Filter'][i])

        if 'Io' in self.telescope:
            flatexo_io(self.Path, filters_used, nbu=3, nbHa=3, nbRc=3, nbz=3, nbr=3, nbi=3, nbg=3, nbIz=7,
                       nbExo=3, nbClear=3)
        if 'Europa' in self.telescope:
            flatexo_euro(self.Path, filters_used, nbRc=3, nbB=3, nbz=3, nbV=3, nbr=3, nbi=3, nbg=3, nbIz=7,
                         nbExo=3, nbClear=3)
        if 'Ganymede' in self.telescope:
            flatexo_gany(self.Path, filters_used, nbOIII=3, nbHa=3, nbSII=3, nbz=3, nbr=3, nbi=3, nbg=3, nbIz=7,
                         nbExo=3, nbClear=3)
        if 'Callisto' in self.telescope:
            flatexo_calli(self.Path, filters_used, nbu=3, nbB=3, nbz=3, nbV=3, nbr=3, nbi=3, nbg=3, nbIz=7,
                          nbExo=3, nbClear=3)

        flatdawn(self.time_end, sun_rise.iso, self.Path)
        biasdark(self.Path)
        info_message = Fore.GREEN + 'INFO: ' + Fore.BLACK + "Plans made"
        return info_message

    def make_night_block(self, target_chilean):

        for i in range(0, len(target_chilean)):

            # Exposure time and saturation
            if target_chilean['SpT'][i] is not None:
                try:
                    if self.telescope == "Callisto":
                        fwhm_mean = 1.2
                        airmass_mean = 1.1
                        texp = ETC.compute_texp_precision_mphot(Teff=target_chilean['Teff'][i],
                                                                distance=target_chilean['dist'][i],
                                                                seeing_mean=fwhm_mean, airmass_mean=airmass_mean,
                                                                camera='SPIRIT')[0]
                        target_chilean['texp'][i] =  round(texp, 0)
                        print(Fore.GREEN + 'INFO: ' + Fore.BLACK + "The optimum exposure time for " +
                                  target_chilean["Name"][i] + " SpT " +
                                  target_chilean['SpT'][i] + " and J magnitude " + str(target_chilean['Jmag'][i]) +
                                  " with Filter " + target_chilean['Filter'][i] + " is: " + str(
                                round(texp, 1)) + ' seconds')
                    else:
                        if target_chilean['Jmag'] is not None:
                            a = (ETC.etc(mag_val=target_chilean['Jmag'][i], mag_band='J', spt=target_chilean['SpT'][i],
                                         filt=target_chilean['Filter'][i].replace('\'', ''), airmass=1.1,
                                         moonphase=0.5, irtf=0.8, num_tel=1,
                                         seeing=0.75, gain=1.1))
                            texp = a.exp_time_calculator(ADUpeak=45000)[0]
                            print(Fore.GREEN + 'INFO: ' + Fore.BLACK + "The optimum exposure time for " +
                                  target_chilean["Name"][i] + " SpT " +
                                  target_chilean['SpT'][i] + " and J magnitude " + str(target_chilean['Jmag'][i]) +
                                  " with Filter " + target_chilean['Filter'][i] + " is: " + str(
                                round(texp, 1)) + ' seconds')
                            if target_chilean['texp'][i] is not None:
                                ADU_peak = a.peak_calculation(target_chilean['texp'][i])
                                if ADU_peak > 60000:
                                    print(Fore.YELLOW + 'WARNING: ' + Fore.BLACK + "the target might get saturated, "
                                                                                   "please decrease the exposure time.")
                                else:
                                    print(Fore.GREEN + 'INFO: ' + Fore.BLACK + " the exposure time chosen is ok, "
                                                                               "no saturation expected.")
                except KeyError:
                    pass

                try:
                    if target_chilean['Vmag'][i] is not None:
                        a = (ETC.etc(mag_val=target_chilean['Vmag'][i], mag_band='V', spt=target_chilean['SpT'][i],
                                     filt=target_chilean['Filter'][i].replace('\'', ''), airmass=1.1,
                                     moonphase=0.5, irtf=0.8, num_tel=1,
                                     seeing=0.75, gain=1.1))
                        texp = a.exp_time_calculator(ADUpeak=45000)[0]
                        print(Fore.GREEN + 'INFO: ' + Fore.BLACK + "The optimum exposure time for " +
                              target_chilean["Name"][i] + " SpT " +
                              target_chilean['SpT'][i] + " and V magnitude " + str(target_chilean['Vmag'][i]) +
                              " with Filter " + target_chilean['Filter'][i] + " is: " + str(
                            round(texp, 1)) + ' seconds')
                        if target_chilean['texp'][i] is not None:
                            ADU_peak = a.peak_calculation(target_chilean['texp'][i])
                            if ADU_peak > 60000:
                                print(Fore.YELLOW + 'WARNING: ' + Fore.BLACK + "the target might get saturated, "
                                                                               "please decrease the exposure time.")
                            else:
                                print(Fore.GREEN + 'INFO: ' + Fore.BLACK + " the exposure time chosen is ok, "
                                                                           "no saturation expected.")
                except KeyError:
                    pass

            start_between_civil_nautical = Time((self.observatory.twilight_evening_nautical(Time(self.start_date),
                                                                                            which='next').jd
                                                 + self.observatory.twilight_evening_civil(Time(self.start_date),
                                                                                           which='next').jd) / 2,
                                                format='jd')

            end_between_nautical_civil = Time((self.observatory.twilight_morning_nautical(Time(self.start_date) + 1,
                                                                                          which='nearest').jd
                                               + self.observatory.twilight_morning_civil(Time(self.start_date) + 1,
                                                                                         which='nearest').jd) / 2,
                                              format='jd')
            if target_chilean['Start'][i] < start_between_civil_nautical:
                target_chilean['Start'][i] = start_between_civil_nautical.iso
            if target_chilean['End'][i] > end_between_nautical_civil:
                target_chilean['End'][i] = end_between_nautical_civil.iso

        save_night_blocks(target_chilean, self.start_date, self.telescope)

    def check_plans(self):
        """ Check if plans meet constraints

        Returns
        -------
        info message
            return message to inform if the plan are ok or not

        """
        check_ok = False
        target_name = None
        for rr, dd, ff in os.walk(self.Path):
            for f in sorted(ff, reverse=True):
                if f.startswith('startup'):
                    file_startup = open(os.path.join(self.Path, f), 'r')
                    for line in file_startup:
                        if line.startswith('#waituntil 1,'):
                            self.start_date = line[14:].replace('\n', '')
                            self.start_date = self.start_date.replace('/', '-')
                            twilight_evening = self.observatory.twilight_evening_nautical(Time(self.start_date),
                                                                                          which='nearest')
                            twilight_morning = self.observatory.twilight_morning_nautical(Time(self.start_date),
                                                                                          which='next')
                            break
                elif f.startswith('Obj_'):
                    file = open(os.path.join(self.Path, f), 'r')
                    if (self.time_start is None) or (self.time_end is None) or (target_name is None):
                        for l in file:
                            if l.startswith('#waituntil 1,') and self.time_start is None:
                                line_start = l
                                self.time_start = line_start[14:].replace('\n', '')
                                if len(self.time_start) > 7:
                                    self.time_start = Time(self.time_start.replace('/', '-'))
                                else:
                                    self.time_start = Time(Time((Time(self.start_date) + 1).iso,
                                                                out_subfmt='date').value + ' ' + self.time_start)
                            if l.startswith('#quitat'):
                                line_end = l
                                self.time_end = line_end[7:].replace('\n', '')
                                if len(self.time_end) > 7:
                                    self.time_end = self.time_end.replace('/', '-')
                                else:
                                    self.time_end = Time(Time((Time(self.start_date) + 1).iso,
                                                              out_subfmt='date').value + self.time_end)
                            if l.startswith('; Ch'):
                                target_name = l[2:].replace('\n', '')

                    file = open(os.path.join(self.Path, f), 'r')
                    for line in file:
                        if line == ';\n':
                            pass
                        elif line.startswith('; Ch'):
                            target_name = line[2:].replace('\n', '')
                        elif line.startswith('#filter'):
                            filt = line[8:].replace('\n', '')
                            filt_accepted = ['I+z', 'z\'', 'i\'', 'r\'', 'i', 'r', 'z']
                            if filt in filt_accepted:
                                print('INFO: OK, filter chosen for ' + target_name + ' is in the list')
                            else:
                                raise ValueError('ERROR: The filter chosen for target ' + target_name +
                                                 ' is NOT in the filters list (list is [I+z,z\',i\',r\'])')

                        elif line.startswith('#interval'):
                            texp = line[9:].replace('\n', '')
                            if int(texp) < 10:
                                raise ValueError('ERROR: The exposure time for target ' + target_name + ' is < 10s')
                            else:
                                print('INFO: OK, exposure time chosen for ' + target_name + ' is >10s')

                        elif line.startswith(target_name):
                            coords_str = line[(len(target_name) + 1):].replace('\n', '').replace('\t', ' ')
                            coords = SkyCoord(coords_str, unit=(u.hourangle, u.deg))

                            if coords.dec.deg > 80:
                                print(Fore.YELLOW + 'WARNING: ' + Fore.BLACK + 'field ' + target_name +
                                      '\'s declination is above 80°, might have tracking issues')
                            time_range = [Time(self.time_start), Time(self.time_end)]
                            target = FixedTarget(coord=SkyCoord(ra=coords.ra.deg * u.degree,
                                                                dec=coords.dec.deg * u.degree), name=target_name)
                            constraint_elevation = [AltitudeConstraint(min=23 * u.deg),
                                                    AtNightConstraint.twilight_nautical()]  #
                            constraint_moon = [MoonSeparationConstraint(min=20 * u.deg),
                                               AtNightConstraint.twilight_nautical()]
                            observable_elevation = is_always_observable(constraint_elevation, self.observatory, target,
                                                                        time_range=time_range)
                            observable_moon = is_observable(constraint_moon, self.observatory, target,
                                                            time_range=time_range)

                            if observable_elevation:
                                print(Fore.GREEN + 'INFO: ' + Fore.BLACK + 'OK, field ' + target_name
                                      + ' respects the elevation constraint')
                            if not observable_elevation:
                                raise ValueError('ERROR: field ' + target_name
                                                 + ' does NOT respect the constraint of elevation (<23°)')
                            if observable_moon:
                                print(Fore.GREEN + 'INFO: ' + Fore.BLACK + 'OK, field ' + target_name
                                      + ' respects the moon constraint')
                            if not observable_moon:
                                print(Fore.YELLOW + 'WARNING: ' + Fore.BLACK + 'field ' + target_name
                                      + ' does NOT respect the moon separartion angle (>20°)')
                            if abs(coords.dec.deg) > 80:
                                print(Fore.YELLOW + 'WARNING: ' + Fore.BLACK + 'field ' + target_name
                                      + ' is very close to polar (>80) quality will be worst than usual')

                            if self.time_end < self.time_start:
                                raise ValueError(Fore.YELLOW + 'WARNING: ' + Fore.BLACK + 'Start time of field '
                                                 + target_name + ' is > to end time')
                            elif self.time_start < twilight_evening:
                                print(Fore.YELLOW + 'WARNING: ' + Fore.BLACK + 'Start time of field '
                                      + target_name + ' is < to nautical evening twilight !')
                            elif self.time_end > twilight_morning:
                                print(Fore.YELLOW + 'WARNING: ' + Fore.BLACK + 'End time of field '
                                      + target_name + ' is > to nautical morning twilight !')
                            elif (Time(self.time_end).jd - Time(self.time_start).jd) * 24 * 60 < 15:
                                raise ValueError(
                                    'ERROR: You can NOT schedule field ' + target_name + ' for less than 15 min')
                            else:
                                print(
                                    Fore.GREEN + 'INFO: ' + Fore.BLACK + 'Ok, field ' + target_name + ' is scheduled for more than 15 min')
                            if self.check_distance_speculoos_targets(coords.ra, coords.dec, target_name):
                                check_ok = True

        if check_ok:
            print(Fore.GREEN + 'INFO: ' + Fore.BLACK + 'Check completed, plans are OK')
        else:
            print(Fore.RED + 'ERROR: ' + Fore.BLACK + 'Problem in the plans')
        return check_ok

    def etc_andor(self, Jmag, SpT, Filter):
        """ Return the optimized exposure time for the target

        Parameters
        ----------
        Jmag : float
            magnitude in J
        SpT : str
            spectral type of the target
        Filter : str
            filter used

        Returns
        -------
        texp  : float
            exposure time

        """

        moon_phase = round(moon_illumination(Time(self.start_date)), 2)
        a = ETC.etc(mag_val=Jmag, mag_band='J', spt=SpT, \
                    filt=Filter, airmass=1.1, moonphase=moon_phase, irtf=0.8, \
                    num_tel=1, seeing=0.95, gain=1.1)
        texp = a.exp_time_calculator(ADUpeak=30000)
        return texp

    def check_night_blocks(self):
        """ Check if plans meet constraints

        Returns
        -------
        info message
            return message to inform if the plan are ok or not

        """
        check_ok = False
        df_night_block = read_night_block(telescope=self.telescope, day=self.start_date)
        for i in range(len(df_night_block)):
            target_name = df_night_block['target'][i]
            self.time_start = df_night_block['start time (UTC)'][i]
            self.time_end = df_night_block['end time (UTC)'][i]
            conf = ast.literal_eval(df_night_block['configuration'][0])

            # Check filter is OK
            filt = conf['filt']
            filt_accepted = ['I+z', 'z\'', 'i\'', 'r\'', 'g\'', 'i', 'r', 'z', 'g\'', 'zYJ']
            if filt in filt_accepted:
                print(Fore.GREEN + 'INFO: ' + Fore.BLACK + 'OK, filter chosen for ' + target_name + ' is in the list')
            else:
                raise ValueError(Fore.RED + 'ERROR: ' + Fore.BLACK + 'The filter chosen for target ' + target_name +
                                 ' is NOT in the filters list (list is [I+z,z\',i\',r\'])')

            # Check texp is OK
            texp = conf['texp']
            if int(texp) < 10:
                if self.telescope == "Callisto":
                    if int(texp) < 6:
                        raise ValueError(
                            Fore.RED + 'ERROR: ' + Fore.BLACK + 'The exposure time for target ' + target_name + ' is < 10s')
                else:
                    raise ValueError(
                            Fore.RED + 'ERROR: ' + Fore.BLACK + 'The exposure time for target ' + target_name + ' is < 10s')
            else:
                print(Fore.GREEN + 'INFO: ' + Fore.BLACK + 'OK, exposure time chosen for ' + target_name + ' is >10s')

            # Check elevation and moon constraints
            if (df_night_block['dec (d)'][i]) < 0 or (df_night_block['dec (m)'][i] < 0):
                coords_str = str(int(df_night_block['ra (h)'][i])) + ' ' \
                             + str(int(df_night_block['ra (m)'][i])) + ' ' + str(df_night_block['ra (s)'][i]) \
                             + ' -' + str(int(abs(df_night_block['dec (d)'][i]))) + ' ' + \
                             str(abs(int(df_night_block['dec (m)'][i]))) + ' ' + str(abs(df_night_block['dec (s)'][i]))
            else:
                coords_str = str(int(df_night_block['ra (h)'][i])) + ' ' + str(int(df_night_block['ra (m)'][i])) + ' ' \
                             + str(df_night_block['ra (s)'][i]) + '  +' \
                             + str(int(abs(df_night_block['dec (d)'][i]))) + ' ' \
                             + str(abs(int(df_night_block['dec (m)'][i]))) + ' ' \
                             + str(abs(df_night_block['dec (s)'][i]))
            coords = SkyCoord(coords_str, unit=(u.hourangle, u.deg))
            if coords.dec.deg < -80:
                print(Fore.YELLOW + 'WARNING: ' + Fore.BLACK + target_name +
                      '\'s declination is above 80°, might have tracking issues')
            time_range = [Time(self.time_start), Time(self.time_end)]
            target = FixedTarget(coord=SkyCoord(ra=coords.ra.deg * u.degree,
                                                dec=coords.dec.deg * u.degree), name=target_name)
            constraint_elevation = [AltitudeConstraint(min=23 * u.deg)]  #
            constraint_moon = [MoonSeparationConstraint(min=20 * u.deg)]
            try:
                observable_elevation = is_always_observable(constraint_elevation, self.observatory, target,
                                                            time_range=time_range)
            except ValueError:
                raise ValueError(Fore.RED + 'ERROR: ' + Fore.BLACK
                                 + ' Please make sure the start/end time are consistent with the date indicated.')
            observable_moon = is_observable(constraint_moon, self.observatory, target,
                                            time_range=time_range)
            if observable_elevation:
                print(Fore.GREEN + 'INFO: ' + Fore.BLACK + 'OK, field ' + target_name
                      + ' respects the elevation constraint')
            if not observable_elevation:
                raise ValueError(Fore.RED + 'ERROR: ' + Fore.BLACK + 'field ' + target_name
                                 + ' does NOT respect the constraint of elevation (<23°)')
            if observable_moon:
                print(Fore.GREEN + 'INFO: ' + Fore.BLACK + 'OK, field ' + target_name
                      + ' respects the moon constraint')
            if not observable_moon:
                print(Fore.YELLOW + 'WARNING: ' + Fore.BLACK + 'field ' + target_name
                      + ' does NOT respect the moon separartion angle (>20°)')
            if abs(coords.dec.deg) > 80:
                print(Fore.YELLOW + 'WARNING: ' + Fore.BLACK + 'field ' + target_name
                      + ' is very close to polar (>80) quality will be worst than usual')

            # Check duration of observations
            elif (Time(self.time_end).jd - Time(self.time_start).jd) * 24 * 60 < 15:
                raise ValueError(Fore.RED + 'ERROR: ' + Fore.BLACK + 'You can NOT schedule field '
                                 + target_name + ' for less than 15 min')
            else:
                print(Fore.GREEN + 'INFO: ' + Fore.BLACK + 'Ok, field '
                      + target_name + ' is scheduled for more than 15 min')

            # Check distance to SPECULOOS targets
            if self.check_distance_speculoos_targets(coords_str, target_name):
                check_ok = True
            if check_ok:
                print(Fore.GREEN + 'INFO: ' + Fore.BLACK + 'Check completed, for ' + target_name +
                      ', you can send the night_blocks to educrot@uliege.be or to '
                      'GXG831@student.bham.ac.uk. ')
            else:
                print(Fore.RED + 'ERROR: ' + Fore.BLACK + 'Problem in the plans')

        return check_ok

    def check_distance_speculoos_targets(self, coords_str, target_name):
        """ check if target is not in SPECULOOS target list

        Parameters
        ----------
        ra : float
            right ascension (degrees)
        dec : float
            declinaison (degrees)
        target_name : str
            name of the target

        Returns
        -------
        info message
            state whether there is a SPECULOOS target in the field or not

        """
        check_ok = False
        catalog_data = Catalogs.query_object(coords_str, radius=6 * np.sqrt(2) * u.arcminute, catalog="Gaia")
        df = pd.read_csv(path_spock_chilean + '/speculoos_target_list_chilean_nights.txt', delimiter=' ')
        #idx_speculoos_found = [np.where((catalog_data['designation'] == 'Gaia DR2 '
        #                                 + str(gaia_id)))[0] for gaia_id in df['Gaia_ID']]
        idx_speculoos_found = [np.any(catalog_data['designation'] == 'Gaia DR2 ' + str(gaia_id))
                                for gaia_id in df['Gaia_ID']]
        if np.any(idx_speculoos_found):
            raise ValueError('ERROR: There is a SPECULOOS target in this field, please change your coordinates')
        else:
            print(Fore.GREEN + 'INFO: ' + Fore.BLACK + 'OK, field ' + target_name
                  + ' does not contain a SPECULOOS target')
            check_ok = True
        return check_ok


def save_night_blocks(target_chilean, date, telescope):
    durations = []
    configurations = []
    ra1s = []
    ra2s = []
    ra3s = []
    dec1s = []
    dec2s = []
    dec3s = []

    for i in range(len(target_chilean)):
        durations.append((Time(target_chilean['End'][i]).jd - Time(target_chilean['Start'][i]).jd) * 24 * 60)
        configurations.append({"filt": target_chilean['Filter'][i], "texp": target_chilean['texp'][i]})

        coords = SkyCoord(ra=target_chilean['RA'][i] * u.deg, dec=target_chilean['DEC'][i] * u.deg)
        ra1s.append(coords.ra.hms[0])
        ra2s.append(coords.ra.hms[1])
        ra3s.append(coords.ra.hms[2])
        dec1s.append(coords.dec.dms[0])
        dec2s.append(coords.dec.dms[1])
        dec3s.append(coords.dec.dms[2])

    df = pd.DataFrame({"target": target_chilean['Name'], "start time (UTC)": target_chilean['Start'],
                       "end time (UTC)": target_chilean['End'], "duration (minutes)": durations,
                       "ra (h)": ra1s, "ra (m)": ra2s, "ra (s)": ra3s, "dec (d)": dec1s, "dec (m)": dec2s,
                       "dec (s)": dec3s, "configuration": configurations})

    df.to_csv(os.path.join(path_spock_chilean + '/../Archive_night_blocks_chilean/night_blocks_' +
                           telescope + '_' + Time(date, out_subfmt='date').iso
                           + '.txt'), sep=' ', index=None)
    # print(Fore.GREEN + 'INFO: ' + Fore.BLACK +
    #       ' night blocks saved in the folder \"path_spock_chilean/Archive_night_blocks_chilean\"')


def available_dates_telescopes(df):
    available_dates = []
    available_telescopes = []
    for i in range(len(df)):
        if np.any(df.values[i] == 1):
            available_dates.append(df.values[i][0].strftime('%Y-%m-%d'))
            if df.values[i][1] == 1:
                telescope = 'Io'
                available_telescopes.append(telescope)
            if df.values[i][2] == 1:
                telescope = 'Europa'
                available_telescopes.append(telescope)
            if df.values[i][3] == 1:
                telescope = 'Ganymede'
                available_telescopes.append(telescope)
            if df.values[i][4] == 1:
                telescope = 'Callisto'
                available_telescopes.append(telescope)

    return available_dates, available_telescopes


def read_night_block(telescope, day):
    """

    Parameters
    ----------
    telescope: name telescope
    day: date

    Returns
    -------

    """

    day_fmt = Time(day, scale='utc', out_subfmt='date').tt.datetime.strftime("%Y-%m-%d")
    path_local = path_spock_chilean + '/../Archive_night_blocks_chilean/' + 'night_blocks_' + telescope + '_' + day_fmt + '.txt'

    if os.path.exists(path_local):
        scheduler_table = Table.read(path_local, format='ascii')
    else:
        print(Fore.red + 'ERROR: ' + Fore.black + 'No night block for this date and/or telescope.')

    return scheduler_table
