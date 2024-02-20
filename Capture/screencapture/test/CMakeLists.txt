# CTests for screencapture project

add_test(NAME screencapture_help_test
        COMMAND reprostim-screencapture -h)

# Optionally, set properties for the test
set_tests_properties(screencapture_help_test
        PROPERTIES
        PASS_REGULAR_EXPRESSION "Usage\\: reprostim-screencapture.*"
        WILL_FAIL FALSE
        EXPECTED_RETURN_CODE 0
)