setup() {
  load "${BATS_LIBS_ROOT}/bats-support/load"
  load "${BATS_LIBS_ROOT}/bats-assert/load"
}

#@test "can detect C# language" {
#    run python secureli/main.py init -ryd tests/end-to-end/test-data/Csharp_Sample/
#    assert_output --partial '[seCureLI] The following language(s) support secrets detection: C#'
#    assert_output --partial '[seCureLI] - C#: 100%'
#}

#@test "can detect Go language" {
#    run python secureli/main.py init -ryd tests/end-to-end/test-data/Go_Sample/
#    assert_output --partial '[seCureLI] - Go: 100%'
#    assert_output --partial '[seCureLI] seCureLI has been installed successfully for the following language(s): Go.'
#}

#@test "can detect Javascript language" {
#    run python secureli/main.py init -ryd tests/end-to-end/test-data/JavaScript_Sample/
#    assert_output --partial '[seCureLI] - JavaScript: 100%'
#    assert_output --partial '[seCureLI] seCureLI has been installed successfully for the following language(s): JavaScript.'
#}

#@test "can detect Kotlin language" {
#    run python secureli/main.py init -ryd tests/end-to-end/test-data/Kotlin_Sample/
#    assert_output --partial '[seCureLI] - Kotlin: 100%'
#    assert_output --partial '[seCureLI] seCureLI has been installed successfully for the following language(s): Kotlin.'
#}

#@test "can detect Python language" {
#    run python secureli/main.py init -ryd tests/end-to-end/test-data/Python_Sample/
#    assert_output --partial '[seCureLI] - Python: 100%'
#    assert_output --partial '[seCureLI] seCureLI has been installed successfully for the following language(s): Python.'
#}

#@test "can detect Swift language" {
#    run python secureli/main.py init -ryd tests/end-to-end/test-data/Swift_Sample/
#    assert_output --partial '[seCureLI] seCureLI has been installed successfully for the following language(s): Swift.'
#    assert_output --partial '[seCureLI] - Swift: 100%'
#}

#@test "can detect Terraform language" {
#    run python secureli/main.py init -ryd tests/end-to-end/test-data/Terraform_Sample/
#    assert_output --partial '[seCureLI] - Terraform: 100%'
#    assert_output --partial '[seCureLI] seCureLI has been installed successfully for the following language(s): Terraform.'
#}

#@test "can detect Typescript language" {
#    run python secureli/main.py init -ryd tests/end-to-end/test-data/Typescript_Sample/
#    assert_output --partial '[seCureLI] - TypeScript: 100%'
#    assert_output --partial '[seCureLI] seCureLI has been installed successfully for the following language(s): TypeScript.'
#}
