# -*- coding: utf-8 -*-
"""
Created on Sat Aug 29 16:11:33 2020

@author: Ram
"""
import statewise

def main():
    
    andhra = statewise.State()
    '''
    The date format should be '%d-%m-%Y'
    '''
    try:
        andhra.districts_covid_trend()
    except Exception as e:
        print(e)
    
    #Prakasam = District()
    #prakasam.histogram()
    
    pass

if __name__ == "__main__":
    main()
    