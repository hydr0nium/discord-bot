import requests
from bs4 import BeautifulSoup
import discord
from discord.ext import commands, tasks
from timezonefinder import TimezoneFinder
import pytz
import datetime
import time
import random

file = open("../token.txt", "r")  # Opens a file for the token to be read
TOKEN = str(file.read())  # Reads out the token from the token file for later use
language = "en"  # Default language for the weather module
location = "Deutschland"  # Default location for the weather module
bot = commands.Bot(command_prefix="!")  # Setting the command prefix for the discord bot
log_path = "../log.txt"  # Setting the path for the log file which logs all commands being used when and from whom
last_update = ""  # String when the last update of the corona bot was made
vaccinations = 0  # Number of Vaccinations made
DEBUG = 0  # Debug Value if set it deactivates some functions


# --------------------------------------------------------------------------------------------

# Converting latitude and longitude to local time of that area
def get_time_from_location(lat, lon):
    tf = TimezoneFinder()
    ret = tf.timezone_at(lng=float(lon), lat=float(lat))
    tz = pytz.timezone(ret)
    normal = datetime.datetime.utcfromtimestamp(time.time())
    offset = tz.utcoffset(normal, is_dst=True)
    loc_time = datetime.datetime.utcnow() + offset
    loc_time = str(loc_time).split(" ")[1].split(".")[0]
    return loc_time


# Getting an image for the bot to display for the current weather
def get_weather_img(info_uncut):
    info = info_uncut.split("C ")[1].split("\n")[0]
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

    else:  # Some fun default case where it picks a random university image around the world
        ran = random.randint(1, 5000)
        print(ran)
        return "https://www.univerzities.com/Images/Uni/logo" + str(ran) + ".jpg"


# Just some parser magic for the <span class="class_name">out</span> tag
def parse_weather_html(array, class_name):
    if len(array) == 0:  # If an empty string is parsed then this base case is used
        return "0.0"
    cut1 = str(array[0])[(13 + len(class_name) + 2)::]  # cut the first part with the class_name
    flipped = cut1[::-1]  # flip all
    cut2 = flipped[8::]  # cut the </span> at the end
    out = cut2[::-1]  # flip back
    return out  # return cutted string


# Weather function to return the weather in either english or german for a place that is parsed to the function
def weather_func(place, lang):
    global DEBUG  # Debug value for deactivating the weather function
    out = ""
    # START Generate lat,long from place
    # Some replacing for security purposes
    place = place.replace("/", "").replace(":", "").replace("@", "").replace(".", "")
    # Request to website which converts place to lat / long
    rep2 = requests.get("http://www.geonames.org/search.html?q=" + place)
    html2 = rep2.text  # Convert reply to text string
    parsed2 = BeautifulSoup(html2, "html.parser")  # Some HTML parsing magic
    lat_a = parsed2.find_all("span", "latitude")  # Some HTML parsing magic
    lon_a = parsed2.find_all("span", "longitude")  # Some HTML parsing magic
    # END Generate lat,long from place

    lat = parse_weather_html(lat_a, "latitude")  # remove span tag
    lon = parse_weather_html(lon_a, "longitude")  # remove span tag
    coords = str(lat) + "," + str(lon)  # Convert to the right format for the url to use it
    time_loc = get_time_from_location(lat, lon)  # Get the local time for latitude and longitude
    # Generate Weather from place
    address = "https://darksky.net/forecast/"  # URL to convert between lat / long to weather
    if DEBUG == 1:
        return ""
    rep = requests.get(address + coords + "/ca24/" + lang)  # Actual request to url
    html = rep.text  # Some HTML parsing magic
    parsed = BeautifulSoup(html, "html.parser")  # Some HTML parsing magic
    weather_p = parsed.find_all("span", "summary swap")  # Some HTML parsing magic
    out = out + parse_weather_html(weather_p, "summary swap")  # remove span tag
    out = out.replace("\xa0", "C ")  # Some weird html artifact used on the webpage, I just remove it here
    out = out + "\n" + time_loc  # Some formating
    if (len(lat_a) or len(lon_a)) == 0:  # If a location is supplied that was not found then this error is returned
        out = "ERROR"
    return out


# ------------------------------------------------------------------------------------------------------------

# Update the weather in the status of the bot every 30 minutes
@tasks.loop(minutes=30)
async def weather_update():
    global location
    global language
    if DEBUG != 0:
        # Used default / or last set location and language as parameters to get the weather
        weather_status = weather_func(location, language)
        weather_status = weather_status[:32:]  # Status is limited to 32 chars
        weather_status = weather_status.split("\n")[0]  # We don't need to local time
        await bot.change_presence(
            activity=discord.Game(str(location).capitalize() + ": " + weather_status))  # Update status on bot


# The actual weather command that is used with the bot
@bot.command(pass_context=True, brief="Prints some weather data for some given parameters")
async def weather(ctx, *args):
    global language
    global location
    username = ctx.author.name # Get the username of the user who ran the command
    command = "!weather "
    usage = "Usage: !weather <location> <en/de> \nLanguage is optional\n" \
            "Returns the weather for the location in the choosen language"

    if len(args) == 2:  # If command is of the form !weather <location> <en/de>
        arg1 = args[0]  # Parse first argument of command
        arg2 = args[1]  # Parse second argument of command
        command = command + arg1 + " " + arg2
        ret = weather_func(str(arg1), str(arg2))  # Call the weather function on the arguments

        if DEBUG == 1: # Deactivate weather function if debug value is set
            await ctx.send("The weather function is currently unavailable")
            return

        elif ret != "ERROR": # If no error occurred use this
            if arg2 == "en" or arg2 == "de": # Check if a correct language was set
                if arg2 == "en": # Set all language related stuff
                    language = "en"
                    title = "Weather in "
                    temp = "Temperature"
                    tim = "Local Time"
                    command = command + arg1 + " en"

                elif arg2 == "de": # Set all language related stuff
                    language = "de"
                    title = "Wetter in "
                    temp = "Temperatur"
                    tim = "Lokale Uhrzeit"
                    command = command + arg1 + " de"

                location = str(arg1).capitalize() # Capitalize location
                title = title + location # Format title with location
                img = get_weather_img(ret) # Get the image for the location
                time_loc = ret.split("\n")[1] # Split return string to get local time
                weather_out = ret.split("\n")[0] # Split return string to get weather
                # Change bot status to the current weather
                await bot.change_presence(activity=discord.Game(str(arg1).capitalize() + ": " + weather_out))

                # Prepare and output embed with weather data
                embed = discord.Embed(title=title, color=discord.Color.green())
                embed.set_thumbnail(url=img)
                embed.add_field(name=temp, value=weather_out, inline=True)
                embed.add_field(name=tim, value=time_loc, inline=True)
                await ctx.send(embed=embed)
            else: # If no proper language was set use this
                await ctx.send("Please use a valid language option! For help see !weather")

        else: # If an error occurred use this
            await ctx.send("Please use a valid language option! For help see !weather")

    elif len(args) == 1:  # If command is of the form !weather <location>
        arg1 = args[0]
        command = command + arg1
        ret = weather_func(str(arg1), language)
        if ret != "ERROR":  # If no error occurred use this path
            if language == "en":  # the language was set to english
                # Setting some value in english
                title = "Weather in "
                temp = "Temperature"
                tim = "Local Time"

            if language == "de":  # the language was set to german
                # Setting some value in german
                title = "Wetter in "
                temp = "Temperatur"
                tim = "Lokale Uhrzeit"

            location = str(arg1).capitalize()  # Capitalize location name
            title = title + location  # Add location to the title
            img = get_weather_img(ret)  # Retrieve image for the weather with the return value
            time_loc = ret.split("\n")[1]  # Split the return string to get time string
            weather_out = ret.split("\n")[0]  # Split the return string to get weather string
            # Update the status of the bot
            await bot.change_presence(activity=discord.Game(str(arg1).capitalize() + ": " + weather_out))
            # Prepare and output embed to chat
            embed = discord.Embed(title=title, color=discord.Color.green())
            embed.set_thumbnail(url=img)
            embed.add_field(name=temp, value=weather_out, inline=True)
            embed.add_field(name=tim, value=time_loc, inline=True)
            await ctx.send(embed=embed)

        else:  # Something went wrong in the weather func
            await ctx.send("Please use a valid language option! For help see !weather")

    else:
        await ctx.send(usage)

    log(username, command) #Log user supplied command and username


# ---------------------------------------------------------------------------------------------
# Some parsing magic for the html tag <p class="card-title" style="font-size:30px"><b>string</b></p> --> string
def parse_corona_html(string):
    string = string[48::]
    string = string[::-1]
    string = string[8::]
    string = string[::-1]
    return string


def get_imf_deutsch():
    global vaccinations
    global last_update
    print("The last update was made: " + last_update)
    print("The current date is: " + str(datetime.date.today()))
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
            impfungen = parse_corona_html(str(numbers_a[7]))
            impfungen = impfungen.replace(".", "")
            ret = ret + int(impfungen)
        last_update = str(datetime.date.today())

        ret = str(ret)
        print(ret)

        # GARBAGE ALERT WTF IS THIS ?!
        ret = ret[::-1]
        out = ""
        for i in range(0, len(ret) - 3, 3):
            out = out + ret[i:i + 3] + "."
        if not (len(ret) // 3 == 0):
            out = out + ret[len(ret) - (len(ret) // 3) + 1:len(ret)]
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
           "de/sa": "sachsen", "de/he": "hessen", "de/ber": "berlin", "de/bay": "bayern",
           "de/meckpom": "mecklenburg-vorpommern",
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
        einwohner = parse_corona_html(str(numbers_a[0]))
        infektionen = parse_corona_html(str(numbers_a[1]))
        infektionsrate = parse_corona_html(str(numbers_a[2]))
        neuinfektionen_s_days = parse_corona_html(str(numbers_a[3]))
        deaths = parse_corona_html(str(numbers_a[4]))
        tödlichkeit = parse_corona_html(str(numbers_a[5]))
        neuinfektionen = parse_corona_html(str(numbers_a[6]))
        new_deaths = parse_corona_html(str(numbers_a[8]))
        tests_insgesamt = parse_corona_html(str(numbers_a[9]))
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
        einwohner = parse_corona_html(str(numbers_a[0]))
        infektionen = parse_corona_html(str(numbers_a[1]))
        infektionsrate = parse_corona_html(str(numbers_a[2]))
        neuinfektionen_s_days = parse_corona_html(str(numbers_a[3]))
        deaths = parse_corona_html(str(numbers_a[4]))
        tödlichkeit = parse_corona_html(str(numbers_a[5]))
        impfungen = parse_corona_html(str(numbers_a[7]))

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


def log(username, command):
    global log_path
    file = open(log_path, "a")
    time_now = str(datetime.datetime.now()).split(".")[0]
    out = "[" + time_now + "] " + username + ": " + command + "\n"
    file.write(out)


@bot.event
async def on_ready():
    print("Hello. I am your bot and I am ready to operate!")
    weather_update.start()


bot.run(TOKEN)
