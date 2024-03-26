# Test to ensure pre-exisiting hooks within the .pre-commit-config.yaml files
# are persisted when installing secureli

MOCK_REPO='tests/test-data/mock-repo'

setup() {
  load "${BATS_LIBS_ROOT}/bats-support/load"
  load "${BATS_LIBS_ROOT}/bats-assert/load"
  mkdir -p $MOCK_REPO
  echo 'print("hello world!")' > $MOCK_REPO/hw.py
  run git init $MOCK_REPO
}

@test "can preserve pre-existing hooks" {
    run python secureli/main.py init -y  --directory $MOCK_REPO
    run grep 'https://github.com/psf/black' $MOCK_REPO/.secureli/.pre-commit-config.yaml
    assert_output --partial 'https://github.com/psf/black'
}

teardown() {
    rm -rf $MOCK_REPO
}
