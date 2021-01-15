# -*- coding: utf-8 -*-
"""
Created on Fri Aug 28 12:58:39 2020

@author: Ram
"""
import os
import datetime
from datetime import timedelta
import glob
import logging
from urllib.request import urlopen
from urllib.parse import urlparse
from bs4 import BeautifulSoup as bs
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import tabula


#AP govt uloads Daily covid bulletins to the below website
MAIN_URL = "http://hmfw.ap.gov.in/covid_19_dailybulletins.aspx"

'''
Page number and Area information is measured manually ysing tabula GUI.
This area is where summary of daily report presented in table format.
'''
PAGE_NUMBER = 1
AREA_ON_PAGE = (342, 46, 760, 567)

# The data before 20-06-2020 is in different format so ignoring it.
START_DATE = '20-06-2020'

DISTRICTS = ['Anantapur', 'Chittoor', 'East Godavari', 'Guntur',
             'Kadapa', 'Krishna', 'Kurnool', 'Nellore', 'Prakasam',
             'Srikakulam', 'Visakhapatnam', 'Vizianagaram',
             'West Godavari']
NO_OF_DISTRICTS = len(DISTRICTS)

# configuraiton of logger
logging.basicConfig(filename='logfile', filemode='a',
                    format='%(asctime)s - %(levelname)s - %(message)s',
                    level=logging.DEBUG)



class State:
    '''
    This class implements various methods to create different types of charts
    based on daily covid bulletins issued by government of andhra pradesh.
    '''
    
    def __init__(self):
        pass
    
    def __getallthedates(self):
        '''
        This method parses AP goverments main page where its daily bulletins
        are published and returns list of dates for which daily bulletin is
        uploaded to the website.
        '''
        try:
            main_page = urlopen(MAIN_URL)
            main_page_content = main_page.read()
        except Exception as open_url:
            logging.error("There is problem reading main url", exc_info=True)
            raise Exception(open_url)
        soup = bs(main_page_content, 'html.parser')
        list_of_dates = []
        for link in soup.find_all("a"):
            temp = link["href"]
            if "covid_19" in temp:
                parsed = urlparse(temp)
                list_of_dates.append(parsed.query[5:15])
        return list_of_dates
        
    def __parsedata(self, startdate=None, enddate=None):
        '''
        This method parses all the CSV files and combines the required data
        into single datframe for the given date range.
        '''
        #logging.debug(f'start date is: {startdate}, end date is: {enddate} in parsing')
        fileslist = glob.glob("*2020.csv")
        fileslist = [datetime.datetime.strptime(each_f[0:10], '%d-%m-%Y') for each_f in fileslist]
        fileslist.sort()
        covid_summary = pd.DataFrame(index=DISTRICTS)
        for each_d in fileslist:
            if each_d >= startdate and each_d <= enddate:
                date_string = each_d.strftime('%d-%m-%Y')
                filename = date_string +'.csv'
                temp_covid_summary = pd.read_csv(filename, nrows=13, header=0,
                                                 usecols=[1, 2],
                                                 names=['District', 'Positivecases'])
                covid_summary[date_string] = list(temp_covid_summary['Positivecases'])
        
        covid_summary_t = covid_summary.transpose()
        return covid_summary_t
    
    def __getdata(self, startdate=START_DATE, enddate=None):
        '''
        This method takes list of dates as input and opens the corresponding
        daily covid bulletins which are in pdf format and then selects the
        required data from pdf using tabula and converts it into CSV file
        and stores the data into local computer.
        It downloads only files from 20-06-2020, before that format is
        different.
        '''
        yesterday = datetime.datetime.today()-timedelta(days=1)
        startday = datetime.datetime.strptime(START_DATE, '%d-%m-%Y')
        max_date = datetime.datetime.strftime(yesterday, '%d-%m-%Y')
        logging.info(f'startdate is : {startdate}, enddate is : {enddate}')
        try:
            if enddate is None:
                enddate = yesterday
            else:
                date_obj = datetime.datetime.strptime(enddate, '%d-%m-%Y')
                if date_obj < startday or date_obj > yesterday:
                    logging.error(f"End date should be between {START_DATE}, {max_date}")
                    raise Exception(f"End date should be between {START_DATE}, {max_date}")
                else:
                    enddate = date_obj
                     
            if startdate is None:
                startdate = startday
            else:
                date_obj = datetime.datetime.strptime(startdate, '%d-%m-%Y')
                if date_obj < startday or date_obj > yesterday:
                    logging.error(f"Start date should be between {START_DATE}, {max_date}")
                    raise Exception(f"Start date should be between {START_DATE}, {max_date}")
                else:
                    startdate = date_obj
             
        except:
            logging.error("Input dates are invalid", exc_info=True)
            raise Exception("Invalid input dates")
    
        try:
            list_of_dates = self.__getallthedates()
        except Exception as invalid_dates:
            raise Exception(invalid_dates)
            
        if not os.path.exists("csv_files"):
            os.mkdir('csv_files')
            logging.debug("csv_files directory is created")
        else:
            logging.debug("csv_files directory already exists")
            
        os.chdir("csv_files")
        fileslist = glob.glob("*2020.csv")
        fileslist = [each_f[0:10] for each_f in fileslist]
         
        for each_d in list_of_dates:
            if each_d not in fileslist:
                date_obj = datetime.datetime.strptime(each_d, '%d-%m-%Y')
                if date_obj >= startdate and date_obj <= enddate:
                    logging.debug(f"Preparing file for date: {each_d}")
                    link = "http://hmfw.ap.gov.in/Daily_bullettin/" + \
                            each_d + "/" + each_d + "_10AM_Telugu.pdf"
                    tabula.convert_into(link, each_d+".csv",
                                        output_format="csv", lattice=True,
                                        pages=PAGE_NUMBER, area=AREA_ON_PAGE)
            else:
                logging.debug("Downloading is completed")
                break
            
        covid_summary = self.__parsedata(startdate, enddate)
        return covid_summary
     
    def districts_covid_trend(self, startdate=START_DATE, enddate=None):
        '''
        This method draws linecharts together for all the districts for given dates.
        '''
        try:
            covid_summary_t = self.__getdata(startdate, enddate)
        except Exception as get_data:
            logging.error("Problem in getting the data for analysis")
            raise Exception(get_data)
        
        plt.figure(figsize=(60, 10), dpi=100)
        plt.xticks(rotation=70)
        for col in covid_summary_t.columns:
            plt.plot(np.array(covid_summary_t.index),
                     np.array(covid_summary_t[col]),
                     label=str(col))
    
        plt.gca().set(title="District wise trend", xlabel="Date",
                      ylabel="No of new corona positive cases")
        plt.legend()
        plt.show()
        return
    
    def state_covid_trend(self, startdate=START_DATE, enddate=None):
        '''
        This method draws line chart for total number of covid cases for entire state
        '''
        try:
            covid_summary = self.__getdata(startdate, enddate)
        except Exception as get_data:
            logging.error("Problem in getting the data for analysis")
            raise Exception(get_data)
        
        covid_summary['summary'] = covid_summary.aggregate(func=sum, axis=1)
        plt.figure(figsize=(60, 10), dpi=100)
        plt.xticks(rotation=70)
        plt.plot(np.array(covid_summary.index), np.array(covid_summary['summary']))
        plt.gca().set(title="State corona trend", xlabel="Date",
                      ylabel="No of new corona positive cases")
        plt.legend()
        plt.show()
        return
    
    def state_covid_summary(self, startdate=START_DATE, enddate=None):
        '''
        This method draws districtwise summary of state covide cases.
        '''
        pass
    