# CTests for videocapture project

add_test(NAME videocapture_help_test
        COMMAND reprostim-videocapture -h)

# Optionally, set properties for the test
set_tests_properties(videocapture_help_test
        PROPERTIES
        PASS_REGULAR_EXPRESSION "Usage\\: reprostim-videocapture.*"
        WILL_FAIL FALSE
        EXPECTED_RETURN_CODE 78
)