setup() {
  load "${BATS_LIBS_ROOT}/bats-support/load"
  load "${BATS_LIBS_ROOT}/bats-assert/load"
}

@test "can detect C# language" {
    #cd tests/end-to-end/test-data/Csharp_Sample/
    run python secureli/main.py init -ry
    assert_output --partial 'Hooks successfully updated to latest version'
    assert_output --partial 'seCureLI has been installed successfully'
}

@test "can detect Go language" {
    #cd tests/end-to-end/test-data/Go_Sample/
    run python secureli/main.py init -ry
    assert_output --partial 'Hooks successfully updated to latest version'
    assert_output --partial 'seCureLI has been installed successfully'
}

@test "can detect Javascript language" {
    #cd tests/end-to-end/test-data/JavaScript_Sample/
    run python secureli/main.py init -ry
    assert_output --partial 'Hooks successfully updated to latest version'
    assert_output --partial 'seCureLI has been installed successfully'
}

@test "can detect Kotlin language" {
    #cd tests/end-to-end/test-data/Kotlin_Sample/
    run python secureli/main.py init -ry
    assert_output --partial 'Hooks successfully updated to latest version'
    assert_output --partial 'seCureLI has been installed successfully'
}

@test "can detect Python language" {
    #cd tests/end-to-end/test-data/Python_Sample/
    run python secureli/main.py init -ry
    assert_output --partial 'Hooks successfully updated to latest version'
    assert_output --partial 'seCureLI has been installed successfully'
}

@test "can detect Swift language" {
    #cd tests/end-to-end/test-data/Swift_Sample/
    run python secureli/main.py init -ry
    assert_output --partial 'Hooks successfully updated to latest version'
    assert_output --partial 'seCureLI has been installed successfully'
}

@test "can detect Terraform language" {
    #cd tests/end-to-end/test-data/Terraform_Sample/
    run python secureli/main.py init -ry
    assert_output --partial 'Hooks successfully updated to latest version'
    assert_output --partial 'seCureLI has been installed successfully'
}

@test "can detect Typescript language" {
    #cd tests/end-to-end/test-data/Typescript_Sample/
    run python secureli/main.py init -ry
    assert_output --partial 'Hooks successfully updated to latest version'
    assert_output --partial 'seCureLI has been installed successfully'
}

@test "can detect Cloudformation language" {
    #cd tests/end-to-end/test-data/CloudFormation_Sample/
    run python secureli/main.py init -ry
    assert_output --partial 'Hooks successfully updated to latest version'
    assert_output --partial 'seCureLI has been installed successfully'
}