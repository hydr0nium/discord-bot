
import requests
from bs4 import BeautifulSoup
import discord
from discord.ext import commands, tasks
from timezonefinder import TimezoneFinder
import pytz
import datetime
import time
import random

file = open("../token.txt","r")
TOKEN = str(file.read())
language = "en"
location = "Deutschland"
bot = commands.Bot(command_prefix="!")
log_path = "../log.txt"
last_update = ""
vaccinations = 0




# --------------------------------------------------------------------------------------------


def get_time_from_location(lat, lon):
    tf = TimezoneFinder()
    ret = tf.timezone_at(lng=float(lon), lat=float(lat))
    tz = pytz.timezone(ret)
    normal = datetime.datetime.utcfromtimestamp(time.time())
    offset = tz.utcoffset(normal, is_dst=True)
    loc_time = datetime.datetime.utcnow() + offset
    loc_time = str(loc_time).split(" ")[1].split(".")[0]
    return loc_time


def get_weather_img(info_uncut):
    info = info_uncut.split("C ")[1].split("\n")[0]
    print(info)
    if info == "Stark bewölkt" or info == "Overcast":
        return "https://ssl.gstatic.com/onebox/weather/64/cloudy.png"

    elif info == "Überwiegend bewölkt" or info == "Mostly Cloudy":
        return "https://ssl.gstatic.com/onebox/weather/64/cloudy.png"

    elif info == "Leicht bewölkt" or info == "Partly Cloudy":
        return "https://ssl.gstatic.com/onebox/weather/64/partly_cloudy.png"

    elif info == "Klar":
        return "https://ssl.gstatic.com/onebox/weather/64/sunny.png"

    elif info == "Hohe Luftfeuchtigkeit und überwiegend bewölkt":
        return "https://ssl.gstatic.com/onebox/weather/64/cloudy.png"

    elif info == "Nieselregen möglich":
        return "https://ssl.gstatic.com/onebox/weather/48/rain_s_cloudy.png"

    elif "Snow" in info or "Schnee" in info:
        return "https://ssl.gstatic.com/onebox/weather/48/snow.png"

    elif "Leichter Regen möglich" in info:
        return "https://ssl.gstatic.com/onebox/weather/48/rain_s_cloudy.png"

    else:
        ran = random.randint(1, 5000)
        print(ran)
        return "https://www.univerzities.com/Images/Uni/logo"+ str(ran) + ".jpg"


def parse_html(array, class_name):
    if len(array) == 0:
        return 0.0
    cut1 = str(array[0])[(13+len(class_name)+2)::]
    flipped = cut1[::-1]
    cut2 = flipped[8::]
    out = cut2[::-1]
    return out


def weather_func(place, lang):
    # Initialise lat,lon
    out = ""
    # Generate lat,long from place
    place = place.replace("/", "").replace(":", "").replace("@", "").replace(".", "")
    rep2 = requests.get("http://www.geonames.org/search.html?q=" + place)
    html2 = rep2.text
    parsed2 = BeautifulSoup(html2, "html.parser")
    lat_a = parsed2.find_all("span", "latitude")
    lon_a = parsed2.find_all("span", "longitude")

    lat = parse_html(lat_a, "latitude")
    lon = parse_html(lon_a, "longitude")
    coords = str(lat) + "," + str(lon)
    time_loc = get_time_from_location(lat, lon)
    # Generate Weather from place
    rep = requests.get("https://darksky.net/forecast/" + coords + "/ca24/" + lang)
    html = rep.text
    parsed = BeautifulSoup(html, "html.parser")
    weather_p = parsed.find_all("span", "summary swap")
    out = out + parse_html(weather_p, "summary swap")
    out = out.replace("\xa0", "C ")
    out = out + "\n" + time_loc
    if (len(lat_a) + len(lon_a)) == 0:
        out = "Your supplied location was not in our list or wrongly supplied!\n"
    return out

# ------------------------------------------------------------------------------------------------------------


@tasks.loop(minutes=5)
async def weather_update():

    listOfGlobals = globals()
    language_l = listOfGlobals['language']
    location_l = listOfGlobals['location']
    weather_status = weather_func(location_l, language_l)
    weather_status = weather_status[:32:]
    weather_status = weather_status.split("\n")[0]
    await bot.change_presence(activity=discord.Game(str(location_l).capitalize() + ": " + weather_status))


@bot.command(pass_context=True, brief="Prints some weather data for some given parameters")
@commands.cooldown(1, 0, commands.BucketType.user)
async def weather(ctx, *args):
    global language
    global location
    username = ctx.author.name
    command = "!weather "
    usage = "Usage: !weather <location> <en/de> \nLanguage is optional\nReturns the weather for the location in the choosen language"
    title = "Ehmmmm"
    tim = "The cake is a lie?!"
    time_loc = "69 Nice"
    img = "https://cdn.discordapp.com/emojis/550697172039893054.png?v=1"
    weather_out = "WTF IS WRONG WITH YOU?!"
    temp = "404 ad missing or is it?"

    if len(args) == 2:
        arg1 = args[0]
        arg2 = args[1]
        ret = weather_func(str(arg1), str(arg2))
        if arg2 == "en" or arg2 == "de":
            if arg2 == "en":
                language = "en"
                title = "Weather in "
                temp = "Temperature"
                tim = "Local Time"
                command = command + arg1 + " en"

            if arg2 == "de":
                language = "de"
                title = "Wetter in "
                temp = "Temperatur"
                tim = "Lokale Uhrzeit"
                command = command + arg1 + " de"

            if ret != "Your supplied location was not in our list or wrongly supplied!\n":
                location = str(arg1).capitalize()
                title = title + location
                img = get_weather_img(ret)
                time_loc = ret.split("\n")[1]
                weather_out = ret.split("\n")[0]
                await bot.change_presence(activity=discord.Game(str(arg1).capitalize() + ": " + weather_out))

            embed = discord.Embed(title=title, color=discord.Color.green())
            embed.set_thumbnail(url=img)
            embed.add_field(name=temp, value=weather_out, inline=True)
            embed.add_field(name=tim, value=time_loc, inline=True)
            await ctx.send(embed=embed)


        else:
            await ctx.send("Please use a valid language option! For help see !weather")
            command = command + arg1 + " " + arg2

    elif len(args) == 1:
        arg1 = args[0]
        ret = weather_func(str(arg1), language)
        if ret != "Your supplied location was not in our list or wrongly supplied!\n":
            if language == "en":
                title = "Weather in "
                temp = "Temperature"
                tim = "Local Time"

            if language == "de":
                title = "Wetter in "
                temp = "Temperatur"
                tim = "Lokale Uhrzeit"

            command = command + arg1
            location = str(arg1).capitalize()
            title = title + location
            img = get_weather_img(ret)
            time_loc = ret.split("\n")[1]
            weather_out = ret.split("\n")[0]
            await bot.change_presence(activity=discord.Game(str(arg1).capitalize() + ": " + weather_out))

        embed = discord.Embed(title=title, color=discord.Color.green())
        embed.set_thumbnail(url=img)
        embed.add_field(name=temp, value=weather_out, inline=True)
        embed.add_field(name=tim, value=time_loc, inline=True)
        await ctx.send(embed=embed)

    elif len(args) == 0:
        await ctx.send(usage)
    log(username, command)

# ---------------------------------------------------------------------------------------------
def parse_corona(string):
    string = string[48::]
    string = string[::-1]
    string = string[8::]
    string = string[::-1]
    return string

def get_imf_deutsch():
    global vaccinations
    ret = vaccinations
    global last_update
    print(last_update)
    dic = {"de/saar": "saarland", "de/thr": "thüringen", "de/saan": "sachsen-anhalt", "de/bra": "brandenburg",
           "de/sa": "sachsen", "de/he": "hessen", "de/ber": "berlin", "de/bay": "bayern",
           "de/meckpom": "mecklenburg-vorpommern",
           "de/nrw": "nordrhein-westfalen", "de/shs": "schleswig-holstein", "de/rlp": "rheinland-pfalz",
           "de/bwb": "baden-württemberg", "de/ns": "niedersachsen", "de/ham": "hamburg", "de/bre": "bremen"}
    if str(datetime.date.today()) != last_update:
        ret = 0
        for b in dic:
            bundesland = dic.get(b)
            req = requests.get("https://www.corona-in-zahlen.de/bundeslaender/" + bundesland)
            html_data = req.text
            parsed = BeautifulSoup(html_data, "html.parser")
            numbers_a = parsed.find_all("p", "card-title")
            impfungen = parse_corona(str(numbers_a[7]))
            impfungen = impfungen.replace(".", "")
            ret = ret + int(impfungen)
        last_update = str(datetime.date.today())
        print("Last_update updated to: " + str(datetime.date.today()))
        ret = str(ret)
        ret = ret[::-1]
        out = ""
        for i in range(0, len(ret)-3, 3):
            out = out + ret[i:i+3] + "."
        out = out[::-1]
        vaccinations = out

    return vaccinations




@bot.command(pass_context=True, brief="Prints the current corona numbers for some given parameters")
@commands.cooldown(1, 0, commands.BucketType.user)
async def corona(ctx, *args):

    username = str(ctx.author.name)
    command = "!corona "

    corona_img = "https://cdn.cnn.com/cnnnext/dam/assets/200130165125-corona-virus-cdc-image-super-tease.jpg"
    dic = {"de/saar": "saarland", "de/thr": "thüringen", "de/saan": "sachsen-anhalt", "de/bra": "brandenburg",
           "de/sa": "sachsen", "de/he": "hessen", "de/ber": "berlin", "de/bay": "bayern", "de/meckpom": "mecklenburg-vorpommern",
           "de/nrw": "nordrhein-westfalen", "de/shs": "schleswig-holstein", "de/rlp": "rheinland-pfalz",
           "de/bwb": "baden-württemberg", "de/ns": "niedersachsen", "de/ham": "hamburg", "de/bre": "bremen"}

    if len(args) == 1 and args[0] == "numbers":

        req = requests.get("https://www.worldometers.info/coronavirus/")
        html_data = req.text
        parsed = BeautifulSoup(html_data, "html.parser")
        numbers_unparsed = parsed.find_all("title")[0]
        cases = str(numbers_unparsed).split("and")[0].split(":")[1].replace(",", ".").split(" ")[1]
        deaths = str(numbers_unparsed).split("and")[1].split("from")[0].replace(",", ".").split(" ")[1]
        embed = discord.Embed(title="Corona Numbers Worldwide", color=discord.Color.red())
        embed.add_field(name="Cases:", value=cases, inline=True)
        embed.add_field(name="Deaths:", value=deaths, inline=True)
        embed.set_thumbnail(url=corona_img)
        await ctx.send(embed=embed)
        command = command + "numbers"

    elif len(args) == 2 and args[0] == "numbers" and args[1] == "de":
        req = requests.get("https://www.corona-in-zahlen.de/weltweit/deutschland/")
        html_data = req.text
        parsed = BeautifulSoup(html_data, "html.parser")
        numbers_a = parsed.find_all("p", "card-title")
        einwohner = parse_corona(str(numbers_a[0]))
        infektionen = parse_corona(str(numbers_a[1]))
        infektionsrate = parse_corona(str(numbers_a[2]))
        neuinfektionen_s_days = parse_corona(str(numbers_a[3]))
        deaths = parse_corona(str(numbers_a[4]))
        tödlichkeit = parse_corona(str(numbers_a[5]))
        neuinfektionen = parse_corona(str(numbers_a[6]))
        new_deaths = parse_corona(str(numbers_a[8]))
        tests_insgesamt = parse_corona(str(numbers_a[9]))
        impf_gesamt = get_imf_deutsch();
        embed = discord.Embed(title="Corona Numbers Germany", color=discord.Color.red())
        embed.add_field(name="Population:", value=einwohner, inline=True)
        embed.add_field(name="Infections:", value=infektionen, inline=True)
        embed.add_field(name="Infection Rate: ", value=infektionsrate, inline=True)
        embed.add_field(name="New Infection per 100.000 people / 7 days: ", value=neuinfektionen_s_days, inline=True)
        embed.add_field(name="Deaths: ", value=deaths, inline=True)
        embed.add_field(name="Lethality: ", value=tödlichkeit, inline=True)
        embed.add_field(name="New Infections: ", value=neuinfektionen, inline=True)
        embed.add_field(name="New Deaths: ", value=new_deaths, inline=True)
        embed.add_field(name="All tests done: ", value=tests_insgesamt, inline=True)
        embed.add_field(name="All Vaccinations: ", value=impf_gesamt, inline=True)
        embed.set_thumbnail(url=corona_img)
        await ctx.send(embed=embed)
        command = command + "numbers de"

    elif len(args) == 2 and args[0] == "numbers" and args[1] in dic:
        bundesland = dic.get(args[1])
        req = requests.get("https://www.corona-in-zahlen.de/bundeslaender/" + bundesland)
        html_data = req.text
        parsed = BeautifulSoup(html_data, "html.parser")
        numbers_a = parsed.find_all("p", "card-title")
        einwohner = parse_corona(str(numbers_a[0]))
        infektionen = parse_corona(str(numbers_a[1]))
        infektionsrate = parse_corona(str(numbers_a[2]))
        neuinfektionen_s_days = parse_corona(str(numbers_a[3]))
        deaths = parse_corona(str(numbers_a[4]))
        tödlichkeit = parse_corona(str(numbers_a[5]))
        impfungen = parse_corona(str(numbers_a[7]))

        embed = discord.Embed(title="Corona Numbers Germany " + bundesland.capitalize(), color=discord.Color.red())
        embed.add_field(name="Population:", value=einwohner, inline=True)
        embed.add_field(name="Infections:", value=infektionen, inline=True)
        embed.add_field(name="Infection Rate: ", value=infektionsrate, inline=True)
        embed.add_field(name="New Infection per 100.000 people / 7 days: ", value=neuinfektionen_s_days, inline=True)
        embed.add_field(name="Deaths: ", value=deaths, inline=True)
        embed.add_field(name="Lethality: ", value=tödlichkeit, inline=True)
        embed.add_field(name="Vaccinations: ", value=impfungen, inline=True)
        embed.set_thumbnail(url=corona_img)
        await ctx.send(embed=embed)
        command = command + "numbers " + str(args[1])
    else:
        await ctx.send("Usage: !corona <numbers> <de, de/srl, de/thr> for showing the current cases and deaths")

    log(username, command)


def log(username,command):
    global log_path
    file = open(log_path,"a")
    time_now = str(datetime.datetime.now()).split(".")[0]
    out = "[" + time_now + "] " + username + ": " + command + "\n"
    file.write(out)


@bot.event
async def on_ready():
    print("Hello. I am your bot and I am ready to operate!")
    weather_update.start()

bot.run(TOKEN)
