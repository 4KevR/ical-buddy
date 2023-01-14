function activateUsernameChange() {
    const input_new_user_name = document.querySelector('#input-change-user-name');
    const button = document.querySelector('#button-user-name-change');
    input_new_user_name.readOnly = false;
    button.setAttribute('type', 'submit');
    button.onclick = () => {
        changeUsername();
    };
    button.innerText = "Submit";
}

async function changeUsername() {
    const input_new_user_name = document.querySelector('#input-change-user-name');
    const button = document.querySelector('#button-user-name-change');
    const body = {
        "new_user_name": input_new_user_name.value
    };
    const response = await sendRequest("/api/changeUsername", body);
    if (response.ok) {
        location.href = response.url;
    } else {
        const msg = (await response.json())["msg"];
        if (msg === "Username exists") {
            input_new_user_name.setCustomValidity("The username is already taken");
            addValidityListenerOnce(input_new_user_name);
        } else if (msg === "Already your username") {
            input_new_user_name.readOnly = true;
            button.removeAttribute('type');
            button.onclick = () => {
                activateUsernameChange();
            };
            button.innerText = "Edit";
        }
    }
}

async function changePassword() {
    const old_password = document.querySelector("#input-old-password");
    const new_password = document.querySelector("#input-new-password");
    const new_password_repeat = document.querySelector("#input-repeat-new-password");
    if (new_password.value !== new_password_repeat.value) {
        new_password_repeat.setCustomValidity("The passwords do not match");
        addValidityListenerOnce(new_password_repeat);
        return false;
    }
    const body = {
        "old_password": old_password.value,
        "new_password": new_password.value,
    };
    const response = await sendRequest("/api/changePassword", body);
    if (response.ok) {
        document.querySelector('#change-password-form').reset();
    } else {
        const msg = (await response.json())["msg"];
        if (msg === "Wrong old password") {
            old_password.setCustomValidity("The old password is wrong");
            addValidityListenerOnce(old_password);
            old_password.value = "";
        }
    }
}

async function removeCode(button) {
    const list_element = button.parentNode;
    const body = {
        "remove_code": list_element.children[0].innerText,
    };
    const response = await sendRequest('/api/removeCode', body);
    if (response.ok) {
        list_element.parentNode.removeChild(list_element);
    }
}

function createCode(button) {
    button.parentNode.insertAdjacentHTML("beforebegin", `<li class='list-group-item d-flex'><input type='text' class='form-control w-50' aria-label='new-otp-code' placeholder='Enter new OTP code'/><select class="form-select w-25"><option value="0" selected>Not Admin</option><option value="1">Admin</option></select><div class='flex-grow-1'></div><button type='button' onclick=\"submitCode(this)\" class='btn btn-outline-success me-2'><i class='bi bi-check-circle'></i></button><button type='button' onclick=\"this.parentNode.parentNode.removeChild(this.parentNode)\" class='btn btn-outline-danger'><i class='bi bi-x-circle'></i></button></li>`);
}

async function submitCode(button) {
    const list_element = button.parentNode;
    const new_code_input = list_element.children[0];
    const new_code = new_code_input.value;
    const for_admin = list_element.children[1].value === "1";
    const body = {
        "new_code": new_code,
        "for_admin": for_admin,
    };
    const response = await sendRequest('/api/addCode', body);
    if (response.ok) {
        let newInnerHTML = `<div class="d-flex align-items-center">${new_code}`;
        if (for_admin) {
            newInnerHTML += `<span class="badge rounded-pill text-bg-primary ms-2">Admin</span>`;
        }
        newInnerHTML += `</div><div class="flex-grow-1"></div><button type="button" onclick="removeCode(this)" class="btn btn-outline-danger"><i class="bi bi-x-circle"></i></button>`;
        list_element.innerHTML = newInnerHTML;
    } else {
        new_code_input.setCustomValidity("OTP code already exists or existed in the past");
        addValidityListenerOnce(new_code_input);
    }
}

async function deleteAccount() {
    const response = await sendRequest("/api/deleteAccount", {});
    if (response.ok) {
        location.href = response.url;
    }
}

document.addEventListener('DOMContentLoaded', () => {
    document.querySelector('#danger-zone').addEventListener("click", () => {
        window.open('https://youtu.be/siwpn14IE7E?t=28', '_blank').focus();
    });
});