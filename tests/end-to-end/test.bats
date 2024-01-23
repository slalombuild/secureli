setup() {
  load "${BATS_LIBS_ROOT}/bats-support/load"
  load "${BATS_LIBS_ROOT}/bats-assert/load"
}

@test "can run secureli init" {
    run python secureli/main.py init -ry
    assert_output --partial 'seCureLI has not been setup yet.'
    assert_output --partial 'seCureLI has been installed successfully (language = Python)'
}
