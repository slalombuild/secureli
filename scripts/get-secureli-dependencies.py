import requests
import subprocess
import os
from jinja2 import Environment, FileSystemLoader

# Set necessary top level vars
environment = Environment(loader=FileSystemLoader("templates/"))
template = environment.get_template("formula.txt")
filename = 'secureli.rb'
secureliVersion = "0.1.0" # Hard-coded for testing purposes, this should be retrieved as an ENV in the pipeline
secureliSha256 = "9910509c0f82f63ecf12146a9842f6c424c5849d559d3824915a310270d38867" # Generated at runtime when tarball is published
secureliPackageDependencies = []

secureliPackageNamesCmd="poetry show --only main | sed 's/(!)//' | awk -F ' ' '{print $1}'"
secureliPackageVersionsCmd="poetry show --only main | sed 's/(!)//' | awk -F ' ' '{print $2}'"
                                       
getSecureliPackageNames = subprocess.check_output(secureliPackageNamesCmd, shell=True)
getSecureliPackageVersions = subprocess.check_output(secureliPackageVersionsCmd, shell=True)

decodedSecureliPackageNames = getSecureliPackageNames.decode('utf-8').split()
decodedSecureliPackageVersions = getSecureliPackageVersions.decode('utf-8').split()
    
# This loops through all packages that secureli requires to be properly built 
# It then outputs the package information to a dictionary that will be templated into a Homebrew formula for end-user consumption
for packageName,packageVersion in zip(decodedSecureliPackageNames, decodedSecureliPackageVersions):
    # print(f"The package name is {packageName} with version {packageVersion}")
    packagePayload = requests.get(f"https://pypi.org/pypi/{packageName}/{packageVersion}/json")
    packagePayloadJsonDict = packagePayload.json()

    filteredPayload = {k:v for (k,v) in packagePayloadJsonDict.items() if 'urls' in k}

    # Load all the retrieved package info into a dictionary
    data = {
        'packageName': packageName, 
        'packageurl': filteredPayload['urls'][1]['url'],
        'sha256': filteredPayload['urls'][1]['digests']['sha256']
    }
    secureliPackageDependencies.append(data)

# Create a dict that contains all the package dependency information
# Context will then be passed into the Jinja template renderer to create the homebrew file
context = {
    "secureliPackageDependencies": secureliPackageDependencies,
    "secureliVersion": secureliVersion,
    "secureliSha256": secureliSha256 
}

with open(filename, mode="w", encoding="utf-8") as message:
    message.write(template.render(context))
    print(f'File named {filename} has been created')
