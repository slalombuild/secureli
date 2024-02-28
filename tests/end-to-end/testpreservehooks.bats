MOCK_REPO='tests/test-data/mock-repo'

setup() {
  load "${BATS_LIBS_ROOT}/bats-support/load"
  load "${BATS_LIBS_ROOT}/bats-assert/load"
  mkdir -p $MOCK_REPO
  echo '# Ive been here the whole time!' > $MOCK_REPO/.pre-commit-config.yaml
  echo 'print("hello world!")' > $MOCK_REPO/hw.py
  run git init $MOCK_REPO
}

@test "can preserve pre-existing hooks" {
    run python secureli/main.py init -y  --directory $MOCK_REPO
    run grep '# Ive been here the whole time!' $MOCK_REPO/.secureli/.pre-commit-config.yaml
    assert_output --partial '# Ive been here the whole time!'
}

teardown() {
    rm -rf $MOCK_REPO
}
