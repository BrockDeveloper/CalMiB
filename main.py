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

ENDPOINT_CORSI = 'https://gestioneorari.didattica.unimib.it/PortaleStudentiUnimib/grid_call.php'
ENDPOINT_ESAMI = 'https://gestioneorari.didattica.unimib.it/PortaleStudentiUnimib/test_call.php'
ROME = tz.gettz('Europe/Rome')

class ResponseMessage:
    def __init__(self, message: str):
        self.message = message


app = FastAPI(
    title='CalMiB',
    version='0.0.1',
    description='Calendar feed for unimib lessons',
)


@app.get('/esami/{corso}/{anno}/{anno_accademico}',
         responses={
             '503': {'description': 'Service Unavailable'},
         })
async def esami(
    corso: Course,
    anno: int = Path(title="L'anno solare del calendario",
                     ge=2020, le=datetime.utcnow().year),
    anno_accademico: int = Path(
        title="L'anno accademico di interesse", ge=1, le=3),
    lang: Lang = Lang.italian,
    alarms: bool = False,
):

    req = {
        'view': 'easytest',
        'include': 'et_cdl',
        'et_er': 1,
        'scuola': 'AreaScientifica-Informatica',
        'esami_cdl': corso,
        'anno2[]': anno_accademico,
        'datefrom': f"01-01-{anno}",
        'dateto': f"01-01-{anno+1}",
        'all_events': 1,
        '_lang': lang,
    }

    try:
        res = requests.post(ENDPOINT_ESAMI, data=req)
    except:
        return JSONResponse(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, content=ResponseMessage('Service Unavailable'))

    data = res.json()
    celle: dict = data['Insegnamenti']
    appelli: list = [celle[key]['Appelli'] for key in celle]

    def convert(apl: dict):
        e = Event()
        e.begin = datetime.fromtimestamp(
            apl['Timestamp'])

        # Ora fine se è tutto il giorno è 24:00 quindi non si riesce a parsare eg:: nel caso di chiusura_type
        ora_fine = apl['OraFine'].split(':')
        e.end = datetime.combine(e.begin.date(), time(
            int(ora_fine[0]), int(ora_fine[1]), tzinfo=ROME), tzinfo=ROME)

        if alarms:
            e.alarms = [DisplayAlarm(-timedelta(days=7)),
                        DisplayAlarm(-timedelta(days=1))]

        e.name = f"{apl['TipoEsame'].capitalize()} {apl['nome']} in {apl['AulaCodice'][0]}".strip()
        return e

    c = Calendar()
    c.events = [convert(apl) for apl_lst in appelli for apl in apl_lst]

    return Response(content=c.serialize(), media_type='text/calendar')


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
        res = requests.post(ENDPOINT_CORSI, data=req)
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




import uvicorn
if __name__ == "__main__":
  uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)