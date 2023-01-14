#!/bin/bash

sqlite3 ./instance/database.db <<EOF
INSERT INTO OTP_CODE(code_value, for_admin) VALUES("$initial_otp", true);
EOF