import appdaemon.plugins.hass.hassapi as hass
import datetime
import pytz
from nordpool import elspot

class PriceFetch(hass.Hass):
    def initialize(self):
        self.run_daily(self.getprices, "13:32:01") #New prices are published to Nordpool around 13:30 EET
        self.run_daily(self.getprices, "01:00:01") #Update tommorrow to today after nordpool changes to next day
        hourly_start=datetime.datetime.today().hour+1
        self.run_hourly(self.updatecurrentprice, datetime.time(hourly_start, 0, 1)) #Update prices every even hour
        prices_spot = elspot.Prices()
        datatoday = prices_spot.hourly(end_date=self.date(),areas=['FI'])
        now = datetime.datetime.now(pytz.utc)
        for rate in datatoday['areas']['FI']['values']:
            if rate['start'] <= now < rate['end']:        
                self.set_state("sensor.spot_cost", state=round(rate['value']/10*1.24+3.9+2.79372,3)) #Added VAT, transfer and electricity tax
                self.set_state("sensor.spot_sell", state=round(rate['value']/10,3)) #Raw price for selling
        datatomorrow = prices_spot.hourly(areas=['FI'])
        priceslist = []
        for i in datatoday['areas']['FI']['values']:
            priceslist.append(round(i['value']/10*1.24+3.9+2.79372,3))
        priceslistsorted=sorted(priceslist)
        self.set_state("sensor.spot_cost_today", state=priceslistsorted)
        priceslisttomorrow=[]
        for i in datatomorrow['areas']['FI']['values']:
            priceslisttomorrow.append(round(i['value']/10*1.24+3.9+2.79372,3))
        priceslisttomorrowsorted=sorted(priceslisttomorrow)
        self.set_state("sensor.spot_cost_future", state=priceslisttomorrowsorted)
            
    def getprices(self,kwargs): # Get daily prices
        prices_spot = elspot.Prices()
        now = datetime.datetime.now(pytz.utc)
        datatoday = prices_spot.hourly(end_date=self.date(),areas=['FI'])
        priceslist = []
        for i in datatoday['areas']['FI']['values']:
            priceslist.append(round(i['value']/10*1.24+3.9+2.79372,3))
        priceslistsorted=sorted(priceslist)
        self.set_state("sensor.spot_cost_today", state=priceslistsorted)
        priceslisttomorrow = []
        try:
            datatomorrow = prices_spot.hourly(end_date=(self.date()+datetime.timedelta(days=1)),areas=['FI'])           
            for i in datatomorrow['areas']['FI']['values']:
                priceslisttomorrow.append(round(i['value']/10*1.24+3.9+2.79372,3))
            priceslisttomorrowsorted=sorted(priceslisttomorrow)
            self.set_state("sensor.spot_cost_future", state=priceslisttomorrowsorted)
        except KeyError:
            if datetime.datetime.today().hour>10: # only check again during afternoon, Today() is in UTC time
                self.run_in(self.getprices, 300) # If there is no prices yet check again in 5 minutes
        if priceslisttomorrow[0] == float('inf'): 
            if datetime.datetime.today().hour>10: # only check again during afternoon, Today() is in UTC time
                self.run_in(self.getprices, 300) # If there is no prices yet check again in 5 minutes
            
        
    def updatecurrentprice(self,kwargs): #Get current price once an hour and update it
        prices_spot = elspot.Prices()
        now = datetime.datetime.now(pytz.utc)
        datatoday = prices_spot.hourly(end_date=self.date(),areas=['FI'])
        for rate in datatoday['areas']['FI']['values']:
            if rate['start'] <= now < rate['end']:
                self.set_state("sensor.spot_cost", state=round(rate['value']/10*1.24+3.9+2.79372,3))
                self.set_state("sensor.spot_sell", state=round(rate['value']/10,3))