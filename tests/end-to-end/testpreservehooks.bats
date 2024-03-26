# Test to ensure pre-exisiting hooks within the .pre-commit-config.yaml files
# are persisted when installing secureli

MOCK_REPO='tests/test-data/mock-repo'

setup() {
  load "${BATS_LIBS_ROOT}/bats-support/load"
  load "${BATS_LIBS_ROOT}/bats-assert/load"
  mkdir -p $MOCK_REPO
  echo 'repos:' >> $MOCK_REPO/.pre-commit-config.yaml
  echo '-   repo: https://github.com/hhatto/autopep8' >> $MOCK_REPO/.pre-commit-config.yaml
  echo '    rev: v2.1.0' >> $MOCK_REPO/.pre-commit-config.yaml
  echo '    hooks:' >> $MOCK_REPO/.pre-commit-config.yaml
  echo '    -   id: autopep8' >> $MOCK_REPO/.pre-commit-config.yaml
  echo 'fail_fast: false' >> $MOCK_REPO/.pre-commit-config.yaml
  echo 'print("hello world!")' > $MOCK_REPO/hw.py
  run git init $MOCK_REPO
}

@test "can preserve pre-existing hooks" {
    run python secureli/main.py init -y  --directory $MOCK_REPO
    run grep 'https://github.com/hhatto/autopep8' $MOCK_REPO/.secureli/.pre-commit-config.yaml
    assert_output --partial 'https://github.com/hhatto/autopep8'
    run grep 'fail_fast: false' $MOCK_REPO/.secureli/.pre-commit-config.yaml
    assert_output --partial 'fail_fast: false'
}

teardown() {
    rm -rf $MOCK_REPO
}
