import os
import time
import json
import sqlite3
from datetime import datetime
import cerberus.invoke.command as runcommand


def get_time(timestamp):
    return int(time.mktime(datetime.strptime(timestamp, '%Y-%m-%d %H:%M:%S').timetuple()))


def set_db_path(database_path):
    global db_path
    db_path = database_path


def create_db():
    if os.path.isfile(db_path):
        runcommand.invoke("rm " + db_path)
    sqlite3.connect(db_path)


def create_table():
    connection = sqlite3.connect(db_path)
    crsr = connection.cursor()
    command = """create table Failures (
                 timestamp timestamp,
                 time integer,
                 count integer,
                 issue text,
                 name text,
                 component text);"""
    crsr.execute(command)
    connection.commit()


def insert(timestamp, time, count, issue, names, component):
    connection = sqlite3.connect(db_path)
    crsr = connection.cursor()
    timestamp = timestamp.replace(microsecond=0)
    time = int(time)
    for name in names:
        crsr.execute("insert into Failures values (?, ?, ?, ?, ?, ?)",
                     (timestamp, time, count, issue, name, component))
    connection.commit()


def query(loopback):
    connection = sqlite3.connect(db_path)
    crsr = connection.cursor()
    finish_time = int(time.time())
    start_time = finish_time - loopback
    command = "select timestamp, count, issue, name, component from Failures where " \
              "time >= " + str(start_time) + " and time <= " + str(finish_time)
    crsr.execute(command)
    fetched_data = crsr.fetchall()
    create_json(fetched_data, 'cerberus_history.json')


def custom_query(filters):
    connection = sqlite3.connect(db_path)
    crsr = connection.cursor()
    start_time = ""
    finish_time = ""
    sdate = filters.get("sdate", "")
    stime = filters.get("stime", "")
    fdate = filters.get("fdate", "")
    ftime = filters.get("ftime", "")
    issue = filters.get("issue", ())
    name = filters.get("name", ())
    component = filters.get("component", ())

    if sdate and not stime:
        stime = "00:00:00"
    if fdate and not ftime:
        ftime = "23:59:59"

    if sdate:
        start_time = sdate + " " + stime
        start_time = get_time(start_time)
    if fdate:
        finish_time = fdate + " " + ftime
        finish_time = get_time(finish_time)

    command = "select timestamp, count, issue, name, component from Failures where "

    if start_time and finish_time:
        command += "time >= " + str(start_time) + " and time <= " + str(finish_time) + " and "
    elif start_time:
        command += "time >= " + str(start_time) + " and "
    elif finish_time:
        command += "time <= " + str(finish_time) + " and "

    if issue:
        command += "issue in " + str(issue + ('', )) + " and "
    if name:
        command += "name in " + str(name + ('', )) + " and "
    if component:
        command += "component in " + str(component + ('', )) + " and "

    command = command.strip().rsplit(' ', 1)[0]

    crsr.execute(command)
    fetched_data = crsr.fetchall()

    create_json(fetched_data, 'cerberus_analysis.json')


def create_json(fetched_data, file_name):
    failures = []
    for data in fetched_data:
        failure = {"timestamp": data[0], "count": data[1], "issue": data[2],
                   "name": data[3], "component": data[4]}
        failures.append(failure)

    history = {"history": {"failures": failures}}

    with open('./history/' + file_name, 'w+') as file:
        json.dump(history, file, indent=4, separators=(',', ': '))
