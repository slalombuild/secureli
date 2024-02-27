setup() {
  load "${BATS_LIBS_ROOT}/bats-support/load"
  load "${BATS_LIBS_ROOT}/bats-assert/load"
  mkdir tests/end-to-end/mock-repo
  echo '# Ive been here the whole time!' > tests/end-to-end/mock-repo/.pre-commit-config.yaml
  echo 'print('hello world!')' > tests/end-to-end/mock-repo/hw.py
  run git init tests/end-to-end/mock-repo
}

@test "can preserve pre-existing hooks" {
    run python secureli/main.py init -y  --directory tests/end-to-end/mock-repo
    run grep '# Ive been here the whole time!' tests/end-to-end/mock-repo/.pre-commit-config.yaml
    assert_output --partial '# Ive been here the whole time!'
}

teardown() {
    rm -rf tests/end-to-end/mock-repo
}
