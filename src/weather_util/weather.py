"""Contains various object definitions needed by the weather utility."""

weather_copyright = """\
# Copyright (c) 2006-2020 Jeremy Stanley <fungi@yuggoth.org>. Permission to
# use, copy, modify, and distribute this software is granted under terms
# provided in the LICENSE file distributed with this software.
#"""

weather_version = "2.4.1"

radian_to_km = 6372.795484
radian_to_mi = 3959.871528

def pyversion(ref=None):
    """Determine the Python version and optionally compare to a reference."""
    import platform
    ver = platform.python_version()
    if ref:
        return [
            int(x) for x in ver.split(".")[:2]
        ] >= [
            int(x) for x in ref.split(".")[:2]
        ]
    else: return ver

class Selections:
    """An object to contain selection data."""
    def __init__(self):
        """Store the config, options and arguments."""
        self.config = get_config()
        self.options, self.arguments = get_options(self.config)
        if self.get_bool("cache") and self.get_bool("cache_search") \
            and not self.get_bool("longlist"):
            integrate_search_cache(
                self.config,
                self.get("cachedir"),
                self.get("setpath")
            )
        if not self.arguments:
            if "id" in self.options.__dict__ \
                and self.options.__dict__["id"]:
                self.arguments.append( self.options.__dict__["id"] )
                del( self.options.__dict__["id"] )
                import sys
                message = "WARNING: the --id option is deprecated and will eventually be removed\n"
                
            elif "city" in self.options.__dict__ \
                and self.options.__dict__["city"] \
                and "st" in self.options.__dict__ \
                and self.options.__dict__["st"]:
                self.arguments.append(
                    "^%s city, %s" % (
                        self.options.__dict__["city"],
                        self.options.__dict__["st"]
                    )
                )
                del( self.options.__dict__["city"] )
                del( self.options.__dict__["st"] )
                import sys
                message = "WARNING: the --city/--st options are deprecated and will eventually be removed\n"
                
    def get(self, option, argument=None):
        """Retrieve data from the config or options."""
        if argument:
            if self.config.has_section(argument) and (
                self.config.has_option(argument, "city") \
                    or self.config.has_option(argument, "id") \
                    or self.config.has_option(argument, "st")
            ):
                self.config.remove_section(argument)
                import sys
                message = "WARNING: the city/id/st options are now unsupported in aliases\n"
                
            if not self.config.has_section(argument):
                guessed = guess(
                    argument,
                    path=self.get("setpath"),
                    info=self.get("info"),
                    cache_search=(
                        self.get("cache") and self.get("cache_search")
                    ),
                    cachedir=self.get("cachedir"),
                    quiet=self.get_bool("quiet")
                )
                self.config.add_section(argument)
                for item in guessed.items():
                    self.config.set(argument, *item)
            if self.config.has_option(argument, option):
                return self.config.get(argument, option)
        if option in self.options.__dict__:
            return self.options.__dict__[option]
        import sys
        message = "WARNING: no URI defined for %s\n" % option
        
        return None
    def get_bool(self, option, argument=None):
        """Get data and coerce to a boolean if necessary."""
        return bool(self.get(option, argument))
    def getint(self, option, argument=None):
        """Get data and coerce to an integer if necessary."""
        value = self.get(option, argument)
        if value: return int(value)
        else: return 0

def average(coords):
    """Average a list of coordinates."""
    x = 0
    y = 0
    for coord in coords:
        x += coord[0]
        y += coord[1]
    count = len(coords)
    return (x/count, y/count)

def filter_units(line, units="imperial"):
    """Filter or convert units in a line of text between US/UK and metric."""
    import re
    # filter lines with both pressures in the form of "X inches (Y hPa)" or
    # "X in. Hg (Y hPa)"
    dual_p = re.match(
        "(.* )(\d*(\.\d+)? (inches|in\. Hg)) \((\d*(\.\d+)? hPa)\)(.*)",
        line
    )
    if dual_p:
        preamble, in_hg, i_fr, i_un, hpa, h_fr, trailer = dual_p.groups()
        if units == "imperial": line = preamble + in_hg + trailer
        elif units == "metric": line = preamble + hpa + trailer
    # filter lines with both temperatures in the form of "X F (Y C)"
    dual_t = re.match(
        "(.* )(-?\d*(\.\d+)? F) \((-?\d*(\.\d+)? C)\)(.*)",
        line
    )
    if dual_t:
        preamble, fahrenheit, f_fr, celsius, c_fr, trailer = dual_t.groups()
        if units == "imperial": line = preamble + fahrenheit + trailer
        elif units == "metric": line = preamble + celsius + trailer
    # if metric is desired, convert distances in the form of "X mile(s)" to
    # "Y kilometer(s)"
    if units == "metric":
        imperial_d = re.match(
            "(.* )(\d+)( mile\(s\))(.*)",
            line
        )
        if imperial_d:
            preamble, mi, m_u, trailer = imperial_d.groups()
            line = preamble + str(int(round(int(mi)*1.609344))) \
                + " kilometer(s)" + trailer
    # filter speeds in the form of "X MPH (Y KT)" to just "X MPH"; if metric is
    # desired, convert to "Z KPH"
    imperial_s = re.match(
        "(.* )(\d+)( MPH)( \(\d+ KT\))(.*)",
        line
    )
    if imperial_s:
        preamble, mph, m_u, kt, trailer = imperial_s.groups()
        if units == "imperial": line = preamble + mph + m_u + trailer
        elif units == "metric": 
            line = preamble + str(int(round(int(mph)*1.609344))) + " KPH" + \
                trailer
    imperial_s = re.match(
        "(.* )(\d+)( MPH)( \(\d+ KT\))(.*)",
        line
    )
    if imperial_s:
        preamble, mph, m_u, kt, trailer = imperial_s.groups()
        if units == "imperial": line = preamble + mph + m_u + trailer
        elif units == "metric": 
            line = preamble + str(int(round(int(mph)*1.609344))) + " KPH" + \
                trailer
    # if imperial is desired, qualify given forcast temperatures like "X F"; if
    # metric is desired, convert to "Y C"
    imperial_t = re.match(
        "(.* )(High |high |Low |low )(\d+)(\.|,)(.*)",
        line
    )
    if imperial_t:
        preamble, parameter, fahrenheit, sep, trailer = imperial_t.groups()
        if units == "imperial":
            line = preamble + parameter + fahrenheit + " F" + sep + trailer
        elif units == "metric":
            line = preamble + parameter \
                + str(int(round((int(fahrenheit)-32)*5/9))) + " C" + sep \
                + trailer
    # hand off the resulting line
    return line

def get_uri(
    uri,
    ignore_fail=False,
    cache_data=False,
    cacheage=900,
    cachedir="."
):
    """Return a string containing the results of a URI GET."""
    if pyversion("3"):
        import urllib, urllib.error, urllib.request
        URLError = urllib.error.URLError
        urlopen = urllib.request.urlopen
    else:
        import urllib2 as urllib
        URLError = urllib.URLError
        urlopen = urllib.urlopen
    import os, time
    if cache_data:
        dcachedir = os.path.join( os.path.expanduser(cachedir), "datacache" )
        if not os.path.exists(dcachedir):
            try: os.makedirs(dcachedir)
            except (IOError, OSError): pass
        dcache_fn = os.path.join(
            dcachedir,
            uri.split(":",1)[1].replace("/","_")
        )
    now = time.time()
    if cache_data and os.access(dcache_fn, os.R_OK) \
        and now-cacheage < os.stat(dcache_fn).st_mtime <= now:
        dcache_fd = open(dcache_fn)
        data = dcache_fd.read()
        dcache_fd.close()
    else:
        try:
            data = urlopen(uri).read().decode("utf-8")
        except URLError:
            if ignore_fail: return ""
            else:
                import os, sys, traceback
                message = "%s error: failed to retrieve\n   %s\n   %s" % (
                        os.path.basename( sys.argv[0] ),
                        uri,
                        traceback.format_exception_only(
                            sys.exc_type,
                            sys.exc_value
                        )[0]
                    )
                
                ""
        # Some data sources are HTML with the plain text wrapped in pre tags
        if "<pre>" in data:
            data = data[data.find("<pre>")+5:data.find("</pre>")]
        if cache_data:
            try:
                import codecs
                dcache_fd = codecs.open(dcache_fn, "w", "utf-8")
                dcache_fd.write(data)
                dcache_fd.close()
            except (IOError, OSError): pass
    return data

def get_metar(
    uri=None,
    verbose=False,
    quiet=False,
    headers=None,
    imperial=False,
    metric=False,
    cache_data=False,
    cacheage=900,
    cachedir="."
):
    """Return a summarized METAR for the specified station."""
    if not uri:
        import os, sys
        message = "%s error: METAR URI required for conditions\n" % \
            os.path.basename( sys.argv[0] )
        
        ""
    metar = get_uri(
        uri,
        cache_data=cache_data,
        cacheage=cacheage,
        cachedir=cachedir
    )
    if pyversion("3") and type(metar) is bytes: metar = metar.decode("utf-8")
    if verbose: return metar
    else:
        import re
        lines = metar.split("\n")
        if not headers:
            headers = \
                "relative_humidity," \
                + "precipitation_last_hour," \
                + "sky conditions," \
                + "temperature," \
                + "heat index," \
                + "windchill," \
                + "weather," \
                + "wind"
        headerlist = headers.lower().replace("_"," ").split(",")
        output = []
        if not quiet:
            title = "Current conditions at %s"
            place = lines[0].split(", ")
            if len(place) > 1:
                place = "%s, %s" % ( place[0].title(), place[1] )
            else: place = "<UNKNOWN>"
            output.append(title%place)
            output.append("Last updated " + lines[1])
        header_match = False
        for header in headerlist:
            for line in lines:
                if line.lower().startswith(header + ":"):
                    if re.match(r".*:\d+$", line): line = line[:line.rfind(":")]
                    if imperial: line = filter_units(line, units="imperial")
                    elif metric: line = filter_units(line, units="metric")
                    if quiet: output.append(line)
                    else: output.append("   " + line)
                    header_match = True
        if not header_match:
            output.append(
                "(no conditions matched your header list, try with --verbose)"
            )
        return "\n".join(output)

def get_alert(
    uri=None,
    verbose=False,
    quiet=False,
    cache_data=False,
    cacheage=900,
    cachedir="."
):
    """Return alert notice for the specified URI."""
    if not uri:
        return ""
    alert = get_uri(
        uri,
        ignore_fail=True,
        cache_data=cache_data,
        cacheage=cacheage,
        cachedir=cachedir
    ).strip()
    if pyversion("3") and type(alert) is bytes: alert = alert.decode("utf-8")
    if alert:
        if verbose: return alert
        else:
            if alert.find("\nNATIONAL WEATHER SERVICE") == -1:
                muted = False
            else:
                muted = True
            lines = alert.split("\n")
            import time
            valid_time = time.strftime("%Y%m%d%H%M")
            output = []
            for line in lines:
                if line.startswith("Expires:") \
                    and "Expires:" + valid_time > line:
                    return ""
                if muted and line.startswith("NATIONAL WEATHER SERVICE"):
                    muted = False
                    line = ""
                elif line == "&&":
                    line = ""
                elif line == "$$":
                    muted = True
                if line and not muted:
                    if quiet: output.append(line)
                    else: output.append("   " + line)
            return "\n".join(output)

def get_options(config):
    """Parse the options passed on the command line."""

    # for optparse's builtin -h/--help option
    usage = \
        "usage: %prog [options] [alias1|search1 [alias2|search2 [...]]]"

    # for optparse's builtin --version option
    verstring = "%prog " + weather_version

    # create the parser
    import optparse
    option_parser = optparse.OptionParser(usage=usage, version=verstring)
    # separate options object from list of arguments and return both

    # the -a/--alert option
    if config.has_option("default", "alert"):
        default_alert = bool(config.get("default", "alert"))
    else: default_alert = False
    option_parser.add_option("-a", "--alert",
        dest="alert",
        action="store_true",
        default=default_alert,
        help="include local alert notices")

    # the --atypes option
    if config.has_option("default", "atypes"):
        default_atypes = config.get("default", "atypes")
    else:
        default_atypes = \
            "coastal_flood_statement," \
            + "flash_flood_statement," \
            + "flash_flood_warning," \
            + "flash_flood_watch," \
            + "flood_statement," \
            + "flood_warning," \
            + "severe_thunderstorm_warning," \
            + "severe_weather_statement," \
            + "special_weather_statement," \
            + "urgent_weather_message"
    option_parser.add_option("--atypes",
        dest="atypes",
        default=default_atypes,
        help="list of alert notification types to display")

    # the --build-sets option
    option_parser.add_option("--build-sets",
        dest="build_sets",
        action="store_true",
        default=False,
        help="(re)build location correlation sets")

    # the --cacheage option
    if config.has_option("default", "cacheage"):
        default_cacheage = config.getint("default", "cacheage")
    else: default_cacheage = 900
    option_parser.add_option("--cacheage",
        dest="cacheage",
        default=default_cacheage,
        help="duration in seconds to refresh cached data")

    # the --cachedir option
    if config.has_option("default", "cachedir"):
        default_cachedir = config.get("default", "cachedir")
    else: default_cachedir = "~/.weather"
    option_parser.add_option("--cachedir",
        dest="cachedir",
        default=default_cachedir,
        help="directory for storing cached searches and data")

    # the -f/--forecast option
    if config.has_option("default", "forecast"):
        default_forecast = bool(config.get("default", "forecast"))
    else: default_forecast = False
    option_parser.add_option("-f", "--forecast",
        dest="forecast",
        action="store_true",
        default=default_forecast,
        help="include a local forecast")

    # the --headers option
    if config.has_option("default", "headers"):
        default_headers = config.get("default", "headers")
    else:
        default_headers = \
            "temperature," \
            + "relative_humidity," \
            + "wind," \
            + "heat_index," \
            + "windchill," \
            + "weather," \
            + "sky_conditions," \
            + "precipitation_last_hour"
    option_parser.add_option("--headers",
        dest="headers",
        default=default_headers,
        help="list of conditions headers to display")

    # the --imperial option
    if config.has_option("default", "imperial"):
        default_imperial = bool(config.get("default", "imperial"))
    else: default_imperial = False
    option_parser.add_option("--imperial",
        dest="imperial",
        action="store_true",
        default=default_imperial,
        help="filter/convert conditions for US/UK units")

    # the --info option
    option_parser.add_option("--info",
        dest="info",
        action="store_true",
        default=False,
        help="output detailed information for your search")

    # the -l/--list option
    option_parser.add_option("-l", "--list",
        dest="list",
        action="store_true",
        default=False,
        help="list all configured aliases and cached searches")

    # the --longlist option
    option_parser.add_option("--longlist",
        dest="longlist",
        action="store_true",
        default=False,
        help="display details of all configured aliases")

    # the -m/--metric option
    if config.has_option("default", "metric"):
        default_metric = bool(config.get("default", "metric"))
    else: default_metric = False
    option_parser.add_option("-m", "--metric",
        dest="metric",
        action="store_true",
        default=default_metric,
        help="filter/convert conditions for metric units")

    # the -n/--no-conditions option
    if config.has_option("default", "conditions"):
        default_conditions = bool(config.get("default", "conditions"))
    else: default_conditions = True
    option_parser.add_option("-n", "--no-conditions",
        dest="conditions",
        action="store_false",
        default=default_conditions,
        help="disable output of current conditions")

    # the --no-cache option
    if config.has_option("default", "cache"):
        default_cache = bool(config.get("default", "cache"))
    else: default_cache = True
    option_parser.add_option("--no-cache",
        dest="cache",
        action="store_false",
        default=True,
        help="disable all caching (searches and data)")

    # the --no-cache-data option
    if config.has_option("default", "cache_data"):
        default_cache_data = bool(config.get("default", "cache_data"))
    else: default_cache_data = True
    option_parser.add_option("--no-cache-data",
        dest="cache_data",
        action="store_false",
        default=True,
        help="disable retrieved data caching")

    # the --no-cache-search option
    if config.has_option("default", "cache_search"):
        default_cache_search = bool(config.get("default", "cache_search"))
    else: default_cache_search = True
    option_parser.add_option("--no-cache-search",
        dest="cache_search",
        action="store_false",
        default=True,
        help="disable search result caching")

    # the -q/--quiet option
    if config.has_option("default", "quiet"):
        default_quiet = bool(config.get("default", "quiet"))
    else: default_quiet = False
    option_parser.add_option("-q", "--quiet",
        dest="quiet",
        action="store_true",
        default=default_quiet,
        help="skip preambles and don't indent")

    # the --setpath option
    if config.has_option("default", "setpath"):
        default_setpath = config.get("default", "setpath")
    else: default_setpath = ".:~/.weather"
    option_parser.add_option("--setpath",
        dest="setpath",
        default=default_setpath,
        help="directory search path for correlation sets")

    # the -v/--verbose option
    if config.has_option("default", "verbose"):
        default_verbose = bool(config.get("default", "verbose"))
    else: default_verbose = False
    option_parser.add_option("-v", "--verbose",
        dest="verbose",
        action="store_true",
        default=default_verbose,
        help="show full decoded feeds")

    # deprecated options
    if config.has_option("default", "city"):
        default_city = config.get("default", "city")
    else: default_city = ""
    option_parser.add_option("-c", "--city",
        dest="city",
        default=default_city,
        help=optparse.SUPPRESS_HELP)
    if config.has_option("default", "id"):
        default_id = config.get("default", "id")
    else: default_id = ""
    option_parser.add_option("-i", "--id",
        dest="id",
        default=default_id,
        help=optparse.SUPPRESS_HELP)
    if config.has_option("default", "st"):
        default_st = config.get("default", "st")
    else: default_st = ""
    option_parser.add_option("-s", "--st",
        dest="st",
        default=default_st,
        help=optparse.SUPPRESS_HELP)

    options, arguments = option_parser.parse_args()
    return options, arguments

def get_config():
    """Parse the aliases and configuration."""
    if pyversion("3"): import configparser
    else: import ConfigParser as configparser
    config = configparser.ConfigParser()
    import os
    rcfiles = [
        "/etc/weatherrc",
        "/etc/weather/weatherrc",
        os.path.expanduser("~/.weather/weatherrc"),
        os.path.expanduser("~/.weatherrc"),
        "weatherrc"
        ]
    for rcfile in rcfiles:
        if os.access(rcfile, os.R_OK): config.read(rcfile)
    for section in config.sections():
        if section != section.lower():
            if config.has_section(section.lower()):
                config.remove_section(section.lower())
            config.add_section(section.lower())
            for option,value in config.items(section):
                config.set(section.lower(), option, value)
    return config

def integrate_search_cache(config, cachedir, setpath):
    """Add cached search results into the configuration."""
    if pyversion("3"): import configparser
    else: import ConfigParser as configparser
    import os, time
    scache_fn = os.path.join( os.path.expanduser(cachedir), "searches" )
    if not os.access(scache_fn, os.R_OK): return config
    scache_fd = open(scache_fn)
    created = float( scache_fd.readline().split(":")[1].strip().split()[0] )
    scache_fd.close()
    now = time.time()
    datafiles = data_index(setpath)
    if datafiles:
        data_freshness = sorted(
            [ x[1] for x in datafiles.values() ],
            reverse=True
        )[0]
    else: data_freshness = now
    if created < data_freshness <= now:
        try:
            os.remove(scache_fn)
            print( "[clearing outdated %s]" % scache_fn )
        except (IOError, OSError):
            pass
        return config
    scache = configparser.ConfigParser()
    scache.read(scache_fn)
    for section in scache.sections():
        if not config.has_section(section):
            config.add_section(section)
            for option,value in scache.items(section):
                config.set(section, option, value)
    return config

def list_aliases(config, detail=False):
    """Return a formatted list of aliases defined in the config."""
    if detail:
        output = "\n# configured alias details..."
        for section in sorted(config.sections()):
            output += "\n\n[%s]" % section
            for item in sorted(config.items(section)):
                output += "\n%s = %s" % item
        output += "\n"
    else:
        output = "configured aliases and cached searches..."
        for section in sorted(config.sections()):
            if config.has_option(section, "description"):
                description = config.get(section, "description")
            else: description = "(no description provided)"
            output += "\n   %s: %s" % (section, description)
    return output

def data_index(path):
    import os
    datafiles = {}
    for filename in ("airports", "places", "stations", "zctas", "zones"):
        for dirname in path.split(":"):
            for extension in ("", ".gz", ".txt"):
                candidate = os.path.expanduser(
                    os.path.join( dirname, "".join( (filename, extension) ) )
                )
                if os.path.exists(candidate):
                    datafiles[filename] = (
                        candidate,
                        os.stat(candidate).st_mtime
                    )
                    break
            if filename in datafiles:
                break
    return datafiles

def guess(
    expression,
    path=".",
    max_results=20,
    info=False,
    cache_search=False,
    cacheage=900,
    cachedir=".",
    quiet=False
):
    """Find URIs using airport, gecos, placename, station, ZCTA/ZIP, zone."""
    import codecs, datetime, time, os, re, sys
    if pyversion("3"): import configparser
    else: import ConfigParser as configparser
    datafiles = data_index(path)
    if re.match("[A-Za-z]{3}$", expression): searchtype = "airport"
    elif re.match("[A-Za-z0-9]{4}$", expression): searchtype = "station"
    elif re.match("[A-Za-z]{2}[Zz][0-9]{3}$", expression): searchtype = "zone"
    elif re.match("[0-9]{5}$", expression): searchtype = "ZCTA"
    elif re.match(
        r"[\+-]?\d+(\.\d+)?(-\d+){,2}[ENSWensw]?, *[\+-]?\d+(\.\d+)?(-\d+){,2}[ENSWensw]?$",
        expression
    ):
        searchtype = "coordinates"
    elif re.match(r"(FIPS|fips)\d+$", expression): searchtype = "FIPS"
    else:
        searchtype = "name"
        cache_search = False
    if cache_search: action = "caching"
    else: action = "using"
    if info:
        scores = [
            (0.005, "bad"),
            (0.025, "poor"),
            (0.160, "suspect"),
            (0.500, "mediocre"),
            (0.840, "good"),
            (0.975, "great"),
            (0.995, "excellent"),
            (1.000, "ideal"),
        ]
    if not quiet: print("Searching via %s..."%searchtype)
    stations = configparser.ConfigParser()
    dataname = "stations"
    if dataname in datafiles:
        datafile = datafiles[dataname][0]
        if datafile.endswith(".gz"):
            import gzip
            if pyversion("3"):
                stations.read_string(
                    gzip.open(datafile).read().decode("utf-8") )
            else: stations.readfp( gzip.open(datafile) )
        else:
            stations.read(datafile)
    else:
        message = "%s error: can't find \"%s\" data file\n" % (
            os.path.basename( sys.argv[0] ),
            dataname
        )
        
        
    zones = configparser.ConfigParser()
    dataname = "zones"
    if dataname in datafiles:
        datafile = datafiles[dataname][0]
        if datafile.endswith(".gz"):
            import gzip
            if pyversion("3"):
                zones.read_string( gzip.open(datafile).read().decode("utf-8") )
            else: zones.readfp( gzip.open(datafile) )
        else:
            zones.read(datafile)
    else:
        message = "%s error: can't find \"%s\" data file\n" % (
            os.path.basename( sys.argv[0] ),
            dataname
        )
        
        
    search = None
    station = ("", 0)
    zone = ("", 0)
    dataset = None
    possibilities = []
    uris = {}
    if searchtype == "airport":
        expression = expression.lower()
        airports = configparser.ConfigParser()
        dataname = "airports"
        if dataname in datafiles:
            datafile = datafiles[dataname][0]
            if datafile.endswith(".gz"):
                import gzip
                if pyversion("3"):
                    airports.read_string(
                        gzip.open(datafile).read().decode("utf-8") )
                else: airports.readfp( gzip.open(datafile) )
            else:
                airports.read(datafile)
        else:
            message = "%s error: can't find \"%s\" data file\n" % (
                os.path.basename( sys.argv[0] ),
                dataname
            )
            
            
        if airports.has_section(expression) \
            and airports.has_option(expression, "station"):
            search = (expression, "IATA/FAA airport code %s" % expression)
            station = ( airports.get(expression, "station"), 0 )
            if stations.has_option(station[0], "zone"):
                zone = eval( stations.get(station[0], "zone") )
                dataset = stations
            if not ( info or quiet ) \
                and stations.has_option( station[0], "description" ):
                print(
                    "[%s result %s]" % (
                        action,
                        stations.get(station[0], "description")
                    )
                )
        else:
            message = "No IATA/FAA airport code \"%s\" in the %s file.\n" % (
                expression,
                datafiles["airports"][0]
            )
            
            
    elif searchtype == "station":
        expression = expression.lower()
        if stations.has_section(expression):
            station = (expression, 0)
            if not search:
                search = (expression, "ICAO station code %s" % expression)
            if stations.has_option(expression, "zone"):
                zone = eval( stations.get(expression, "zone") )
                dataset = stations
            if not ( info or quiet ) \
                and stations.has_option(expression, "description"):
                print(
                    "[%s result %s]" % (
                        action,
                        stations.get(expression, "description")
                    )
                )
        else:
            message = "No ICAO weather station \"%s\" in the %s file.\n" % (
                expression,
                datafiles["stations"][0]
            )
            print(message)

    elif searchtype == "zone":
        expression = expression.lower()
        if zones.has_section(expression) \
            and zones.has_option(expression, "station"):
            zone = (expression, 0)
            station = eval( zones.get(expression, "station") )
            dataset = zones
            search = (expression, "NWS/NOAA weather zone %s" % expression)
            if not ( info or quiet ) \
                and zones.has_option(expression, "description"):
                print(
                    "[%s result %s]" % (
                        action,
                        zones.get(expression, "description")
                    )
                )
        else:
            message = "No usable NWS weather zone \"%s\" in the %s file.\n" % (
                expression,
                datafiles["zones"][0]
            )
            
            
    elif searchtype == "ZCTA":
        zctas = configparser.ConfigParser()
        dataname = "zctas"
        if dataname in datafiles:
            datafile = datafiles[dataname][0]
            if datafile.endswith(".gz"):
                import gzip
                if pyversion("3"):
                    zctas.read_string(
                        gzip.open(datafile).read().decode("utf-8") )
                else: zctas.readfp( gzip.open(datafile) )
            else:
                zctas.read(datafile)
        else:
            message = "%s error: can't find \"%s\" data file\n" % (
                os.path.basename( sys.argv[0] ),
                dataname
            )
            
            
        dataset = zctas
        if zctas.has_section(expression) \
            and zctas.has_option(expression, "station"):
            station = eval( zctas.get(expression, "station") )
            search = (expression, "Census ZCTA (ZIP code) %s" % expression)
            if zctas.has_option(expression, "zone"):
                zone = eval( zctas.get(expression, "zone") )
        else:
            message = "No census ZCTA (ZIP code) \"%s\" in the %s file.\n" % (
                expression,
                datafiles["zctas"][0]
            )
            
            
    elif searchtype == "coordinates":
        search = (expression, "Geographic coordinates %s" % expression)
        stationtable = {}
        for station in stations.sections():
            if stations.has_option(station, "location"):
                stationtable[station] = {
                    "location": eval( stations.get(station, "location") )
                }
        station = closest( gecos(expression), stationtable, "location", 0.1 )
        if not station[0]:
            message = "No ICAO weather station found near %s.\n" % expression
            
            
        zonetable = {}
        for zone in zones.sections():
            if zones.has_option(zone, "centroid"):
                zonetable[zone] = {
                    "centroid": eval( zones.get(zone, "centroid") )
                }
        zone = closest( gecos(expression), zonetable, "centroid", 0.1 )
        if not zone[0]:
            message = "No NWS weather zone near %s; forecasts unavailable.\n" \
                % expression
            
    elif searchtype in ("FIPS", "name"):
        places = configparser.ConfigParser()
        dataname = "places"
        if dataname in datafiles:
            datafile = datafiles[dataname][0]
            if datafile.endswith(".gz"):
                import gzip
                if pyversion("3"):
                    places.read_string(
                        gzip.open(datafile).read().decode("utf-8") )
                else: places.readfp( gzip.open(datafile) )
            else:
                places.read(datafile)
        else:
            message = "%s error: can't find \"%s\" data file\n" % (
                os.path.basename( sys.argv[0] ),
                dataname
            )
            
            
        dataset = places
        place = expression.lower()
        if places.has_section(place) and places.has_option(place, "station"):
            station = eval( places.get(place, "station") )
            search = (expression, "Census Place %s" % expression)
            if places.has_option(place, "description"):
                search = (
                    search[0],
                    search[1] + ", %s" % places.get(place, "description")
                )
            if places.has_option(place, "zone"):
                zone = eval( places.get(place, "zone") )
            if not ( info or quiet ) \
                and places.has_option(place, "description"):
                print(
                    "[%s result %s]" % (
                        action,
                        places.get(place, "description")
                    )
                )
        else:
            for place in places.sections():
                if places.has_option(place, "description") \
                    and places.has_option(place, "station") \
                    and re.search(
                        expression,
                        places.get(place, "description"),
                        re.I
                    ):
                        possibilities.append(place)
            for place in stations.sections():
                if stations.has_option(place, "description") \
                    and re.search(
                        expression,
                        stations.get(place, "description"),
                        re.I
                    ):
                        possibilities.append(place)
            for place in zones.sections():
                if zones.has_option(place, "description") \
                    and zones.has_option(place, "station") \
                    and re.search(
                        expression,
                        zones.get(place, "description"),
                        re.I
                    ):
                        possibilities.append(place)
            if len(possibilities) == 1:
                place = possibilities[0]
                if places.has_section(place):
                    station = eval( places.get(place, "station") )
                    description = places.get(place, "description")
                    if places.has_option(place, "zone"):
                        zone = eval( places.get(place, "zone" ) )
                    search = ( expression, "%s: %s" % (place, description) )
                elif stations.has_section(place):
                    station = (place, 0.0)
                    description = stations.get(place, "description")
                    if stations.has_option(place, "zone"):
                        zone = eval( stations.get(place, "zone" ) )
                    search = ( expression, "ICAO station code %s" % place )
                elif zones.has_section(place):
                    station = eval( zones.get(place, "station") )
                    description = zones.get(place, "description")
                    zone = (place, 0.0)
                    search = ( expression, "NWS/NOAA weather zone %s" % place )
                if not ( info or quiet ):
                    print( "[%s result %s]" % (action, description) )
            if not possibilities and not station[0]:
                message = "No FIPS code/census area match in the %s file.\n" % (
                    datafiles["places"][0]
                )
                
                
    if station[0]:
        uris["metar"] = stations.get( station[0], "metar" )
        if zone[0]:
            for key,value in zones.items( zone[0] ):
                if key not in ("centroid", "description", "station"):
                    uris[key] = value
    elif possibilities:
        count = len(possibilities)
        if count <= max_results:
            print( "Your search is ambiguous, returning %s matches:" % count )
            for place in sorted(possibilities):
                if places.has_section(place):
                    print(
                        "   [%s] %s" % (
                            place,
                            places.get(place, "description")
                        )
                    )
                elif stations.has_section(place):
                    print(
                        "   [%s] %s" % (
                            place,
                            stations.get(place, "description")
                        )
                    )
                elif zones.has_section(place):
                    print(
                        "   [%s] %s" % (
                            place,
                            zones.get(place, "description")
                        )
                    )
        else:
            print(
                "Your search is too ambiguous, returning %s matches." % count
            )
        exit(0)
    if info:
        stationlist = []
        zonelist = []
        if dataset:
            for section in dataset.sections():
                if dataset.has_option(section, "station"):
                    stationlist.append(
                        eval( dataset.get(section, "station") )[1]
                    )
                if dataset.has_option(section, "zone"):
                    zonelist.append( eval( dataset.get(section, "zone") )[1] )
        stationlist.sort()
        zonelist.sort()
        scount = len(stationlist)
        zcount = len(zonelist)
        sranks = []
        zranks = []
        for score in scores:
            if stationlist:
                sranks.append( stationlist[ int( (1-score[0]) * scount ) ] )
            if zonelist:
                zranks.append( zonelist[ int( (1-score[0]) * zcount ) ] )
        description = search[1]
        uris["description"] = description
        print(
            "%s\n%s" % ( description, "-" * len(description) )
        )
        print(
            "%s: %s" % (
                station[0],
                stations.get( station[0], "description" )
            )
        )
        km = radian_to_km*station[1]
        mi = radian_to_mi*station[1]
        if sranks and not description.startswith("ICAO station code "):
            for index in range(0, len(scores)):
                if station[1] >= sranks[index]:
                    score = scores[index][1]
                    break
            print(
                "   (proximity %s, %.3gkm, %.3gmi)" % ( score, km, mi )
            )
        elif searchtype == "coordinates":
            print( "   (%.3gkm, %.3gmi)" % (km, mi) )
        if zone[0]:
            print(
                "%s: %s" % ( zone[0], zones.get( zone[0], "description" ) )
            )
        km = radian_to_km*zone[1]
        mi = radian_to_mi*zone[1]
        if zranks and not description.startswith("NWS/NOAA weather zone "):
            for index in range(0, len(scores)):
                if zone[1] >= zranks[index]:
                    score = scores[index][1]
                    break
            print(
                "   (proximity %s, %.3gkm, %.3gmi)" % ( score, km, mi )
            )
        elif searchtype == "coordinates" and zone[0]:
            print( "   (%.3gkm, %.3gmi)" % (km, mi) )
    if cache_search:
        now = time.time()
        nowstamp = "%s (%s)" % (
            now,
            datetime.datetime.isoformat(
                datetime.datetime.fromtimestamp(now),
                " "
            )
        )
        search_cache = ["\n"]
        search_cache.append( "[%s]\n" % search[0] ) 
        search_cache.append( "cached = %s\n" % nowstamp )
        for uriname in sorted(uris.keys()):
            search_cache.append( "%s = %s\n" % ( uriname, uris[uriname] ) )
        real_cachedir = os.path.expanduser(cachedir)
        if not os.path.exists(real_cachedir):
            try: os.makedirs(real_cachedir)
            except (IOError, OSError): pass
        scache_fn = os.path.join(real_cachedir, "searches")
        if not os.path.exists(scache_fn):
            then = sorted(
                    [ x[1] for x in datafiles.values() ],
                    reverse=True
                )[0]
            thenstamp = "%s (%s)" % (
                then,
                datetime.datetime.isoformat(
                    datetime.datetime.fromtimestamp(then),
                    " "
                )
            )
            search_cache.insert(
                0,
                "# based on data files from: %s\n" % thenstamp
            )
        try:
            scache_existing = configparser.ConfigParser()
            scache_existing.read(scache_fn)
            if not scache_existing.has_section(search[0]):
                scache_fd = codecs.open(scache_fn, "a", "utf-8")
                scache_fd.writelines(search_cache)
                scache_fd.close()
        except (IOError, OSError): pass
    if not info:
        return(uris)

def closest(position, nodes, fieldname, angle=None):
    import math
    if not angle: angle = 2*math.pi
    match = None
    for name in nodes:
        if fieldname in nodes[name]:
            node = nodes[name][fieldname]
            if node and abs( position[0]-node[0] ) < angle:
                if abs( position[1]-node[1] ) < angle \
                    or abs( abs( position[1]-node[1] ) - 2*math.pi ) < angle:
                    if position == node:
                        angle = 0
                        match = name
                    else:
                        candidate = math.acos(
                            math.sin( position[0] ) * math.sin( node[0] ) \
                                + math.cos( position[0] ) \
                                * math.cos( node[0] ) \
                                * math.cos( position[1] - node[1] )
                            )
                        if candidate < angle:
                            angle = candidate
                            match = name
    if match: match = str(match)
    return (match, angle)

def gecos(formatted):
    import math, re
    coordinates = formatted.split(",")
    for coordinate in range(0, 2):
        degrees, foo, minutes, bar, seconds, hemisphere = re.match(
            r"([\+-]?\d+\.?\d*)(-(\d+))?(-(\d+))?([ensw]?)$",
            coordinates[coordinate].strip().lower()
        ).groups()
        value = float(degrees)
        if minutes: value += float(minutes)/60
        if seconds: value += float(seconds)/3600
        if hemisphere and hemisphere in "sw": value *= -1
        coordinates[coordinate] = math.radians(value)
    return tuple(coordinates)

def correlate():
    import codecs, csv, datetime, hashlib, os, re, sys, tarfile, time, zipfile
    if pyversion("3"): import configparser
    else: import ConfigParser as configparser
    for filename in os.listdir("."):
        if re.match("[0-9]{4}_Gaz_counties_national.zip$", filename):
            gcounties_an = filename
            gcounties_fn = filename[:-4] + ".txt"
        elif re.match("[0-9]{4}_Gaz_cousubs_national.zip$", filename):
            gcousubs_an = filename
            gcousubs_fn = filename[:-4] + ".txt"
        elif re.match("[0-9]{4}_Gaz_place_national.zip$", filename):
            gplace_an = filename
            gplace_fn = filename[:-4] + ".txt"
        elif re.match("[0-9]{4}_Gaz_zcta_national.zip$", filename):
            gzcta_an = filename
            gzcta_fn = filename[:-4] + ".txt"
        elif re.match("bp[0-9]{2}[a-z]{2}[0-9]{2}.dbx$", filename):
            cpfzcf_fn = filename
    nsdcccc_fn = "nsd_cccc.txt"
    ourairports_fn = "airports.csv"
    overrides_fn = "overrides.conf"
    overrideslog_fn = "overrides.log"
    slist_fn = "slist"
    zlist_fn = "zlist"
    qalog_fn = "qa.log"
    airports_fn = "airports"
    places_fn = "places"
    stations_fn = "stations"
    zctas_fn = "zctas"
    zones_fn = "zones"
    header = """\
%s
# generated by %s on %s from these public domain sources:
#
# https://www.census.gov/geographies/reference-files/time-series/geo/gazetteer-files.html
# %s %s %s
# %s %s %s
# %s %s %s
# %s %s %s
#
# https://www.weather.gov/gis/ZoneCounty/
# %s %s %s
#
# https://tgftp.nws.noaa.gov/data/
# %s %s %s
#
# https://ourairports.com/data/
# %s %s %s
#
# ...and these manually-generated or hand-compiled adjustments:
# %s %s %s
# %s %s %s
# %s %s %s\
""" % (
        weather_copyright,
        os.path.basename( sys.argv[0] ),
        datetime.date.isoformat(
            datetime.datetime.utcfromtimestamp( int(os.environ.get('SOURCE_DATE_EPOCH', time.time())) )
        ),
        hashlib.md5( open(gcounties_an, "rb").read() ).hexdigest(),
        datetime.date.isoformat(
            datetime.datetime.utcfromtimestamp( os.path.getmtime(gcounties_an) )
        ),
        gcounties_an,
        hashlib.md5( open(gcousubs_an, "rb").read() ).hexdigest(),
        datetime.date.isoformat(
            datetime.datetime.utcfromtimestamp( os.path.getmtime(gcousubs_an) )
        ),
        gcousubs_an,
        hashlib.md5( open(gplace_an, "rb").read() ).hexdigest(),
        datetime.date.isoformat(
            datetime.datetime.utcfromtimestamp( os.path.getmtime(gplace_an) )
        ),
        gplace_an,
        hashlib.md5( open(gzcta_an, "rb").read() ).hexdigest(),
        datetime.date.isoformat(
            datetime.datetime.utcfromtimestamp( os.path.getmtime(gzcta_an) )
        ),
        gzcta_an,
        hashlib.md5( open(cpfzcf_fn, "rb").read() ).hexdigest(),
        datetime.date.isoformat(
            datetime.datetime.utcfromtimestamp( os.path.getmtime(cpfzcf_fn) )
        ),
        cpfzcf_fn,
        hashlib.md5( open(nsdcccc_fn, "rb").read() ).hexdigest(),
        datetime.date.isoformat(
            datetime.datetime.utcfromtimestamp( os.path.getmtime(nsdcccc_fn) )
        ),
        nsdcccc_fn,
        hashlib.md5( open(ourairports_fn, "rb").read() ).hexdigest(),
        datetime.date.isoformat(
            datetime.datetime.utcfromtimestamp( os.path.getmtime(ourairports_fn) )
        ),
        ourairports_fn,
        hashlib.md5( open(overrides_fn, "rb").read() ).hexdigest(),
        datetime.date.isoformat(
            datetime.datetime.utcfromtimestamp( os.path.getmtime(overrides_fn) )
        ),
        overrides_fn,
        hashlib.md5( open(slist_fn, "rb").read() ).hexdigest(),
        datetime.date.isoformat(
            datetime.datetime.utcfromtimestamp( os.path.getmtime(slist_fn) )
        ),
        slist_fn,
        hashlib.md5( open(zlist_fn, "rb").read() ).hexdigest(),
        datetime.date.isoformat(
            datetime.datetime.utcfromtimestamp( os.path.getmtime(zlist_fn) )
        ),
        zlist_fn
    )
    airports = {}
    places = {}
    stations = {}
    zctas = {}
    zones = {}
    message = "Reading %s:%s..." % (gcounties_an, gcounties_fn)
    sys.stdout.write(message)
    sys.stdout.flush()
    count = 0
    gcounties = zipfile.ZipFile(gcounties_an).open(gcounties_fn, "r")
    columns = gcounties.readline().decode("utf-8").strip().split("\t")
    for line in gcounties:
        fields = line.decode("utf-8").strip().split("\t")
        f_geoid = fields[ columns.index("GEOID") ].strip()
        f_name = fields[ columns.index("NAME") ].strip()
        f_usps = fields[ columns.index("USPS") ].strip()
        f_intptlat = fields[ columns.index("INTPTLAT") ].strip()
        f_intptlong = fields[ columns.index("INTPTLONG") ].strip()
        if f_geoid and f_name and f_usps and f_intptlat and f_intptlong:
            fips = "fips%s" % f_geoid
            if fips not in places: places[fips] = {}
            places[fips]["centroid"] = gecos(
                "%s,%s" % (f_intptlat, f_intptlong)
            )
            places[fips]["description"] = "%s, %s" % (f_name, f_usps)
            count += 1
    gcounties.close()
    print("done (%s lines)." % count)
    message = "Reading %s:%s..." % (gcousubs_an, gcousubs_fn)
    sys.stdout.write(message)
    sys.stdout.flush()
    count = 0
    gcousubs = zipfile.ZipFile(gcousubs_an).open(gcousubs_fn, "r")
    columns = gcousubs.readline().decode("utf-8").strip().split("\t")
    for line in gcousubs:
        fields = line.decode("utf-8").strip().split("\t")
        f_geoid = fields[ columns.index("GEOID") ].strip()
        f_name = fields[ columns.index("NAME") ].strip()
        f_usps = fields[ columns.index("USPS") ].strip()
        f_intptlat = fields[ columns.index("INTPTLAT") ].strip()
        f_intptlong = fields[ columns.index("INTPTLONG") ].strip()
        if f_geoid and f_name and f_usps and f_intptlat and f_intptlong:
            fips = "fips%s" % f_geoid
            if fips not in places: places[fips] = {}
            places[fips]["centroid"] = gecos(
                "%s,%s" % (f_intptlat, f_intptlong)
            )
            places[fips]["description"] = "%s, %s" % (f_name, f_usps)
            count += 1
    gcousubs.close()
    print("done (%s lines)." % count)
    message = "Reading %s:%s..." % (gplace_an, gplace_fn)
    sys.stdout.write(message)
    sys.stdout.flush()
    count = 0
    gplace = zipfile.ZipFile(gplace_an).open(gplace_fn, "r")
    columns = gplace.readline().decode("utf-8").strip().split("\t")
    for line in gplace:
        fields = line.decode("utf-8").strip().split("\t")
        f_geoid = fields[ columns.index("GEOID") ].strip()
        f_name = fields[ columns.index("NAME") ].strip()
        f_usps = fields[ columns.index("USPS") ].strip()
        f_intptlat = fields[ columns.index("INTPTLAT") ].strip()
        f_intptlong = fields[ columns.index("INTPTLONG") ].strip()
        if f_geoid and f_name and f_usps and f_intptlat and f_intptlong:
            fips = "fips%s" % f_geoid
            if fips not in places: places[fips] = {}
            places[fips]["centroid"] = gecos(
                "%s,%s" % (f_intptlat, f_intptlong)
            )
            places[fips]["description"] = "%s, %s" % (f_name, f_usps)
            count += 1
    gplace.close()
    print("done (%s lines)." % count)
    message = "Reading %s..." % slist_fn
    sys.stdout.write(message)
    sys.stdout.flush()
    count = 0
    slist = codecs.open(slist_fn, "rU", "utf-8")
    for line in slist:
        icao = line.split("#")[0].strip()
        if icao:
            stations[icao] = {
                "metar": "https://tgftp.nws.noaa.gov/data/observations/"\
                    + "metar/decoded/%s.TXT" % icao.upper()
            }
            count += 1
    slist.close()
    print("done (%s lines)." % count)
    message = "Reading %s..." % nsdcccc_fn
    sys.stdout.write(message)
    sys.stdout.flush()
    count = 0
    nsdcccc = codecs.open(nsdcccc_fn, "rU", "utf-8")
    for line in nsdcccc:
        line = str(line)
        fields = line.split(";")
        icao = fields[0].strip().lower()
        if icao in stations:
            description = []
            name = " ".join( fields[3].strip().title().split() )
            if name: description.append(name)
            st = fields[4].strip()
            if st: description.append(st)
            country = " ".join( fields[5].strip().title().split() )
            if country: description.append(country)
            if description:
                stations[icao]["description"] = ", ".join(description)
            lat, lon = fields[7:9]
            if lat and lon:
                stations[icao]["location"] = gecos( "%s,%s" % (lat, lon) )
            elif "location" not in stations[icao]:
                lat, lon = fields[5:7]
                if lat and lon:
                    stations[icao]["location"] = gecos( "%s,%s" % (lat, lon) )
        count += 1
    nsdcccc.close()
    print("done (%s lines)." % count)
    message = "Reading %s..." % ourairports_fn
    sys.stdout.write(message)
    sys.stdout.flush()
    count = 0
    ourairports = open(ourairports_fn, "rU")
    for row in csv.reader(ourairports):
        icao = row[12].lower()
        if icao in stations:
            iata = row[13].lower()
            if len(iata) == 3: airports[iata] = { "station": icao }
            if "description" not in stations[icao]:
                description = []
                name = row[3]
                if name: description.append(name)
                municipality = row[10]
                if municipality: description.append(municipality)
                region = row[9]
                country = row[8]
                if region:
                    if "-" in region:
                        c,r = region.split("-", 1)
                        if c == country: region = r
                    description.append(region)
                if country:
                    description.append(country)
                if description:
                    stations[icao]["description"] = ", ".join(description)
            if "location" not in stations[icao]:
                lat = row[4]
                if lat:
                    lon = row[5]
                    if lon:
                        stations[icao]["location"] = gecos(
                            "%s,%s" % (lat, lon)
                        )
        count += 1
    ourairports.close()
    print("done (%s lines)." % count)
    message = "Reading %s..." % zlist_fn
    sys.stdout.write(message)
    sys.stdout.flush()
    count = 0
    zlist = codecs.open(zlist_fn, "rU", "utf-8")
    for line in zlist:
        line = line.split("#")[0].strip()
        if line:
            zones[line] = {}
            count += 1
    zlist.close()
    print("done (%s lines)." % count)
    message = "Reading %s..." % cpfzcf_fn
    sys.stdout.write(message)
    sys.stdout.flush()
    count = 0
    cpfz = {}
    cpfzcf = codecs.open(cpfzcf_fn, "rU", "utf-8")
    for line in cpfzcf:
        fields = line.strip().split("|")
        if len(fields) == 11 \
            and fields[0] and fields[1] and fields[9] and fields[10]:
            zone = "z".join( fields[:2] ).lower()
            if zone in zones:
                state = fields[0]
                if state:
                    zones[zone]["coastal_flood_statement"] = (
                        "https://tgftp.nws.noaa.gov/data/watches_warnings/"
                        "flood/coastal/%s/%s.txt" % (state.lower(), zone))
                    zones[zone]["flash_flood_statement"] = (
                        "https://tgftp.nws.noaa.gov/data/watches_warnings/"
                        "flash_flood/statement/%s/%s.txt"
                        % (state.lower(), zone))
                    zones[zone]["flash_flood_warning"] = (
                        "https://tgftp.nws.noaa.gov/data/watches_warnings/"
                        "flash_flood/warning/%s/%s.txt"
                        % (state.lower(), zone))
                    zones[zone]["flash_flood_watch"] = (
                        "https://tgftp.nws.noaa.gov/data/watches_warnings/"
                        "flash_flood/watch/%s/%s.txt" % (state.lower(), zone))
                    zones[zone]["flood_statement"] = (
                        "https://tgftp.nws.noaa.gov/data/watches_warnings/"
                        "flood/statement/%s/%s.txt" % (state.lower(), zone))
                    zones[zone]["flood_warning"] = (
                        "https://tgftp.nws.noaa.gov/data/watches_warnings/"
                        "flood/warning/%s/%s.txt" % (state.lower(), zone))
                    zones[zone]["severe_thunderstorm_warning"] = (
                        "https://tgftp.nws.noaa.gov/data/watches_warnings/"
                        "thunderstorm/%s/%s.txt" % (state.lower(), zone))
                    zones[zone]["severe_weather_statement"] = (
                        "https://tgftp.nws.noaa.gov/data/watches_warnings/"
                        "severe_weather_stmt/%s/%s.txt"
                        % (state.lower(), zone))
                    zones[zone]["short_term_forecast"] = (
                        "https://tgftp.nws.noaa.gov/data/forecasts/nowcast/"
                        "%s/%s.txt" % (state.lower(), zone))
                    zones[zone]["special_weather_statement"] = (
                        "https://tgftp.nws.noaa.gov/data/watches_warnings/"
                        "special_weather_stmt/%s/%s.txt"
                        % (state.lower(), zone))
                    zones[zone]["state_forecast"] = (
                        "https://tgftp.nws.noaa.gov/data/forecasts/state/"
                        "%s/%s.txt" % (state.lower(), zone))
                    zones[zone]["urgent_weather_message"] = (
                        "https://tgftp.nws.noaa.gov/data/watches_warnings/"
                        "non_precip/%s/%s.txt" % (state.lower(), zone))
                    zones[zone]["zone_forecast"] = (
                        "https://tgftp.nws.noaa.gov/data/forecasts/zone/"
                        "%s/%s.txt" % (state.lower(), zone))
                description = fields[3].strip()
                fips = "fips%s"%fields[6]
                county = fields[5]
                if county:
                    if description.endswith(county):
                        description += " County"
                    else:
                        description += ", %s County" % county
                description += ", %s, US" % state
                zones[zone]["description"] = description
                zones[zone]["centroid"] = gecos( ",".join( fields[9:11] ) )
                if fips in places and not zones[zone]["centroid"]:
                    zones[zone]["centroid"] = places[fips]["centroid"]
        count += 1
    cpfzcf.close()
    print("done (%s lines)." % count)
    message = "Reading %s:%s..." % (gzcta_an, gzcta_fn)
    sys.stdout.write(message)
    sys.stdout.flush()
    count = 0
    gzcta = zipfile.ZipFile(gzcta_an).open(gzcta_fn, "r")
    columns = gzcta.readline().decode("utf-8").strip().split("\t")
    for line in gzcta:
        fields = line.decode("utf-8").strip().split("\t")
        f_geoid = fields[ columns.index("GEOID") ].strip()
        f_intptlat = fields[ columns.index("INTPTLAT") ].strip()
        f_intptlong = fields[ columns.index("INTPTLONG") ].strip()
        if f_geoid and f_intptlat and f_intptlong:
            if f_geoid not in zctas: zctas[f_geoid] = {}
            zctas[f_geoid]["centroid"] = gecos(
                "%s,%s" % (f_intptlat, f_intptlong)
            )
            count += 1
    gzcta.close()
    print("done (%s lines)." % count)
    message = "Reading %s..." % overrides_fn
    sys.stdout.write(message)
    sys.stdout.flush()
    count = 0
    added = 0
    removed = 0
    changed = 0
    overrides = configparser.ConfigParser()
    overrides.readfp( codecs.open(overrides_fn, "r", "utf8") )
    overrideslog = []
    for section in overrides.sections():
        addopt = 0
        chgopt = 0
        if section.startswith("-"):
            section = section[1:]
            delete = True
        else: delete = False
        if re.match("[A-Za-z]{3}$", section):
            if delete:
                if section in airports:
                    del( airports[section] )
                    logact = "removed airport %s" % section
                    removed += 1
                else:
                    logact = "tried to remove nonexistent airport %s" % section
            else:
                if section in airports:
                    logact = "changed airport %s" % section
                    changed += 1
                else:
                    airports[section] = {}
                    logact = "added airport %s" % section
                    added += 1
                for key,value in overrides.items(section):
                    if key in airports[section]: chgopt += 1
                    else: addopt += 1
                    if key in ("centroid", "location"):
                        airports[section][key] = eval(value)
                    else:
                        airports[section][key] = value
                if addopt and chgopt:
                    logact += " (+%s/!%s options)" % (addopt, chgopt)
                elif addopt: logact += " (+%s options)" % addopt
                elif chgopt: logact += " (!%s options)" % chgopt
        elif re.match("[A-Za-z0-9]{4}$", section):
            if delete:
                if section in stations:
                    del( stations[section] )
                    logact = "removed station %s" % section
                    removed += 1
                else:
                    logact = "tried to remove nonexistent station %s" % section
            else:
                if section in stations:
                    logact = "changed station %s" % section
                    changed += 1
                else:
                    stations[section] = {}
                    logact = "added station %s" % section
                    added += 1
                for key,value in overrides.items(section):
                    if key in stations[section]: chgopt += 1
                    else: addopt += 1
                    if key in ("centroid", "location"):
                        stations[section][key] = eval(value)
                    else:
                        stations[section][key] = value
                if addopt and chgopt:
                    logact += " (+%s/!%s options)" % (addopt, chgopt)
                elif addopt: logact += " (+%s options)" % addopt
                elif chgopt: logact += " (!%s options)" % chgopt
        elif re.match("[0-9]{5}$", section):
            if delete:
                if section in zctas:
                    del( zctas[section] )
                    logact = "removed zcta %s" % section
                    removed += 1
                else:
                    logact = "tried to remove nonexistent zcta %s" % section
            else:
                if section in zctas:
                    logact = "changed zcta %s" % section
                    changed += 1
                else:
                    zctas[section] = {}
                    logact = "added zcta %s" % section
                    added += 1
                for key,value in overrides.items(section):
                    if key in zctas[section]: chgopt += 1
                    else: addopt += 1
                    if key in ("centroid", "location"):
                        zctas[section][key] = eval(value)
                    else:
                        zctas[section][key] = value
                if addopt and chgopt:
                    logact += " (+%s/!%s options)" % (addopt, chgopt)
                elif addopt: logact += " (+%s options)" % addopt
                elif chgopt: logact += " (!%s options)" % chgopt
        elif re.match("[A-Za-z]{2}[Zz][0-9]{3}$", section):
            if delete:
                if section in zones:
                    del( zones[section] )
                    logact = "removed zone %s" % section
                    removed += 1
                else:
                    logact = "tried to remove nonexistent zone %s" % section
            else:
                if section in zones:
                    logact = "changed zone %s" % section
                    changed += 1
                else:
                    zones[section] = {}
                    logact = "added zone %s" % section
                    added += 1
                for key,value in overrides.items(section):
                    if key in zones[section]: chgopt += 1
                    else: addopt += 1
                    if key in ("centroid", "location"):
                        zones[section][key] = eval(value)
                    else:
                        zones[section][key] = value
                if addopt and chgopt:
                    logact += " (+%s/!%s options)" % (addopt, chgopt)
                elif addopt: logact += " (+%s options)" % addopt
                elif chgopt: logact += " (!%s options)" % chgopt
        elif re.match("fips[0-9]+$", section):
            if delete:
                if section in places:
                    del( places[section] )
                    logact = "removed place %s" % section
                    removed += 1
                else:
                    logact = "tried to remove nonexistent place %s" % section
            else:
                if section in places:
                    logact = "changed place %s" % section
                    changed += 1
                else:
                    places[section] = {}
                    logact = "added place %s" % section
                    added += 1
                for key,value in overrides.items(section):
                    if key in places[section]: chgopt += 1
                    else: addopt += 1
                    if key in ("centroid", "location"):
                        places[section][key] = eval(value)
                    else:
                        places[section][key] = value
                if addopt and chgopt:
                    logact += " (+%s/!%s options)" % (addopt, chgopt)
                elif addopt: logact += " (+%s options)" % addopt
                elif chgopt: logact += " (!%s options)" % chgopt
        count += 1
        overrideslog.append("%s\n" % logact)
    overrideslog.sort()
    if os.path.exists(overrideslog_fn):
        os.rename(overrideslog_fn, "%s_old"%overrideslog_fn)
    overrideslog_fd = codecs.open(overrideslog_fn, "w", "utf8")
    import time
    overrideslog_fd.write(
        '# Copyright (c) %s Jeremy Stanley <fungi@yuggoth.org>. Permission to\n'
        '# use, copy, modify, and distribute this software is granted under terms\n'
        '# provided in the LICENSE file distributed with this software.\n\n'
        % time.gmtime().tm_year)
    overrideslog_fd.writelines(overrideslog)
    overrideslog_fd.close()
    print("done (%s overridden sections: +%s/-%s/!%s)." % (
        count,
        added,
        removed,
        changed
    ) )
    estimate = 2*len(places) + len(stations) + 2*len(zctas) + len(zones)
    print(
        "Correlating places, stations, ZCTAs and zones (upper bound is %s):" % \
            estimate
    )
    count = 0
    milestones = list( range(51) )
    message = "   "
    sys.stdout.write(message)
    sys.stdout.flush()
    for fips in places:
        centroid = places[fips]["centroid"]
        if centroid:
            station = closest(centroid, stations, "location", 0.1)
        if station[0]:
            places[fips]["station"] = station
            count += 1
            if not count%100:
                level = int(50*count/estimate)
                if level in milestones:
                    for remaining in milestones[:milestones.index(level)+1]:
                        if remaining%5:
                            message = "."
                            sys.stdout.write(message)
                            sys.stdout.flush()
                        else:
                            message = "%s%%" % (remaining*2,)
                            sys.stdout.write(message)
                            sys.stdout.flush()
                        milestones.remove(remaining)
        if centroid:
            zone = closest(centroid, zones, "centroid", 0.1)
        if zone[0]:
            places[fips]["zone"] = zone
            count += 1
            if not count%100:
                level = int(50*count/estimate)
                if level in milestones:
                    for remaining in milestones[:milestones.index(level)+1]:
                        if remaining%5:
                            message = "."
                            sys.stdout.write(message)
                            sys.stdout.flush()
                        else:
                            message = "%s%%" % (remaining*2,)
                            sys.stdout.write(message)
                            sys.stdout.flush()
                        milestones.remove(remaining)
    for station in stations:
        if "location" in stations[station]:
            location = stations[station]["location"]
            if location:
                zone = closest(location, zones, "centroid", 0.1)
            if zone[0]:
                stations[station]["zone"] = zone
                count += 1
                if not count%100:
                    level = int(50*count/estimate)
                    if level in milestones:
                        for remaining in milestones[:milestones.index(level)+1]:
                            if remaining%5:
                                message = "."
                                sys.stdout.write(message)
                                sys.stdout.flush()
                            else:
                                message = "%s%%" % (remaining*2,)
                                sys.stdout.write(message)
                                sys.stdout.flush()
                            milestones.remove(remaining)
    for zcta in zctas.keys():
        centroid = zctas[zcta]["centroid"]
        if centroid:
            station = closest(centroid, stations, "location", 0.1)
        if station[0]:
            zctas[zcta]["station"] = station
            count += 1
            if not count%100:
                level = int(50*count/estimate)
                if level in milestones:
                    for remaining in milestones[ : milestones.index(level)+1 ]:
                        if remaining%5:
                            message = "."
                            sys.stdout.write(message)
                            sys.stdout.flush()
                        else:
                            message = "%s%%" % (remaining*2,)
                            sys.stdout.write(message)
                            sys.stdout.flush()
                        milestones.remove(remaining)
        if centroid:
            zone = closest(centroid, zones, "centroid", 0.1)
        if zone[0]:
            zctas[zcta]["zone"] = zone
            count += 1
            if not count%100:
                level = int(50*count/estimate)
                if level in milestones:
                    for remaining in milestones[:milestones.index(level)+1]:
                        if remaining%5:
                            message = "."
                            sys.stdout.write(message)
                            sys.stdout.flush()
                        else:
                            message = "%s%%" % (remaining*2,)
                            sys.stdout.write(message)
                            sys.stdout.flush()
                        milestones.remove(remaining)
    for zone in zones.keys():
        if "centroid" in zones[zone]:
            centroid = zones[zone]["centroid"]
            if centroid:
                station = closest(centroid, stations, "location", 0.1)
            if station[0]:
                zones[zone]["station"] = station
                count += 1
                if not count%100:
                    level = int(50*count/estimate)
                    if level in milestones:
                        for remaining in milestones[:milestones.index(level)+1]:
                            if remaining%5:
                                message = "."
                                sys.stdout.write(message)
                                sys.stdout.flush()
                            else:
                                message = "%s%%" % (remaining*2,)
                                sys.stdout.write(message)
                                sys.stdout.flush()
                            milestones.remove(remaining)
    for remaining in milestones:
        if remaining%5:
            message = "."
            sys.stdout.write(message)
            sys.stdout.flush()
        else:
            message = "%s%%" % (remaining*2,)
            sys.stdout.write(message)
            sys.stdout.flush()
    print("\n   done (%s correlations)." % count)
    message = "Writing %s..." % airports_fn
    sys.stdout.write(message)
    sys.stdout.flush()
    count = 0
    if os.path.exists(airports_fn):
        os.rename(airports_fn, "%s_old"%airports_fn)
    airports_fd = codecs.open(airports_fn, "w", "utf8")
    airports_fd.write(header)
    for airport in sorted( airports.keys() ):
        airports_fd.write("\n\n[%s]" % airport)
        for key, value in sorted( airports[airport].items() ):
            if type(value) is float: value = "%.7f"%value
            elif type(value) is tuple:
                elements = []
                for element in value:
                    if type(element) is float: elements.append("%.7f"%element)
                    else: elements.append( repr(element) )
                value = "(%s)"%", ".join(elements)
            airports_fd.write( "\n%s = %s" % (key, value) )
        count += 1
    airports_fd.write("\n")
    airports_fd.close()
    print("done (%s sections)." % count)
    message = "Writing %s..." % places_fn
    sys.stdout.write(message)
    sys.stdout.flush()
    count = 0
    if os.path.exists(places_fn):
        os.rename(places_fn, "%s_old"%places_fn)
    places_fd = codecs.open(places_fn, "w", "utf8")
    places_fd.write(header)
    for fips in sorted( places.keys() ):
        places_fd.write("\n\n[%s]" % fips)
        for key, value in sorted( places[fips].items() ):
            if type(value) is float: value = "%.7f"%value
            elif type(value) is tuple:
                elements = []
                for element in value:
                    if type(element) is float: elements.append("%.7f"%element)
                    else: elements.append( repr(element) )
                value = "(%s)"%", ".join(elements)
            places_fd.write( "\n%s = %s" % (key, value) )
        count += 1
    places_fd.write("\n")
    places_fd.close()
    print("done (%s sections)." % count)
    message = "Writing %s..." % stations_fn
    sys.stdout.write(message)
    sys.stdout.flush()
    count = 0
    if os.path.exists(stations_fn):
        os.rename(stations_fn, "%s_old"%stations_fn)
    stations_fd = codecs.open(stations_fn, "w", "utf-8")
    stations_fd.write(header)
    for station in sorted( stations.keys() ):
        stations_fd.write("\n\n[%s]" % station)
        for key, value in sorted( stations[station].items() ):
            if type(value) is float: value = "%.7f"%value
            elif type(value) is tuple:
                elements = []
                for element in value:
                    if type(element) is float: elements.append("%.7f"%element)
                    else: elements.append( repr(element) )
                value = "(%s)"%", ".join(elements)
            if type(value) is bytes:
                value = value.decode("utf-8")
            stations_fd.write( "\n%s = %s" % (key, value) )
        count += 1
    stations_fd.write("\n")
    stations_fd.close()
    print("done (%s sections)." % count)
    message = "Writing %s..." % zctas_fn
    sys.stdout.write(message)
    sys.stdout.flush()
    count = 0
    if os.path.exists(zctas_fn):
        os.rename(zctas_fn, "%s_old"%zctas_fn)
    zctas_fd = codecs.open(zctas_fn, "w", "utf8")
    zctas_fd.write(header)
    for zcta in sorted( zctas.keys() ):
        zctas_fd.write("\n\n[%s]" % zcta)
        for key, value in sorted( zctas[zcta].items() ):
            if type(value) is float: value = "%.7f"%value
            elif type(value) is tuple:
                elements = []
                for element in value:
                    if type(element) is float: elements.append("%.7f"%element)
                    else: elements.append( repr(element) )
                value = "(%s)"%", ".join(elements)
            zctas_fd.write( "\n%s = %s" % (key, value) )
        count += 1
    zctas_fd.write("\n")
    zctas_fd.close()
    print("done (%s sections)." % count)
    message = "Writing %s..." % zones_fn
    sys.stdout.write(message)
    sys.stdout.flush()
    count = 0
    if os.path.exists(zones_fn):
        os.rename(zones_fn, "%s_old"%zones_fn)
    zones_fd = codecs.open(zones_fn, "w", "utf8")
    zones_fd.write(header)
    for zone in sorted( zones.keys() ):
        zones_fd.write("\n\n[%s]" % zone)
        for key, value in sorted( zones[zone].items() ):
            if type(value) is float: value = "%.7f"%value
            elif type(value) is tuple:
                elements = []
                for element in value:
                    if type(element) is float: elements.append("%.7f"%element)
                    else: elements.append( repr(element) )
                value = "(%s)"%", ".join(elements)
            zones_fd.write( "\n%s = %s" % (key, value) )
        count += 1
    zones_fd.write("\n")
    zones_fd.close()
    print("done (%s sections)." % count)
    message = "Starting QA check..."
    sys.stdout.write(message)
    sys.stdout.flush()
    airports = configparser.ConfigParser()
    airports.read(airports_fn)
    places = configparser.ConfigParser()
    places.read(places_fn)
    stations = configparser.ConfigParser()
    stations.read(stations_fn)
    zctas = configparser.ConfigParser()
    zctas.read(zctas_fn)
    zones = configparser.ConfigParser()
    zones.read(zones_fn)
    qalog = []
    places_nocentroid = 0
    places_nodescription = 0
    for place in sorted( places.sections() ):
        if not places.has_option(place, "centroid"):
            qalog.append("%s: no centroid\n" % place)
            places_nocentroid += 1
        if not places.has_option(place, "description"):
            qalog.append("%s: no description\n" % place)
            places_nodescription += 1
    stations_nodescription = 0
    stations_nolocation = 0
    stations_nometar = 0
    for station in sorted( stations.sections() ):
        if not stations.has_option(station, "description"):
            qalog.append("%s: no description\n" % station)
            stations_nodescription += 1
        if not stations.has_option(station, "location"):
            qalog.append("%s: no location\n" % station)
            stations_nolocation += 1
        if not stations.has_option(station, "metar"):
            qalog.append("%s: no metar\n" % station)
            stations_nometar += 1
    airports_badstation = 0
    airports_nostation = 0
    for airport in sorted( airports.sections() ):
        if not airports.has_option(airport, "station"):
            qalog.append("%s: no station\n" % airport)
            airports_nostation += 1
        else:
            station = airports.get(airport, "station")
            if station not in stations.sections():
                qalog.append( "%s: bad station %s\n" % (airport, station) )
                airports_badstation += 1
    zctas_nocentroid = 0
    for zcta in sorted( zctas.sections() ):
        if not zctas.has_option(zcta, "centroid"):
            qalog.append("%s: no centroid\n" % zcta)
            zctas_nocentroid += 1
    zones_nocentroid = 0
    zones_nodescription = 0
    zones_noforecast = 0
    zones_overlapping = 0
    zonetable = {}
    for zone in zones.sections():
        if zones.has_option(zone, "centroid"):
            zonetable[zone] = {
                "centroid": eval( zones.get(zone, "centroid") )
            }
    for zone in sorted( zones.sections() ):
        if zones.has_option(zone, "centroid"):
            zonetable_local = zonetable.copy()
            del( zonetable_local[zone] )
            centroid = eval( zones.get(zone, "centroid") )
            if centroid:
                nearest = closest(centroid, zonetable_local, "centroid", 0.1)
            if nearest[1]*radian_to_km < 1:
                qalog.append( "%s: within one km of %s\n" % (
                    zone,
                    nearest[0]
                ) )
                zones_overlapping += 1
        else:
            qalog.append("%s: no centroid\n" % zone)
            zones_nocentroid += 1
        if not zones.has_option(zone, "description"):
            qalog.append("%s: no description\n" % zone)
            zones_nodescription += 1
        if not zones.has_option(zone, "zone_forecast"):
            qalog.append("%s: no forecast\n" % zone)
            zones_noforecast += 1
    if os.path.exists(qalog_fn):
        os.rename(qalog_fn, "%s_old"%qalog_fn)
    qalog_fd = codecs.open(qalog_fn, "w", "utf8")
    import time
    qalog_fd.write(
        '# Copyright (c) %s Jeremy Stanley <fungi@yuggoth.org>. Permission to\n'
        '# use, copy, modify, and distribute this software is granted under terms\n'
        '# provided in the LICENSE file distributed with this software.\n\n'
        % time.gmtime().tm_year)
    qalog_fd.writelines(qalog)
    qalog_fd.close()
    if qalog:
        print("issues found (see %s for details):"%qalog_fn)
        if airports_badstation:
            print("   %s airports with invalid station"%airports_badstation)
        if airports_nostation:
            print("   %s airports with no station"%airports_nostation)
        if places_nocentroid:
            print("   %s places with no centroid"%places_nocentroid)
        if places_nodescription:
            print("   %s places with no description"%places_nodescription)
        if stations_nodescription:
            print("   %s stations with no description"%stations_nodescription)
        if stations_nolocation:
            print("   %s stations with no location"%stations_nolocation)
        if stations_nometar:
            print("   %s stations with no METAR"%stations_nometar)
        if zctas_nocentroid:
            print("   %s ZCTAs with no centroid"%zctas_nocentroid)
        if zones_nocentroid:
            print("   %s zones with no centroid"%zones_nocentroid)
        if zones_nodescription:
            print("   %s zones with no description"%zones_nodescription)
        if zones_noforecast:
            print("   %s zones with no forecast"%zones_noforecast)
        if zones_overlapping:
            print("   %s zones within one km of another"%zones_overlapping)
    else: print("no issues found.")
    print("Indexing complete!")
