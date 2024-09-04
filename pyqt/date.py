from datetime import datetime
import pandas as pd


def get_timestamp(date):
    date = date.tz_localize(tz='Etc/GMT+4')
    timestamp = int(date.timestamp())
    return timestamp

def get_n_days_ago(days):
    today = pd.Timestamp.today().normalize()
    date = subtract_days(today, days)
    return date

def subtract_days(date, days):
    n_days = pd.Timedelta(days=days)
    date = date - n_days
    return date
