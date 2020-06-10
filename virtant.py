from __future__ import print_function
import datetime
import pickle
import os.path
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import os
import wikipedia
import time
import playsound
import speech_recognition as sr
#from gtts import gTTS #by google
import pyttsx3
import pytz #used for time zone
import subprocess # it opens the subprocess
import sounddevice
import webbrowser # it access the internet to explore the possibilities
import smtplib #used to access gmail to send the emails


SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']#link for gooogle calenders to fetch and manipulate data

#some global variables
MONTHS = ["january", "february", "march", "april", "may", "june","july", "august", "september","october", "november", "december"]
DAYS = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
DAY_EXTENTIONS = ["rd", "th", "st", "nd"]


def speak(text): #python's module for speech recognition
    # init function to get an engine instance for the speech synthesis
    engine=pyttsx3.init()
    # say method on the engine that passing input text to be spoken
    engine.say(text)
    # run and wait method, it processes the voice commands.
    engine.runAndWait()
    

#speak("initialising assisstant") #passing the parameter to the function speak

#wishes the user
def wishMe():
    hour = int(datetime.datetime.now().hour) # gives current hour
    if hour>=0 and hour<12:
        speak("good morning")
    elif hour>=12 and hour>18:
        speak("good afternoon")
    else:
        speak("good evening")

    speak("I am your virtual assisstant")
    speak("how may i help you?")

#sends email to a paricular email address
def sendEmail(to,content):
#first enable less secure apps in gmail
    server=smtplib.SMTP('smtp.gmail.com',587)#opens the port #587
    server.ehlo() #Extended HELO (EHLO) is an Extended Simple Mail Transfer Protocol (ESMTP) command sent by an email server to identify itself when connecting to another email server to start the process of sending an email.
    server.starttls()#opens the socket
    server.login('***email-id****','******password*****')#gives access to the sending email i.e sender's email # to run the email function you need to give the email id and password
    server.sendmail('***email-id****',to,content) #give access to the recepient
    server.close()# closes the socket

# user audio input, returns the text verision of whatever we say in the microphone
def get_audio():
    r=sr.Recognizer() #it recognizes the audio
    with sr.Microphone() as source: #using device's microphone
        #r.pause_threshold=1 #press ctrl and click here to change the microphone setting
        audio = r.listen(source) #listens through the microphone
        said="" #a variable
        try:
            said=r.recognize_google(audio) #convert audio to text using google's API
            print(said) #print the speech
        except Exception as e:
            print("Please Repeat: ")
            return "None"
    return said.lower()
#if the user gives a long enough pause then the func recognizes that the sentence is over

# authenticates the account and then prints the first 10 events in the calender
def authenticate_google():
    """Shows basic usage of the Google Calendar API.
    Prints the start and name of the next 10 events on the user's calendar.
    """
    creds = None

    #login begins
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)

        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)

    service = build('calendar', 'v3', credentials=creds)
    return service
    #login ends

def get_events(day, service):
    # Call the Calendar API

    # the below two lines are there for the time constraint of the day ie 00:00-23:59
    date = datetime.datetime.combine(day, datetime.datetime.min.time())
    end_date = datetime.datetime.combine(day, datetime.datetime.max.time())

    # will convert the date in UTC format
    utc = pytz.UTC
    date = date.astimezone(utc)
    end_date = end_date.astimezone(utc)

    events_result = service.events().list(calendarId='primary', timeMin=date.isoformat(), timeMax=end_date.isoformat(),
                                        singleEvents=True,
                                        orderBy='startTime').execute()
    events = events_result.get('items', [])

    if not events:
        speak('No upcoming events found.')
    else:
        speak(f"You have {len(events)} events on this day.")

        for event in events:
            start = event['start'].get('dateTime', event['start'].get('date'))
            print(start, event['summary'])
            start_time = str(start.split("T")[1].split("-")[0]) # get the hour the event starts
            if int(start_time.split(":")[0]) < 12: # if the event is in the morning
                start_time = start_time + "am"
            else:
                start_time = str(int(start_time.split(":")[0])-12) + start_time.split(":")[1] # convert 24 hour time to regular
                start_time = start_time + "pm"

            speak(event["summary"] + " at " + start_time)
            # the output comes in "2020-06-22T16:30:00+05:30" format, so we need to split the time wrt "T" and "-"

    # api concludes

#function to give the desired date
def get_date(text):
    text = text.lower() #converts any type of format to lower case
    today = datetime.date.today()  #to set default date as "TODAY"

    if text.count("today") > 0: #if the user talks about today any where in the text
        # it means if the usage of the word today is >0 then
        return today # return today's date

    # -1 as we dont know the current details and the year is considerd as "this year"
    day = -1
    day_of_week = -1
    month = -1
    year = today.year

    for word in text.split(): # loop through each word of the speech by the user
        if word in MONTHS: # if the word is present in the global list(written above) then..
            month = MONTHS.index(word) + 1 # make month=desired one
            # for example "september", it's index is 8 so, month=8+1=9

        # same for days
        elif word in DAYS:
            day_of_week = DAYS.index(word)
        elif word.isdigit():
            day = int(word)
        else:
            # what we are doing in here??
            # for example if we found "5th", then the pgm will find "th" and stores '5' in day
            for ext in DAY_EXTENTIONS:
                found = word.find(ext)
                if found > 0:
                    try:
                        day = int(word[:found])
                    except:
                        pass

    # if we found a month in the string of text and it is less than the current month of today then increment the year
    if month < today.month and month != -1:  # if the month mentioned is before the current month set the year to the next
        year = year+1

    # as long as we haven't defined the month and we have defined day and the current day is less than the current day
    if month == -1 and day != -1:  # if we didn't find a month, but we have a day
        if day < today.day:
            month = today.month + 1
        else:
            month = today.month

    # if we have just defined the day of the week (ex-tuesday)
    if month == -1 and day == -1 and day_of_week != -1:
        current_day_of_week = today.weekday() #today.weekday() will give the day in the numeric value
        #0-6 where 0 is monday and 6 is sunday
        dif = day_of_week - current_day_of_week #it gives the difference between the desired day and the current day
        #for example today is wednusday and the user is talking about friday, which means the friday in this week
        #so to get to friday we do friday(4)-wednusday(2)=2 so we can add 2 on wednusday(2) to get friday.

        # but what if the user asks for monday?, which is before wednusday
        if dif < 0:
            dif += 7 #we add 7 to the current week, i.e. move to the next week
            if text.count("next") >= 1:
                dif += 7

        return today + datetime.timedelta(dif) #this function does all the adjustment we want

    if day != -1:   # if any other task is assigned, then no need for date(else it will do this work  with -ve month and cause errors)
        return datetime.date(month=month, day=day, year=year)# gives the desired day,month and year

def note(text): # to take notes
    date=datetime.datetime.now() #makes the date to today's day
    file_name =str(date).replace(":","-") + "-note.txt" # saves the notes as .txt
    with open(file_name,"w") as f:
        f.write(text)

    subprocess.Popen(["notepad.exe",file_name]) #opens the "filename" in windows' notepad
# or if you want to open another editor then write the path of it


# code begins here
WAKE="hello" #like hey siri
SERVICE = authenticate_google()
speak("Initialising VarTant")
wishMe()
while True:
    print("Listening")#always displays this line
    text = get_audio() #calls the function for verification of the wake keyword
    if text.count(WAKE) > 0:
        speak("I am Ready")
        text=get_audio()

        #accessing wikipedia
        if 'wikipedia' in text:
            speak("searching wikipedia....")
            text1=text
            text1=text.replace("wikipedia", "")# for example we search "SRK wikipedia", it eleminates the word wikipedia amd just search SRK on the wikipedia server
            results=wikipedia.summary(text,sentences=2)#just 2 lines from wikipedia
            speak("Acording to wikipedia")
            print(results)
            speak(results)

        #code to launch websites
        elif 'open youtube' in text:

            webbrowser.open("youtube.com")

        #code to open in built apps
        elif 'play music' in text:
            music_dir = 'C:\\Users\\Ark Pandey\\Desktop\\songs' #path for songs
            songs=os.listdir(music_dir)#loads the directory
            print(songs)
            os.startfile(os.path.join(music_dir,songs[0])) #opens the folder and plays the first song

        #code to send email
        elif 'email to' in text:
            try:
                speak("what should I say?")
                content = get_audio()
                to = '***email_id***' #edit this with the recepiant email id
                sendEmail(to,content) #sends the email, read its's function
                print('email sent')
                speak("email sent")

            except Exception as e:
                print(e)
                speak("I can't send")

        #give the time
        elif 'the time' in text:
            strtime=datetime.datetime.now().strftime("%H:%M:%S") #hour min sec
            speak(f"Sir, the time is {strtime}")

        #open any built in program
        elif 'open photos' in text: #search the given pgm
            photopath="C:\\Users\\Ark Pandey\\Desktop\\nani's photos" #provide the path
            os.startfile(photopath) #call the os module to open the path

        elif 'stop' in text:
            exit()

        CALENDAR_STRS = ["what do i have", "do i have plans", "am i busy"]
        for phrase in CALENDAR_STRS:
            if phrase in text:
                date = get_date(text)  # if something like in the list is enterd, then assign today's date
                if date:
                    get_events(date, SERVICE)
                else:
                    speak("I don't understand")

        # code to make a note using notepad
        NOTE_STRS=["make a note","write this down","remember"] #if this stmt exists in the text then the function runs
        for phrase in NOTE_STRS:
            if phrase in text:
                speak("What would you like me to write down? ")
                write_down = get_audio()
                note(write_down)
                speak("I've made a note of that.")
