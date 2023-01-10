#!/bin/sh

sqlite3 ./instance/database.db <<EOF
INSERT INTO OTP_CODE(code_value) VALUES("$initial_otp");
EOF