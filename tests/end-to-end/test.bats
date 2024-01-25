setup() {
  load "${BATS_LIBS_ROOT}/bats-support/load"
  load "${BATS_LIBS_ROOT}/bats-assert/load"
}

@test "can run secureli init" {
    run python secureli/main.py init -ry
    assert_output --partial 'Hooks successfully updated to latest version'
    assert_output --partial 'seCureLI has been installed successfully'
}

@test "can run secureli scan" {
    run python secureli/main.py scan -y -m all-files
    assert_output --partial 'Detected the following language(s):'
}
