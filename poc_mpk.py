"""
Finding departures from choosen bus/tram stop in Wroclaw,
using Wrloclaw open data (txt files)
source data imported from: https://www.wroclaw.pl/open-data/dataset/rozkladjazdytransportupublicznegoplik_data/resource/62b3f371-2375-4979-874c-05c6bbb9b09e
source data documentation: https://developers.google.com/transit/gtfs/reference
Legend:
    pts: public transport system
"""
import time

#initial configuration. 
# Path of data files and how many minuites in futer to search departures for
fpath = 'C:/projects/python/poc_mpk/files/'
search_min = 20
#search timeframe (min = current, max = current + serach_min(minutes) )
cur_time = time.time()
time1 = time.strftime("%H:%M:%S", time.localtime(cur_time))
time2 = time.strftime("%H:%M:%S", time.localtime(cur_time + (search_min * 60)))

def tt_day():
    """Determining service_id of weekday timetables variant.
    Args:
        weekday: user input (name of serched stop)
        calendar_file: read file with timetable variant data
        service_id: service_id of valid (in particular weekday) timetable variant
        tt_line: lane of data in file
        tt_parts: split data records in line (comma delimited)
        is_current: flag of record in column related to weekday
    End result:
        service_id
    """
    weekday = int(time.strftime("%w", time.localtime(cur_time)))
    if weekday == 0: weekday = 7 #change from  [0(Sunday),6] to  [1(Monday),6]
    calendar_file = open(fpath + "calendar.txt", encoding='utf-8-sig')
    service_id = ''
    for tt_variant in calendar_file:
        tt_line = tt_variant.strip()
        tt_parts = tt_line.split(',')
        is_current = tt_parts[weekday]
        if is_current == '1':
            service_id = tt_parts[0]
            break
    return service_id


def input_data():
    """Prompting for stop name and checking min characters lenght (3).
    Args:
        stop_input: user input (name of serched stop)
        too_little: in case of insufficient lenght of input - ask for repeating input
    End result:
        calling function stop_list with arg: stop_input
    """
    stop_input = input("\nPodaj nazwę przystanku (minimum 3 początkowe znaki): ")
    if len(stop_input) < 3:
            too_little = input("Z mało znaków. Chcesz wpisać jeszcze raz (T/N)? ")
            if too_little.upper() == 'T':
                input_data()
            else:
                quit()
    stop_list(stop_input)


def stop_list(stop_search):
    """Searching for stop with name beggining from input string.
        In case of more than one stop found, asking for picking the right one
        In case of no stops found, option of starting over (back to inpyt) or quiting
    Args:
        stop_search: string used for searching stop
        stop_inp_len: lenght of stop input
        stops found: list of lists - stops with attributes
        stops_distinct: temporary list to verify if stop hasn't been foud in earlier rows of file
        file_stops: reading file
        stopd_line: extract line of texct file
        stopd_parts: splitting csv file (comma separated data records)
        stopd_name: name of stop from data field, double quotes removed
        stops_no: number of distinct stops found
        txt: text to be constructed if no stops have been found
        to_start: Prompting for decision (start over or quit) if no stops have been found
        stop_idint: if stops_no > 1, prompting to choose right one (endter number of stop within generated list)
        stop_id = id of found stop
        stop_code = pts' stop code
        stop_info = temporary list containing stop id, code and name
    End result:
        calling function stop_times with arg: list of lists with stops found
    """
    x = 0
    y = 0
    stop_inp_len = len(stop_search)
    stops_found = []
    stops_distinct = []
    file_stops = open(fpath + "stops.txt", encoding='utf-8-sig')
    for stopd in file_stops:
        stopd_line = stopd.strip()
        stopd_parts = stopd_line.split(',')
        stopd_name = stopd_parts[2].replace('"','')
        if (stopd_name[:stop_inp_len]).lower() == stop_search.lower() and \
            stopd_name not in stops_distinct: stops_distinct.append(stopd_name)
        stops_no = len(stops_distinct)
    if stops_no == 0:
        txt = "Nie znaleziono przystanku o nazwie zaczynającej się na:" + stop_search + ". Czy chcesz kontynuować?(T/N) "
        to_start = input(txt)
        if to_start.upper() == 'T':
            input_data()
        else:
            quit()
    elif stops_no == 1:
        print(f"Znaleziono jedną nazwę przystanku zaczynającą się od {stop_search}: {stops_distinct[0]}")
        stop_search = stops_distinct[0]
    else:
        print("Jest kilka przystanków o podobnych nazwach:")
        i = 0
        for s in stops_distinct:
            i += 1
            print(f"    {i}: {stops_distinct[i-1]}")
        stop_idint = input("Wpisz numer (liczbę) właściwego przystanku: ")
        while stop_idint.isdigit() != True or int(stop_idint) not in range(1, i+1):
            print(f'Wprowadzone "{stop_idint}" nie jest numerem albo jest poza zakresem. Wpisz liczbę w zakresie od 1 do {i}')
            stop_idint = input("Wpisz numer (liczbę) właściwego przystanku: ")
        stop_search = stops_distinct[int(stop_idint)-1]
        print("wpisane", stop_idint, ":", stop_search)
    file_stops = open(fpath + "stops.txt", encoding='utf-8-sig')
    for stop in file_stops:
        stop_line = stop.strip()
        stop_parts = stop_line.split(',')
        stop_name = stop_parts[2].replace('"','')
        x += 1
        if stop_name.lower() == stop_search.lower():
            y += 1
            stop_id = stop_parts[0]
            stop_code = stop_parts[1]
            stop_info = [stop_id, stop_code, stop_name]
            if stops_found is None:
                stops_found = stop_info
            else:
                stops_found.append(stop_info)
    
    #print("Found", len(stops_found), "stops:\n", stops_found, "\n", ("-"*64))
    stop_times(stops_found)

def stop_times(stops_found):
    """Enriching and enlarging stops list (of lists) with departure times info.
        Looping through stop_times csv file and finiding departure times connected with found stops
        For time found - getting bus/tram line data from trips file (calling trips function) 
    Args:
        stops_id: temporary list of stops' ids found
        stops_no: number of stops found
        id: stop's id to be added to stops_id list
        sl_file: open csv file with times
        stopd_list: new list of list with enriched data
        stopt_line = read line of sl_file
        stopt_parts = split records in line (comma delimited)
        stopt_time = departure time
        stopt_stopid = stop id from times file's data row
        
        stops_ix = index of stop in stops_id list
        stop_code = pts' stop code
        stop_name = name of stop
        stopt_tripid = id of trop (to be searched in trips file)
        stopt_time = departure time
        trps = trips(stopt_tripid)
        trps_line = pts' line retrieved from trips file
        trps_dir = pts line's direction name retrieved from trips file   
        trps_valid: is timetable valid today (day of week comparison) True/False     
    End result:
        calling function timetables with arg: stopd_list (list of list containing stops, times and lines data)
    """
    x = 0
    y = 0
    stops_id = []
    stops_no = len(stops_found)
    for i in range (0, stops_no):
        id = stops_found[i][0]
        stops_id.append(id)
    sl_file = open(fpath + "stop_times.txt", encoding='utf-8-sig')
    stopt_list = []
    service_id = tt_day()
    for stop_time in sl_file:
        stopt_line = stop_time.strip()
        stopt_parts = stopt_line.split(',')
        stopt_time = stopt_parts[2]
        stopt_stopid = stopt_parts[3]
        # check if time fullfils criteria (stop_id and timeframe)
        if stopt_stopid in stops_id and stopt_time > time1 and stopt_time <= time2 and stopt_time < '24':
            stops_ix = stops_id.index(stopt_stopid)
            stop_code = stops_found[stops_ix][1]
            stop_name = stops_found[stops_ix][2]
            stopt_tripid = stopt_parts[0]
            stopt_time = stopt_parts[2]
            trps = trips(stopt_tripid, service_id)
            trps_line = trps[0]
            trps_dir = trps[1]
            trps_valid = trps[2]
            stopt_list.append([stop_code, stop_name, stopt_time, stopt_tripid, trps_line, trps_dir, trps_valid])
            x += 1
        y += 1
    #print(x)
    timetable(stopt_list)


def trips(trip_id, service_id):
    """retrieving pts line symbol, direction and timetable validity for given day of week 
    Args:
        t_file: open file with trip data
        t_line: data row
        t_parts: data records in row (comma delimited)
        city_line: line symbol
        where_to: direction
        valid: is this trip valid today (day of week)     
    End result:
        returning city_line, where_to and valid
    """
    t_file = open(fpath + "trips.txt", encoding='utf-8-sig')
    x = 0
    t_list = []
    for trip in t_file:
        t_line = trip.strip()
        t_parts = t_line.split(',')
        if t_parts[2] == trip_id:
            city_line = t_parts[0]
            where_to = t_parts[3].replace('"','')
            if service_id == t_parts[1]:
                valid = True
            else:
                valid = False
            break
    return city_line, where_to, valid


def sort_times(x):
    #used to generate sorted timetable (1st level of sorting)
    return x[2]


def sort_stops(x):
    #used to generate sorted timetable (23nd = final level of sorting)
    return x[0]


def timetable(stopt_list):
    """Printing timetable
    """    
    #print("executing function timetable ...")
    stopt_list.sort(key=sort_times)
    stopt_list.sort(key=sort_stops)
    #print(stopt_list)
    print("\n\n>>>>> Odjazdy w ciągu najbliższych", search_min, "minut <<<<<")
    x = 0
    for item in stopt_list:
        if x == 0 or stopt_list[x][0] != stopt_list[x-1][0]:
            print(f"Przystanek: {stopt_list[x][1]} (kod {stopt_list[x][0]})")
        if (x == 0 or \
                    (stopt_list[x][2] + stopt_list[x][4] + stopt_list[x][5]) \
                        != (stopt_list[x-1][2] + stopt_list[x-1][4] + stopt_list[x-1][5])) \
                and stopt_list[x][6] == True:
            hour = stopt_list[x][2]
            hour = hour[:5]
            print(f"   {hour}, linia {stopt_list[x][4]}, kierunek {stopt_list[x][5]}")
        x += 1


input_data()
