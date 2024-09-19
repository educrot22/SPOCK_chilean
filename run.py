import pandas as pd
from SPOCK_chilean.make_night_plans import chilean_time
import SPOCK_chilean.ETC as ETC

# set in advance with the planning with SSO team
telescope = 'Callisto'

date = '2022-03-08 15:00:00'  # start of night date
chilean_nb_target = 4  # number of target to observe this night
counts = 5000  # counts of images per targets (no limit = 5000)
chilean_plans = chilean_time(date, telescope)

df = pd.read_csv('SPIRIT_target_tests.csv')


target_chilean = pd.DataFrame({'Date': date, 'Telescope': df['Telescope'][0], 'Name': df['Name'][0],
                        'Start': df['Start'][0],
                        'End': df['End'][0],
                        'RA':  df['RA'][0],
                        'DEC': df['DEC'][0],
                        'Filter': 'z',
                        'texp': 10,
                        'Counts': counts, '#target': 1, 'Gaia_ID': 'gaia_id', 'Jmag': 19, 'SpT': 'M8'},
                              index=[0])


for i in range(1,2):
    if chilean_nb_target > 1:
        other_target = {'Date': date, 'Telescope': df['Telescope'][i], 'Name': df['Name'][i],
                        'Start': df['Start'][i],
                        'End': df['End'][i],
                        'RA':  df['RA'][i],
                        'DEC': df['DEC'][i],
                        'Filter': 'z',
                        'texp': 10,
                        'Counts': counts, '#target': 1, 'Gaia_ID': 'gaia_id', 'Jmag': 19, 'SpT': 'M8'}
        target_chilean = pd.concat([target_chilean,pd.DataFrame(other_target,index=[0])], ignore_index=True)

# for i in range(-1, -2):
#     if chilean_nb_target > 1:
#         other_target = {'Date': date, 'Telescope': df['Telescope'][i], 'Name': df['Name'][i],
#                         'Start': df['Start'][i],
#                         'End': df['End'][i],
#                         'RA':  df['RA'][i],
#                         'DEC': df['DEC'][i],
#                         'Filter': 'zYJ',
#                         'Counts': counts, '#target': 1, 'Gaia_ID': 'gaia_id', 'Jmag': 19, 'SpT': 'M8'}
#         target_chilean = target_chilean.append(other_target, ignore_index=True, sort=False)

chilean_plans.make_night_block(target_chilean)

chilean_plans.check_night_blocks()

print()







# OTHER EXAMPLES


# # set in advance with the planning of the chilean nights
# telescope = 'Ganymede'

# date = '2020-05-26'
# chilean_nb_target = 1
# counts = 5000
# chilean_plans = chilean_time('2020-05-26')


# target_chilean = pd.DataFrame({'Date': date, 'Telescope': telescope, 'Name': 'Ch_1',
#                                'Start': '2020-05-27 00:30:00.000', 'End': '2020-05-27 03:00:00.000',
#                                'RA': 181.8609974 , \
#                                'DEC': -52.7885865, 'Filter': 'I+z',
#                                'texp': 20, \
#                                'Counts': counts, '#target': 1,'Gaia_ID':'gaia_id','Jmag':11.8,'SpT':'M4'},
#                               index=[0])

# if chilean_nb_target > 1:
#     other_target = {'Date': date, 'Telescope': telescope, 'Name': 'Ch_2',
#                                'Start': '2020-01-31 05:30:00.000', 'End': '2020-01-31 06:00:00.000',
#                                'RA': 79.4074682 , \
#                                'DEC': -33.8175201, 'Filter': 'r\'',
#                                'texp': 10, \
#                                'Counts': counts, '#target': 1,'Gaia_ID':'gaia_id'}
#     target_chilean = target_chilean.append(other_target, ignore_index=True, sort=False)

# if chilean_nb_target > 2:
#     other_target = {'Date': date, 'Telescope': telescope, 'Name': 'Ch_2',
#                                'Start': '2020-01-31 05:30:00.000', 'End': '2020-01-31 06:00:00.000',
#                                'RA': 79.4074682 , \
#                                'DEC': -33.8175201, 'Filter': 'r\'',
#                                'texp': 10, \
#                                'Counts': counts, '#target': 1,'Gaia_ID':'gaia_id'}
#     target_chilean = target_chilean.append(other_target, ignore_index=True, sort=False)

# if chilean_nb_target > 3:
#     other_target = {'Date': date, 'Telescope': telescope, 'Name': 'Ch_2',
#                                'Start': '2020-01-31 05:30:00.000', 'End': '2020-01-31 06:00:00.000',
#                                'RA': 79.4074682 , \
#                                'DEC': -33.8175201, 'Filter': 'r\'',
#                                'texp': 10, \
#                                'Counts': counts, '#target': 1,'Gaia_ID':'gaia_id'}
#     target_chilean = target_chilean.append(other_target, ignore_index=True, sort=False)

# if chilean_nb_target > 4:
#     other_target = {'Date': date, 'Telescope': telescope, 'Name': 'Ch_2',
#                                'Start': '2020-01-31 05:30:00.000', 'End': '2020-01-31 06:00:00.000',
#                                'RA': 79.4074682 , \
#                                'DEC': -33.8175201, 'Filter': 'r\'',
#                                'texp': 10, \
#                                'Counts': counts, '#target': 1,'Gaia_ID':'gaia_id'}
#     target_chilean = target_chilean.append(other_target, ignore_index=True, sort=False)

# if chilean_nb_target > 5:
#     other_target = {'Date': date, 'Telescope': telescope, 'Name': 'Ch_2',
#                                'Start': '2020-01-31 05:30:00.000', 'End': '2020-01-31 06:00:00.000',
#                                'RA': 79.4074682 , \
#                                'DEC': -33.8175201, 'Filter': 'r\'',
#                                'texp': 10, \
#                                'Counts': counts, '#target': 1,'Gaia_ID':'gaia_id'}
#     target_chilean = target_chilean.append(other_target, ignore_index=True, sort=False)

# if chilean_nb_target > 6:
#     other_target = {'Date': date, 'Telescope': telescope, 'Name': 'Ch_2',
#                                'Start': '2020-01-31 05:30:00.000', 'End': '2020-01-31 06:00:00.000',
#                                'RA': 79.4074682 , \
#                                'DEC': -33.8175201, 'Filter': 'r\'',
#                                'texp': 10, \
#                                'Counts': counts, '#target': 1,'Gaia_ID':'gaia_id'}
#     target_chilean = target_chilean.append(other_target, ignore_index=True, sort=False)

# if chilean_nb_target > 7:
#     other_target = {'Date': date, 'Telescope': telescope, 'Name': 'Ch_2',
#                                'Start': '2020-01-31 05:30:00.000', 'End': '2020-01-31 06:00:00.000',
#                                'RA': 79.4074682 , \
#                                'DEC': -33.8175201, 'Filter': 'r\'',
#                                'texp': 10, \
#                                'Counts': counts, '#target': 1,'Gaia_ID':'gaia_id'}
#     target_chilean = target_chilean.append(other_target, ignore_index=True, sort=False)

# if chilean_nb_target > 8:
#     other_target = {'Date': date, 'Telescope': telescope, 'Name': 'Ch_2',
#                                'Start': '2020-01-31 05:30:00.000', 'End': '2020-01-31 06:00:00.000',
#                                'RA': 79.4074682 , \
#                                'DEC': -33.8175201, 'Filter': 'r\'',
#                                'texp': 10, \
#                                'Counts': counts, '#target': 1,'Gaia_ID':'gaia_id'}
#     target_chilean = target_chilean.append(other_target, ignore_index=True, sort=False)

# if chilean_nb_target > 9:
#     other_target = {'Date': date, 'Telescope': telescope, 'Name': 'Ch_2',
#                                'Start': '2020-01-31 05:30:00.000', 'End': '2020-01-31 06:00:00.000',
#                                'RA': 79.4074682 , \
#                                'DEC': -33.8175201, 'Filter': 'r\'',
#                                'texp': 10, \
#                                'Counts': counts, '#target': 1,'Gaia_ID':'gaia_id'}
#     target_chilean = target_chilean.append(other_target, ignore_index=True, sort=False)

# chilean_plans.make_plans(target_chilean)
# chilean_plans.check_plans()


# print()

