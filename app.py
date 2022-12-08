from flask import Flask, jsonify, render_template, request
from joblib import load
from group_estimator import GroupbyEstimator, ColumnSelector, hgbc_factory
import pandas as pd
import numpy as np
import json
import requests
import os
from datetime import datetime

airlines = ['AA', 'DL', 'UA', 'WN', 'AS', 'B6', 'NK', 'F9', 'G4', 'HA']
with open("new_model.joblib","r") as f:
    model = load(f)

def make_api_call(formstring):
    formdata = json.loads(formstring)
    appid = os.getenv('CIRIUM_APPID')
    appkey = os.getenv('CIRIUM_APPKEY')
    carrier = formdata['airline']
    flight_number = formdata['flight_number']
    orig = formdata['departing_airport']
    dest = formdata['arriving_airport']
    flight_date = formdata['arrival_date']
    flight_dt = datetime.strptime(flight_date, '%m/%d/%Y, %H:%M %p')
    year = flight_dt.year
    month = flight_dt.month
    day = flight_dt.day

    url = f'https://api.flightstats.com/flex/schedules/rest/v1/json/from/{orig}/to/{dest}/arriving/{year}/{month}/{day}?appId={appid}&appKey={appkey}'
    s = requests.Session()
    return(s.get(url))
    
def parse_response(text):
    fl_list = json.loads(text)
    dep_airport, arr_airport = [fl_list['appendix']['airports'][i] for i in [0,1]]
    tzdelta = int(arr_airport['utcOffsetHours']) - int(dep_airport['utcOffsetHours'])
    astring, dstring = [f"{d['city']}, {d['stateCode']} ({d['iata']})" for d in [arr_airport, dep_airport]]
    aldict = {d['iata']:d['name'] for d in fl_list['appendix']['airlines']}
    df = pd.DataFrame(fl_list['scheduledFlights'])
    
    cutdf = df[df['carrierFsCode'].isin(airlines)].copy()
    cutdf.rename(columns={'arrivalAirportFsCode':'dest'},inplace=True)
    cutdf['deptime'] = pd.to_datetime(cutdf['departureTime'],format='%Y-%m-%dT%H:%M')
    cutdf['arrtime'] = pd.to_datetime(cutdf['arrivalTime'],format='%Y-%m-%dT%H:%M')
    cutdf['flighttime'] = (cutdf['arrtime'] - cutdf['deptime'])/np.timedelta64(1,'m') - 60*tzdelta
    cutdf["dayofweek"] = cutdf["arrtime"].dt.weekday
    cutdf["weekofyear"] = cutdf["arrtime"].dt.isocalendar().week
    cutdf["hour"] = cutdf['arrtime'].dt.hour.astype(int)

    cutdf['ddate'] = cutdf['deptime'].dt.strftime('%m/%d/%Y')
    cutdf['dtime'] = cutdf['deptime'].dt.strftime('%H:%M')
    cutdf['adate'] = cutdf['arrtime'].dt.strftime('%m/%d/%Y')
    cutdf['atime'] = cutdf['arrtime'].dt.strftime('%H:%M')
    cutdf['astring'] = astring
    cutdf['dstring'] = dstring
    cutdf['alname'] = cutdf['carrierFsCode'].map(aldict)

    return cutdf.copy()
 
app = Flask(__name__)

@app.route('/')
def index():
    with open("ap_select.json","r") as infile:
        option_list = json.load(infile)    
    return render_template('index.html',option_list=option_list, table=False)

    
@app.route('/predict',methods=['GET'])
def get_prediction():
    model = load('new_model.joblib')

    args = request.args
    # resp = make_api_call(json.dumps(args))
    # response_df = parse_response(resp.text)
    f = open('./cirium-schedule.json')
    text = f.read()
    response_df = parse_response(text)
    response_df.reset_index(inplace=True)
    response_df['probs'] = model.predict_proba(response_df)[:,-1]*100

    selected_airline = args['airline']
    selected_flight_num = args['flight_number']
    flight_search = (response_df['carrierFsCode'] == selected_airline) & (response_df['flightNumber'] == selected_flight_num)
    found_flight = json.loads(response_df[flight_search].to_json(orient='records'))
    output_list = json.loads(response_df[~flight_search].sort_values('deptime').to_json(orient='records'))
    
    with open("ap_select.json","r") as infile:
        option_list = json.load(infile)    

    return render_template('index.html',
            option_list=option_list, 
            table=True,
            found_flight=found_flight,
            output_list=output_list)
     
if __name__ == '__main__':
    app.run(debug=True)
