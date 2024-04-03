setup() {
  load "${BATS_LIBS_ROOT}/bats-support/load"
  load "${BATS_LIBS_ROOT}/bats-assert/load"
}

@test "can detect language" {
    #cd tests/end-to-end/test-data/Csharp_Sample/
    run python secureli/main.py init -ry
    assert_output --partial 'Hooks successfully updated to latest version'
    assert_output --partial 'seCureLI has been installed successfully'
}

