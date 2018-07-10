from flask import Flask , render_template, request, redirect
import json
import requests
import math
import datetime

app = Flask(__name__)

global api_key
global origin
global destination
global weather_api_key
global configCheck
configCheck = 0

@app.route('/')
def main():
    global configCheck
    #check for config file the first time program is run
    #if setup page is used, the config variable will be overwritten
    if configCheck == 0:
        try:
            checkConfig()
        except Exception:
            print('config file not found')
        configCheck = 1

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

    try:
        weather_data = getWeather()
    except Exception:
        weather_data = ['NaN','NaN','NaN','NaN']

    icon = weather_data[0]
    description= weather_data[1]
    temp_min = weather_data[2]
    temp_max = weather_data[3]
    #print(description)

    return render_template('home.html',timeToWork = timeToWork, schedule_1 = schedule_1, schedule_2 = schedule_2 ,schedule_3 = schedule_3, icon = icon, description=description, temp_min = temp_min, temp_max = temp_max)



@app.route('/data', methods = ['POST'])
def data():
    global api_key
    global origin
    global destination
    global weather_api_key

    api_key = request.form['api_key']
    origin = request.form['origin']
    destination = request.form['destination']
    weather_api_key = request.form['weather_api_key']

    return redirect('/')

@app.route('/setup')
def setup():
    return render_template('setup.html')


def getTimetoWork():

    # Google Distance Matrix base URL to which all other parameters are attached
    base_url = 'https://maps.googleapis.com/maps/api/distancematrix/json?'

    #Note: origin, destination and api key recieved from the setup page and given as a global variable

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

def getWeather():
    #req = requests.get('http://api.openweathermap.org/data/2.5/weather?q=Charlotte&APPID=229dd301e4f45f8d0d96eb28c6592c7e')



    base_url = 'http://api.openweathermap.org/data/2.5/weather?'


    payload = {
        'q' : 'Charlotte',
        'APPID': weather_api_key,
        }
    req = requests.get(base_url, params = payload)

    parsed_json = req.json()
    icon_id = parsed_json['weather'][0]['id']
    weather_description = parsed_json['weather'][0]['description']
    temp_min = math.floor(((parsed_json['main']['temp_min'])*(9/5)) - 459.67)
    temp_max = math.floor(((parsed_json['main']['temp_max'])*(9/5)) - 459.67)
    print(weather_description)

    with open('weather.json') as f:
        parsed_json = json.load(f)

    icon_name = parsed_json[str(icon_id)]["icon"]

    weather_data = [icon_name, weather_description, temp_min, temp_max]
    return(weather_data)

def checkConfig():
    global api_key
    global origin
    global destination
    global weather_api_key

    with open('config.json') as f:
        parsed_json = json.load(f)

    api_key = parsed_json['config']['google_api']
    weather_api_key = parsed_json['config']['weather_api']
    origin = parsed_json['config']['origin']
    destination = parsed_json['config']['destination']


app.run(debug=True)
