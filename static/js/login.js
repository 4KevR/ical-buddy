async function login(register) {
    const input_username = document.querySelector("#username");
    const input_password = document.querySelector("#password");

    const body = {
        "username": input_username.value,
        "password": input_password.value,
    }
    if (register === "register") {
        const input_password_repeat = document.querySelector("#repeat_password");
        const input_otp_code = document.querySelector("#otp");
        if (input_password.value !== input_password_repeat.value) {
            input_password_repeat.setCustomValidity("The passwords do not match");
            addValidityListenerOnce(input_password_repeat);
            return false;
        }
        body["otp"] = input_otp_code.value;
    }

    const options = {
        method: 'post',
        credentials: 'same-origin',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(body),
    };

    const url = (register === "register") ? "/api/register" : "/api/login";
    const response = await fetch(url, options)
    if (response.ok) {
        location.href = response.url;
    } else {
        const toastBody = document.querySelector("#failedOperationToastBody");
        const msg = (await response.json())["msg"]
        if (msg === "Invalid OTP") {
            toastBody.innerText = "Provided invalid OTP code";
        } else if (msg === "Username exists") {
            toastBody.innerText = "The username is already taken";
        } else if (msg === "Login failed") {
            toastBody.innerText = "Wrong username or password";
        }
        const failedOperationToast = document.querySelector("#failedOperationToast");
        const toast = new bootstrap.Toast(failedOperationToast);
        toast.show();
    }
}