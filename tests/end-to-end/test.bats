setup() {
  load "${BATS_LIBS_ROOT}/bats-support/load"
  load "${BATS_LIBS_ROOT}/bats-assert/load"
}

@test "can run secureli init" {
    run python secureli/main.py init -ry
    assert_output --partial 'SeCureLI has not been setup yet.'
    assert_output --partial 'SeCureLI has been installed successfully (language = Python)'
}

@test "can run secureli scan" {
    run python secureli/main.py scan -y
    assert_output --partial 'Scan executed successfully and detected no issues!'
}
