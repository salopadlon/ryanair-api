from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
import requests
from datetime import datetime
import matplotlib.pyplot as plt
from fastapi.staticfiles import StaticFiles

app = FastAPI()

templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/")
async def root(request: Request) -> Jinja2Templates.TemplateResponse:
    airports = get_airports()
    return templates.TemplateResponse('index.html',
                                      {"request": request, "airports": airports})


@app.post("/search-prices")
async def search(request: Request):
    data = {}

    try:
        data = dict(await request.form())
    except Exception as e:
        print(e)

    code_from = get_code_from_name(data["airport_from"])
    code_to = get_code_from_name(data["airport_to"])

    # airports_to = get_connections_from_airport(get_code_from_name(data["airport_from"]))
    dates_list = get_dates(code_from, code_to, datetime.strptime(data["date_from"], "%Y-%m-%d"),
                           datetime.strptime(data["date_to"], "%Y-%m-%d"))
    fares_dict = get_fares(dates_list, code_from, code_to)
    result, image_path = create_graph(fares_dict)
    return {"show_graph": result, "image_path": image_path}


def get_airports() -> list:
    airports_list = []
    response = requests.get("https://www.ryanair.com/api/locate/v1/autocomplete/airports?phrase=&market=en-gb")
    for airport in response.json():
        airports_list.append(airport["name"] + " (" + airport["code"] + ")")
    return airports_list


def get_connections_from_airport(airport: str):
    response = requests.get(
        f"https://www.ryanair.com/api/locate/v1/autocomplete/routes?arrivalPhrase&departurePhrase={airport}"
        f"&market=en-gb")
    return response.json()


def get_dates(airport_from: str, airport_to: str, date_from: datetime, date_to: datetime) -> list:
    date_list = []
    response = requests.get(
        f"https://www.ryanair.com/api/farfnd/3/oneWayFares/{airport_from}/{airport_to}/availabilities")
    for date in response.json():
        date_dt = datetime.strptime(date, "%Y-%m-%d")
        if date_from <= date_dt <= date_to:
            date_list.append(date)
    return date_list


def get_fares(dates_list: list, airport_from: str, airport_to: str):
    fares_dict = {}
    for date in dates_list:
        response = requests.get(
            f"https://www.ryanair.com/api/booking/v4/en-gb/availability?ADT=1&CHD=0&DateIn=&DateOut={date}"
            f"&Destination={airport_to}&Disc=0&INF=0&Origin={airport_from}"
            f"&TEEN=0&promoCode=&IncludeConnectingFlights=false&FlexDaysBeforeOut=0&FlexDaysOut=0&ToUs=AGREED")
        try:
            fares_dict[date] = [flight["regularFare"]["fares"][0]["amount"] for flight in
                                response.json()["trips"][0]["dates"][0]["flights"]]
        except Exception:
            pass
    return fares_dict


def create_graph(fares_dict: dict) -> list:
    x = list(fares_dict.keys())
    y = list(fares_dict.values())

    fig, ax = plt.subplots()

    if len(x) < 1 or len(y) < 1:
        return [0, ""]
    elif [len(element) > 1 for element in y]:
        y_min = [min(element) for element in y]
        y_max = [max(element) for element in y]
        y_avg = [average(element) for element in y]
        plt.clf()
        plt.plot(x, y_min)
        plt.plot(x, y_max)
        plt.plot(x, y_avg)
    else:
        plt.clf()
        plt.plot(x, y)

    fig.autofmt_xdate()

    image_path = f'static/img/my_plot'+str(datetime.now())+'.png'
    plt.savefig(image_path)

    return [1, image_path]


def average(fares_list) -> float:
    return sum(fares_list) / len(fares_list)


def get_code_from_name(airport: str) -> str:
    return airport[airport.find("(") + 1:airport.find(")")]
