from fastapi import FastAPI, Path, Response, status
from fastapi.responses import JSONResponse
from enum import Enum
from ics import Calendar, Event, DisplayAlarm
from datetime import datetime, time, timedelta
from dateutil import tz
import requests
import re

from models.academicYear import AcademicYear
from models.course import Course
from models.group import Group
from models.lang import Lang

ENDPOINT = 'https://gestioneorari.didattica.unimib.it/PortaleStudentiUnimib/grid_call.php'
ROME = tz.gettz('Europe/Rome')

class ResponseMessage:
    def __init__(self, message: str):
        self.message = message


app = FastAPI(
    title='CalMiB',
    version='0.0.1',
    description='Calendar feed for unimib lessons',
)


@app.get('/{corso}/{anno}/{anno_accademico}/{percorso}',
         responses={
             '503': {'description': 'Service Unavailable'},
         })
async def root(
    corso: Course,
    percorso: Group,
    anno: int = Path(title="L'anno solare del calendario",
                     ge=2020, le=datetime.utcnow().year),
    anno_accademico: int = Path(
        title="L'anno accademico di interesse", ge=1, le=3),
    lang: Lang = Lang.italian,
    alarms: bool = False,
):

    req = {
        'view': 'easycourse',
        'include': 'corso',
        'all_events': 1,
        '_lang': lang,
        'anno': anno,
        'anno2[]': f"{percorso}|{anno_accademico}",
        'corso': corso,
    }

    try:
        res = requests.post(ENDPOINT, data=req)
    except:
        return JSONResponse(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, content=ResponseMessage('Service Unavailable'))

    data = res.json()
    celle: list = data['celle']

    def convert(ev: dict):
        e = Event()
        e.begin = datetime.fromtimestamp(
            ev['timestamp'], tz=ROME)

        # Ora fine se è tutto il giorno è 24:00 quindi non si riesce a parsare eg:: nel caso di chiusura_type
        if ev['tipo'] == 'chiusura_type':
            e.make_all_day()
            e.name =  re.sub('<[^<]+?>', '', ev['nome'])
        else:
            ora_fine = ev['ora_fine'].split(':')
            e.end = datetime.combine(e.begin.date(), time(
                int(ora_fine[0]), int(ora_fine[1]), tzinfo=ROME), tzinfo=ROME)

            if alarms:
                e.alarms = [DisplayAlarm(-timedelta(hours=3)),
                            DisplayAlarm(-timedelta(hours=2))]

            e.name = f"{ev['nome_insegnamento']} in {ev['codice_aula']} con {ev['docente']}"
        return e

    c = Calendar()
    c.events = [convert(ev) for ev in celle]

    return Response(content=c.serialize(), media_type='text/calendar')
