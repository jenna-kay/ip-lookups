import re
import requests
import json
from multiprocessing import cpu_count
from concurrent.futures import ThreadPoolExecutor
import itertools
import time

# TODO
# - Rework prettifying RDAP output
# - Handle 404 codes and output for it accordingly
# - 

# Used in multiple functions
MAX_WORKERS = cpu_count() # Used for multithreading
PATTERN = re.compile(r"\d+.\d+.\d+.\d+") # IP address regex pattern
GEO_SERVER = "https://reallyfreegeoip.org/json/"    # GeoIP lookup server
RDAP_SERVER = "https://rdap.arin.net/bootstrap/ip/" # RDAP lookup server
LOG_FILE = "log.txt"

# parses a text file for IP addresses
def ipParse(textfile):
    matchList = []  

    # append each IP to matchList
    with open(textfile, 'r') as file:
        for line in file:
            for match in re.finditer(PATTERN, line):
                matchList.append(ipFind(match.group()))

    return matchList

# parses a string for an IP address
def ipFind(string):
    return re.findall(PATTERN, string)[0]

# Single geoIP request
def geo_request(ip, session):
    url = GEO_SERVER + ip
    return session.get(url).text

# Looks up GeoIP info for a list of IP addresses
def geoLookup(ipList):
    sesh = requests.Session()

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as pool:
        responseList = list(pool.map(geo_request, ipList, itertools.repeat(sesh)))

    return responseList

# Single RDAP query
# Returns a requests.Match object which contains the json
def rdap_request(ip, session):
    fail_count = 0
    url = RDAP_SERVER + ip

    while True:
        try:
            # url = urlLoop.front() + ip
            # url = RDAP_SERVER + ip
            response = session.get(url)
            status_code = response.status_code
            # print(response.status_code)
            # print(type(response.status_code))

            # print(response.status_code is not 200)

            if fail_count > 2:
                with open(LOG_FILE, 'a') as file:
                    file.write(str(status_code) + " returned for ip " + ip + "\n")
                return None

            # Create useful and readable output for 404s 
            if status_code == 404:
                return None
            elif status_code == 406:
                print("406 error")
                fail_count += 1
                continue
            elif status_code == 429: 
                # code 429: too many requests
                time.sleep(4)
                continue
            elif status_code != 200:
                fail_count += 1
                continue

        except requests.exceptions.ConnectionError:
            time.sleep(4)
            continue
            
        else:
            break
    
    return response.text

# Looks up RDAP info for a list of IP addresses
def rdapLookup(ipList):
    with open(LOG_FILE, 'w') as file:
        file.truncate()

    sesh = requests.Session()

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as pool:
        responseList = list(pool.map(rdap_request, ipList, itertools.repeat(sesh)))


    return responseList

# Reads a list of json strings
# Handle 404s
def jsonListRead(str_list):
    json_list = []
    temp_dict = {}

    for jstring in str_list:
        try:
            temp_dict = json.loads(jstring)
        
        except TypeError:
            temp_dict = {"Error" : "argument was not a string"}
        
        except ValueError:
            if len(jstring) > 1:
                temp_dict = eval(jstring)
            else:
                temp_dict = {"Error" : "argument was not in dictionary structure"}
        finally:
            json_list.append(temp_dict)
    
    return json_list

# Writes RDAP info to output   
def jsonListWriteRdap(json_list, output_file):
    with open(output_file, 'w+') as file:
        for j_dict in json_list:
            file.write(prettify_rdap(j_dict)) 

    return None

# Writes GeoIP info to output
def jsonListWriteGeo(json_list, output_file):
    with open(output_file, 'w+') as file:
        for j_dict in json_list:
            file.write(prettify_geo(j_dict))
    
    return None

# Prettifies GeoIP info
def prettify_geo(temp_dict):
    out_str = ""

    for key, value in temp_dict.items():
        out_str += str(key) + ": " + str(value) + "\n"
    
    out_str += "\n"
    
    return out_str

# Prettifies RDAP output (kinda)
# as of now only outputs limited info
# TODO:
# - display relevant info for 404 responses
# - Expand data that is displayed 
def prettify_rdap(temp_dict):
    out_str = ""
    ip = ""
    owner = ""

    # I don't like how this is structured. I feel like there's a better way to parse it.
    try:
        qurl = temp_dict['links'][0]['value']
        ip = ipFind(qurl)
        owner = temp_dict['entities'][0]['vcardArray'][1][1][3]

    except KeyError:
        # Haven't seen this output get spit out
        try:
            qurl = temp_dict['notices'][2]['links'][0]['value']
            ip = temp_dict['ip']
            owner = "OWNER_NOT_FOUND"
        
        except KeyError:
            qurl = temp_dict['notices'][2]['links'][0]['value']
            ip = ipFind(qurl)
            owner = temp_dict['entities'][3]['vcardArray'][1][1][3]

    finally:
        out_str = "IP: " + ip + "\n" + "OWNER: " +  owner + "\n\n"
        # print(out_str)
        return out_str

# maybe unused function, but may be useful for output
def list_print(List):
    for elem in List:
        print(elem)