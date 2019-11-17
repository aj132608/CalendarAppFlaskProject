from __future__ import print_function
import datetime
import pickle
import os.path
import string
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request


class CalendarProject:
    def __init__(self):
        # If modifying these scopes, delete the file token.pickle.
        self.SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']
        self.current_day = datetime.datetime.now()
        self.next_week_day = self.set_next_week()
        self.week_iterator = 1

    # gets the first day of the week
    def get_first_day(self, current_day):

        week_number = current_day.strftime("%w")

        current_hours = current_day.strftime("%H")
        current_minutes = current_day.strftime("%M")

        day_offset = datetime.timedelta(days=int(week_number), 
                                        hours=int(current_hours),
                                        minutes=int(current_minutes))

        first_day_of_week = current_day - day_offset

        # print("First day of the week: %s\n" % first_day_of_week)

        return first_day_of_week

    # returns the last day of the week given the first day of the week
    def get_last_day(self, first_day):

        day_offset = datetime.timedelta(days=7)

        last_day = first_day + day_offset

        # print("Last Day of the Week: ",last_day,"\n")

        return last_day

    # returns the date in month/day/year format

    def get_readable_dates(self, raw_dates):

        new_dates = []

        for raw_date in raw_dates:
            month = raw_date.split('-', 2)[1]
            day = raw_date.split('-', 2)[2]
            year = raw_date.split('-', 2)[0]

            new_dates.append(month + '/' + day + '/' + year)
        
        return new_dates

    def get_twelve_hour_time(self, raw_time):
        hours = raw_time.split(':', 2)[0]
        minutes = raw_time.split(':', 2)[1]
        seconds = raw_time.split(':', 2)[2]
        hours_int = int(hours)
        if hours_int > 12:
            hours_int -= 12

            # checks if the hours are single digits
            if hours_int < 10:

                # adds a zero to the front to make it 2 digits
                # and sets it as the new string value of hours
                hours = '0'+str(hours_int)
            else:

                # sets hours to the new value
                hours = str(hours_int)

            if hours == '12':
                return hours + ':' + minutes + ':' + seconds + 'AM'
            else:
                return hours + ':' + minutes + ':' + seconds + 'PM'

        elif hours_int == 12:
            return raw_time + 'PM'
        else:
            return raw_time + 'AM'

    # parses the datetime output and separates the date and time

    def get_dates_and_times(self, raw_date_info):
        dates = []
        # readable_dates = []
        times = []
        # readable_times = []

        # print test
        # print(raw_date_info)
        
        for info in raw_date_info:
            # print(info)
            if 'T' in info:
                dates.append(info.split('T', 1)[0])
                times.append(info.split('T', 2)[1])
            else:
                dates.append(info)
                times.append('All Day')

        return dates, times

    def get_readable_times(self, raw_times):
        times = []
        
        for time in raw_times:
            if time == 'All Day':
                times.append('All Day')
            else:
                times.append(self.get_twelve_hour_time(time.split('-')[0]))
        
        return times

    def set_next_week(self):
        date_offset = datetime.timedelta(days=7)

        next_week_day = self.current_day + date_offset
        
        return next_week_day

    # returns the duration of an event given the 
    # start and end times

    def get_event_duration(self, first_time, last_time):
        import math
        # expected input
        # first_time = '09:30:00AM'
        # last_time = '04:00:00PM'

        # expected output (in hours)
        # 6.5

        first_hours = int(first_time.split(':', 2)[0])
        first_minutes = int(first_time.split(':', 2)[1])
        first_seconds_with_string = first_time.split(':', 2)[2]
        
        if first_hours < 12 and 'PM' in first_seconds_with_string:
            first_hours += 12
        
        first_seconds = int(first_seconds_with_string[:-2])

        first_total_time = first_hours + (first_minutes/60) + (first_seconds/3600)

        last_hours = int(last_time.split(':',2)[0])
        last_minutes = int(last_time.split(':',2)[1])
        last_seconds_with_string = last_time.split(':',2)[2]

        if last_hours < 12 and 'PM' in last_seconds_with_string:
            last_hours += 12

        last_seconds = int(last_seconds_with_string[:-2])

        last_total_time = last_hours + (last_minutes/60) + (last_seconds/3600)

        event_duration = last_total_time - first_total_time

        # convert hours to hours and minutes

        hours = math.floor(event_duration)
        minutes = (event_duration % 1) * 60

        return hours, minutes

    def get_calendar_dict(self, now, service):
        week_dict = {f"week{self.week_iterator}": {
            "duration": "",
            "events": {}
        }}

        week_info = week_dict[f'week{self.week_iterator}']

        event_dict = week_info['events']

        first_day = self.get_first_day(now)
        first_day_iso = first_day.isoformat() + 'Z'

        last_day = self.get_last_day(first_day)
        last_day_iso = last_day.isoformat() + 'Z'

        day_offset = datetime.timedelta(days=1)
        actual_last_day = last_day - day_offset

        string_duration = str(first_day.strftime("%x") + ' - ' + actual_last_day.strftime("%x"))

        week_info['duration'] = string_duration

        events_result = service.events().list(calendarId='primary', timeMin=first_day_iso, timeMax=last_day_iso,
                                              singleEvents=True, orderBy='startTime').execute()
        events = events_result.get('items', [])

        event_summaries = []
        all_events_start = []
        all_events_end = []

        if not events:
            print('No upcoming events found.\n')

        for event in events:
            start = event['start'].get('dateTime', event['start'].get('date'))
            end = event['end'].get('dateTime', event['end'].get('date'))

            all_events_start.append(start)
            all_events_end.append(end)

            event_summaries.append(event['summary'])

        (start_dates, start_times) = self.get_dates_and_times(all_events_start)
        (end_dates, end_times) = self.get_dates_and_times(all_events_end)

        # get the unprocessed start and end times and dates

        if len(start_dates) == 0:
            print("You do not have anything going on this week. Yay!\n")
            exit()

        # get the dates in month/day/year format

        processed_start_dates = self.get_readable_dates(start_dates)
        processed_end_dates = self.get_readable_dates(end_dates)

        # get the times in 12 hour format

        processed_start_times = self.get_readable_times(start_times)
        processed_end_times = self.get_readable_times(end_times)

        for i in range(0, len(processed_start_times)):

            event_dict[f"event{i+1}"] = {"name": "", "dates": "", "times": "", "duration": ""}
            current_event = event_dict[f"event{i+1}"]

            if processed_start_dates[i] == processed_end_dates[i]:
                # event_times.append(processed_start_dates[i])
                current_event['dates'] = processed_start_dates[i]
            else:
                # event_times.append(processed_start_dates[i] + ' - ' + processed_end_dates[i])
                current_event['dates'] = processed_start_dates[i] + ' - ' + processed_end_dates[i]

            current_event['name'] = event_summaries[i]

            if processed_end_times[i] == 'All Day':
                # event_durations.append('All Day')
                current_event['duration'] = "All Day"
            else:
                duration_str = ""
                (hours, minutes) = self.get_event_duration(processed_start_times[i], processed_end_times[i])
                if hours == 0:
                    duration_str = '%.0f minutes' % minutes
                else:
                    duration_str = f"{hours} hours and %.0f minutes" % minutes

                current_event['duration'] = duration_str

            current_event['times'] = f"{processed_start_times[i]} - {processed_end_times[i]}"

        self.week_iterator += 1

        return week_dict

    def main(self):
        """Shows basic usage of the Google Calendar API.
        Prints the start and name of the next 10 events on the user's calendar.
        """

        creds = None
        # The file token.pickle stores the user's access and refresh tokens, and is
        # created automatically when the authorization flow completes for the first
        # time.
        try:
            if os.path.exists('token.pickle'):
                with open('token.pickle', 'rb') as token:
                    creds = pickle.load(token)
        except:
            print("Problem with Pickle")
        
        # If there are no (valid) credentials available, let the user log in.
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    'credentials.json', self.SCOPES)
                creds = flow.run_local_server()

            # Save the credentials for the next run
            with open('token.pickle', 'wb') as token:
                pickle.dump(creds, token)

        service = build('calendar', 'v3', credentials=creds)

        current_week_dict = self.get_calendar_dict(self.current_day, service)
        next_week_dict = self.get_calendar_dict(self.next_week_day, service)

        full_dict = {}

        for key in current_week_dict.keys():
            full_dict[key] = current_week_dict[key]

        for key in next_week_dict.keys():
            full_dict[key] = next_week_dict[key]

        return full_dict





