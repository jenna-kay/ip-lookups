import ipToolbox
from time import time

def main():
    filename = "list_of_ips.txt"

    # Start clock
    start = time()

    print("Parsing input file for IP addresses")
    # Parse a text file for IP addresses
    ipList = ipToolbox.ipParse(filename)

    print("Performing GeoIP lookups")
    # Perform GeoIP lookup
    geoList = ipToolbox.geoLookup(ipList)

    print("Performing RDAP lookups")
    # Perform RDAP lookup
    rdapList = ipToolbox.rdapLookup(ipList)

    print("Reading collected jsons")
    # Read the json strings
    geo_results = ipToolbox.jsonListRead(geoList)
    rdap_results = ipToolbox.jsonListRead(rdapList)

    print("Writing to output file")
    # Write to output files
    ipToolbox.jsonListWriteGeo(geo_results, "GeoIP_output.txt")
    ipToolbox.jsonListWriteRdap(rdap_results, "RDAP_output.txt")

    # Stop clock
    elapsed_time = time() - start

    with open(ipToolbox.LOG_FILE, 'a') as file:
        file.write(str(elapsed_time) + " seconds")

main()