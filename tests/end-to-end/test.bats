setup() {
  load "${BATS_LIBS_ROOT}/bats-support/load"
  load "${BATS_LIBS_ROOT}/bats-assert/load"
}

@test "can run secureli" {
    run python secureli/main.py scan
    assert_output --partial 'Scan executed successfully and detected no issues!'
}
