setup() {
  load '../.submodules/test_helper/bats-support/load'
  load '../.submodules/test_helper/bats-assert/load'
}

@test "can run secureli" {
    run python secureli/main.py scan
    assert_output --partial 'Scan executed successfully and detected no issues!'
}
