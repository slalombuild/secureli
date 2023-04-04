import requests
import subprocess
import os
from jinja2 import Environment, FileSystemLoader

# Set necessary top level vars
environment = Environment(loader=FileSystemLoader("templates/"), autoescape=True)
template = environment.get_template("formula.txt")
filename = "secureli.rb"
secureliVersion = os.getenv("secureliVersion")
secureliSha256 = os.getenv("secureliShaSum")
secureliPackageUrl = f"https://github.com/slalombuild/homebrew-secureli/releases/download/{secureliVersion}/secureli-{secureliVersion}.tar.gz"
secureliPackageDependencies = []
secureliFormulaPath = "./homebrew-secureli/Formula/"

secureliPackageNamesCmd = "poetry show --only main | awk '{print $1}'"
secureliPackageVersionsCmd = "poetry show --only main | awk '{print $2}'"

getSecureliPackageNames = subprocess.check_output(
    secureliPackageNamesCmd, shell=True  # nosec B602, B607
)

getSecureliPackageVersions = subprocess.check_output(  # nosec B602, B607
    secureliPackageVersionsCmd, shell=True
)

decodedSecureliPackageNames = getSecureliPackageNames.decode("utf-8").split()
decodedSecureliPackageVersions = getSecureliPackageVersions.decode("utf-8").split()

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

    filteredPayload = {k: v for (k, v) in packagePayloadJsonDict.items() if "urls" in k}

    # Load all the retrieved package info from pypi into a dictionary
    data = {
        "packageName": packageName,
        "packageUrl": filteredPayload["urls"][1]["url"],
        "sha256": filteredPayload["urls"][1]["digests"]["sha256"],
    }
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
