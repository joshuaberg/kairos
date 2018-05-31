from flask import Flask , render_template, request, redirect
import json
import requests
import math
import datetime

app = Flask(__name__)

@app.route('/')
def main():
    try:
        timeToWork = getTimetoWork()
        #print(timeToWork)
    except Exception:
        timeToWork = "NaN"
        #print("Nope")
    next3Trains = getNext3Trains()
    schedule_1 = selectScheduleTime(next3Trains,0)
    schedule_2 = selectScheduleTime(next3Trains,1)
    schedule_3 = selectScheduleTime(next3Trains,2)
    #print(schedule_1)
    #print(schedule_2)
    #print(schedule_3)

    return render_template('home.html',timeToWork = timeToWork, schedule_1 = schedule_1, schedule_2 = schedule_2 ,schedule_3 = schedule_3)


@app.route('/data', methods = ['POST'])
def data():
    global api_key
    global origin
    global destination

    api_key = request.form['api_key']
    origin = request.form['origin']
    destination = request.form['destination']

    return redirect('/')

@app.route('/setup')
def setup():
    return render_template('setup.html')


def getTimetoWork():

    # Google Distance Matrix base URL to which all other parameters are attached
    base_url = 'https://maps.googleapis.com/maps/api/distancematrix/json?'

    # Google Distance Matrix domain-specific terms: origins and destinations
    #origin = ['126 New Bern St, Charlotte, NC 28203']
    #destination = ['8900 Northpointe Executive Park Dr, Huntersville, NC 28078']

    # Prepare the request details
    payload = {
        'origins' : origin,
        'destinations' : destination,
	    'mode' : 'driving',
        'departure_time' : 'now',
        'traffic_model' : 'best_guess',
	    'key' : api_key
        }
    # Build the URL and query the web page
    req = requests.get(base_url, params = payload)
    parsed_json = req.json()
    duration_traffic_sec = (parsed_json['rows'][0]['elements'][0]['duration_in_traffic']['value'])
    duration_traffic_minutes = int(math.ceil(duration_traffic_sec/60))
    formatted_duration = "{} min".format(duration_traffic_minutes)
    return(formatted_duration)

def getNext3Trains():
    #get current time in minutes + current day of the week
    now = datetime.datetime.now()
    h = now.hour
    m = now.minute
    time_min = (h*60) + m
    day = datetime.date.today().weekday()  # 0 is monday   6 is sunday


    #get full train schedule
    req = requests.get('https://raw.githubusercontent.com/brandonfancher/charlotte-lightrail/master/src/helpers/schedules.json')
    parsed_json = req.json()

    # get the current weekday's full schedule
    if day == 5:
        full_schedule = parsed_json['outboundSaturday']['station-19']
    elif day == 6:
        full_schedule = parsed_json['outboundSunday']['station-19']
    else:
        full_schedule = parsed_json['outboundWeekday']['station-19']


    #go through schedule and get next 3 trains
    next3Trains = []
    k = 0
    for arrival in full_schedule:
        #check if thutese value is an actual number, convert it to # if so
        if arrival != 'no stop':
            sch_min = (int(arrival[:2])*60) + int(arrival[-2:]) #converts arival time to min
            #check if ntime is larger then the current time, if so get difference in times
            if sch_min > time_min:
                time_until_train = sch_min - time_min
                #build an array next three values
                if time_until_train > 60:
                    hr = math.floor(time_until_train/60)
                    min = time_until_train - (hr * 60)
                    next3Trains.append("{} hr {} min".format(hr,min))
                else:
                    next3Trains.append("{} min".format(time_until_train))

                k = k + 1
                if k == 3:
                    break
    print(next3Trains)
    return(next3Trains)

def selectScheduleTime(array,num):
    try:
        return(array[num])
    except:
        return('none')

app.run(debug=True)
