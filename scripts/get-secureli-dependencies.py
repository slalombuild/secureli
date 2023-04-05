import requests
import subprocess
import os
from jinja2 import Environment, FileSystemLoader

# Set necessary top level vars
environment = Environment(loader=FileSystemLoader("templates/"), autoescape=True)
template = environment.get_template("formula.txt")
filename = "secureli.rb"
secureliVersion = os.getenv("secureliVersion")
secureliSha256 = os.getenv("secureliSha256")
secureliPackageUrl = f"https://github.com/slalombuild/homebrew-secureli/releases/download/v{secureliVersion}/secureli-{secureliVersion}.tar.gz"
secureliPackageDependencies = []
secureliFormulaPath = "./homebrew-secureli/Formula"

secureliPackageNamesCmd = "poetry show --only main | awk '{print $1}'"
secureliPackageVersionsCmd = "poetry show --only main | awk '{print $2}'"

getPackageNames = subprocess.Popen(
    ["poetry", "show", "--only", "main"], stdout=subprocess.PIPE
)
filterPackageNames = subprocess.Popen(
    ["awk", "{print $1}"], stdin=getPackageNames.stdout, stdout=subprocess.PIPE
)
getPackageNames.stdout.close()

secureliPackageNames, error = filterPackageNames.communicate()

decodedSecureliPackageNames = secureliPackageNames.decode("utf-8").split()

getPackageVersions = subprocess.Popen(
    ["poetry", "show", "--only", "main"], stdout=subprocess.PIPE
)
filterPackageVersions = subprocess.Popen(
    ["awk", "{print $2}"], stdin=getPackageVersions.stdout, stdout=subprocess.PIPE
)
getPackageVersions.stdout.close()

secureliPackageVersions, error = filterPackageVersions.communicate()

decodedSecureliPackageVersions = secureliPackageVersions.decode("utf-8").split()

# This loops through all packages that secureli requires to be properly built
# It then outputs the package information to a dictionary that will be templated into a Homebrew formula for end-user consumption
for packageName, packageVersion in zip(
    decodedSecureliPackageNames, decodedSecureliPackageVersions
):
    print(
        f"The necessary package retrieved from poetry is {packageName} with version {packageVersion}"
    )
    packagePayload = requests.get(
        f"https://pypi.org/pypi/{packageName}/{packageVersion}/json"
    )
    packagePayloadJsonDict = packagePayload.json()

    for package in packagePayloadJsonDict["urls"]:
        if package["packagetype"] == "sdist":
            url = package["url"]
            sha256 = package["digests"]["sha256"]
            break

    # Load all the retrieved package info from pypi into a dictionary
    data = {"packageName": packageName, "packageUrl": url, "sha256": sha256}
    secureliPackageDependencies.append(data)

# Create a dict that contains all the package dependency information
# Context will then be passed into the Jinja template renderer to create the homebrew file
context = {
    "secureliPackageDependencies": secureliPackageDependencies,
    "secureliVersion": secureliVersion,
    "secureliSha256": secureliSha256,
    "secureliPackageUrl": secureliPackageUrl,
}

with open(f"{secureliFormulaPath}/{filename}", mode="w", encoding="utf-8") as message:
    message.write(template.render(context))
    print(f"Homebrew formula file called {filename} has been created")