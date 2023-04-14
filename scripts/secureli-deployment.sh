#!/usr/bin/env bash
set -exo pipefail

pip install requests jinja2 poetry python-semantic-release # TODO: Look into Dockerizing these tools so we're not pulling them down each pipeile run
export secureliVersion=$(semantic-release print-version --current)
cd homebrew-secureli
if git rev-parse "v${secureliVersion}" >/dev/null 2>&1; then
    echo "The tag v${secureliVersion} that would have been deployed already exists, ending pipeline execution..."
    exit 1
else
    cd .. #Return back to secureli home dir to retrieve release
    echo "The tag v${secureliVersion} does not exist, proceeding with deployment"
    echo "Pulling down the most recent published secureli release v${secureliVersion}"
    gh release download v$secureliVersion
    export secureliSha256=$(sha256sum ./secureli-${secureliVersion}.tar.gz | awk '{print $1}')
    git config --global user.email "secureli-automation@slalom.com"
    git config --global user.name "Secureli Automation"
    cd homebrew-secureli
    python ./scripts/get-secureli-dependencies.py
    git checkout -b "secureli-${secureliVersion}-formula-generation"
    git add ./Formula/secureli.rb
    git commit -m "Creating pull request with latest Secureli formula for version ${secureliVersion}"
    git push origin secureli-${secureliVersion}-formula-generation --repo https://github.com/slalombuild/homebrew-secureli.git
    gh release create v${secureliVersion}
    gh pr create --title "Secureli Formula Automated Creation for version ${secureliVersion}" --body "Automated formula creation"
fi
