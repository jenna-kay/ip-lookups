import re
import requests
import json
from multiprocessing import cpu_count
from concurrent.futures import ThreadPoolExecutor
import itertools
import time

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
# Returns tuple of the form (ip, status, response_str)
def rdap_request(ip, session):
    url = RDAP_SERVER + ip

    with open(LOG_FILE, 'a') as file:
        while True:
            try:
                response = session.get(url)
                status_code = response.status_code
                end_tuple = (ip, status_code, response.text)

                if status_code == 404:
                    file.write(str(response) + "\n")
                    return end_tuple
                elif status_code == 406:
                    file.write(str(response) + "\n")
                    file.write(response.text)
                    continue
                elif status_code == 429: 
                    # code 429: too many requests
                    file.write(str(response) + "\n")
                    time.sleep(5)
                    continue
                elif status_code == 504:
                    file.write(str(response) + "\n")
                    time.sleep(5)
                    continue
                elif status_code != 200:
                    file.write(str(response) + "\n")
                    file.write(response.text + "\n")
                    continue

            except requests.exceptions.ConnectionError:
                file.write("connection error caught\n")
                time.sleep(4)
                continue
                
            else:
                break
    
    return end_tuple

# Looks up RDAP info for a list of IP addresses
# returns a list of tuples of (ip address, status code, response text)
def rdapLookup(ipList):
    with open(LOG_FILE, 'w') as file:
        file.truncate()

    sesh = requests.Session()

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as pool:
        responseTupleList = list(pool.map(rdap_request, ipList, itertools.repeat(sesh)))

    return responseTupleList

# Reads a list of json strings
def jsonListRead(response_list):
    json_list = []
    json_dict = {}

    if(type(response_list[0]) == tuple):
        for ip, status, string in response_list:
            json_dict['ip'] = ip
            json_dict['status_code'] = status
            json_dict['contents'] = json.loads(string)
            json_list.append(json_dict)
        
    elif(type(response_list[0]) == str):
        for jstring in response_list:
            json_dict = json.loads(jstring)
            json_list.append(json_dict)

    else: 
        print("not a string or tuple")

    return json_list

# Writes RDAP info to output   
def jsonListWriteRdap(json_list, output_file):
    with open(output_file, 'w+') as file:
        for j_dict in json_list:
            file.write(prettify_rdap(j_dict) + "\n") 

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

def print_dict(diction):
    out_str = ""

    for key, value in diction.items():
        out_str += key + ": " + str(value) + "\n"
    
    return out_str + "\n"

# Prettifies RDAP output 
# Could stand to display the contents a little nicer (make print_dict recursive?)
def prettify_rdap(temp_dict):
    out_str = "IP: " + temp_dict['ip']

    if(temp_dict['status_code'] != 200):
        out_str += temp_dict['ip']  + " returned with HTTP code " + str(temp_dict['status_code']) + "\n"
        return out_str
    
    else:
        out_str += "\n"

    out_str += print_dict(temp_dict['contents'])
    
    return out_str