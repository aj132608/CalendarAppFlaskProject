from flask import Flask
from calendarProject import CalendarProject

app = Flask(__name__)


@app.route('/')
def calender_app():
    import json
    import os

    calendar_dict = CalendarProject().main()

    try:
        with open('calendar.json', 'w') as json_file:
            json.dump(calendar_dict, json_file)
    except:
        return "JSON Creation Unsuccessful"
    else:
        return f"calendar.json successfully created at {os.getcwd()}"


if __name__ == '__main__':
    app.run(debug=True)
