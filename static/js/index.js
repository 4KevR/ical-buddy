let tempElement = 0;

function activateChange(obj, index) {
    if (obj.id.includes("filter-add-button")) {
        obj.parentNode.insertAdjacentHTML("beforebegin", `<li class='list-group-item d-flex align-items-center' id='new-filter-word-${tempElement}'><input type='text' class='form-control flex-grow-1 me-2' id='new-filter-word-input-${tempElement}' aria-label='new-filter-element' placeholder='Enter new filter element'/><button type='button' id='new-filter-add-button-${tempElement}' onclick=\"submitChange(this, ${index})\" class='btn btn-outline-success me-2'><i class='bi bi-check-circle'></i></button><button type='button' onclick=\"this.parentNode.parentNode.removeChild(this.parentNode)\" class='btn btn-outline-danger'><i class='bi bi-x-circle'></i></button></li>`);
        tempElement += 1;
    } else {
        const input_name = document.querySelector("#input-name-" + index);
        const input_ical = document.querySelector("#input-ical-" + index);
        const input_token = document.querySelector("#input-token-" + index);
        input_name.readOnly = input_ical.readOnly = input_token.readOnly = false;
        obj.innerHTML = "<i class='bi bi-check-circle'></i>";
        obj.onclick = function () {
            submitChange(obj, index);
        };
    }
}

async function submitChange(obj, index) {
    const input_name_original = document.querySelector("#heading-button-" + index);
    const body = {
        "profile_name_original": input_name_original.innerText,
    };
    if (obj.id.includes("filter-remove-button")) {
        const list_element = obj.parentNode;
        body["remove_filter"] = list_element.children[0].innerText;
        const response = await sendRequest('/api/changeProfile', body);
        if (response.ok) {
            list_element.parentNode.removeChild(list_element);
        }
    } else if (obj.id.includes("new-filter-add-button")) {
        const id_split = obj.id.split("-");
        const temp_word_id = id_split[id_split.length - 1];
        const new_word_element = document.querySelector("#new-filter-word-input-" + temp_word_id);
        const new_word = new_word_element.value;
        body["add_filter"] = new_word;
        const response = await sendRequest('/api/changeProfile', body);
        if (response.ok) {
            document.querySelector("#new-filter-word-" + temp_word_id).innerHTML = `<div class=\"flex-grow-1 text-break me-2\">${new_word}</div><button type=\"button\" id=\"filter-remove-button-{{ index }}\" onclick=\"submitChange(this, ${index})\" class=\"btn btn-outline-danger  style="height: 38px; width: 42px;"\"><i class=\"bi bi-x-circle\"></i></button>`;
        } else {
            new_word_element.setCustomValidity("Filter word already exists");
            addValidityListenerOnce(new_word_element);
        }
    } else {
        const input_name = document.querySelector("#input-name-" + index);
        const input_ical = document.querySelector("#input-ical-" + index);
        const input_token = document.querySelector("#input-token-" + index);
        input_name.readOnly = input_ical.readOnly = input_token.readOnly = true;
        obj.innerHTML = "<i class=\"bi bi-pencil\"></i>";
        obj.onclick = function () {
            activateChange(obj, index)
        };
        body["profile_name"] = input_name.value;
        body["i_cal_url"] = input_ical.value;
        body["token"] = input_token.value;
        const response = await sendRequest('/api/changeProfile', body);
        if (response.ok) {
            if (input_name_original.innerText !== input_name.value) {
                input_name_original.innerText = input_name.value;
            }
        }
    }
}

async function newProfile() {
    const new_input_name = document.querySelector("#new-input-name");
    const new_input_ical = document.querySelector("#new-input-ical");
    const new_input_token = document.querySelector("#new-input-token");

    const body = {
        "new_profile_name": new_input_name.value,
        "new_ical_url": new_input_ical.value,
        "new_token": new_input_token.value,
    };
    const response = await sendRequest('/api/newProfile', body);
    if (response.ok) {
        location.reload();
    } else {
        const msg = (await response.json())["msg"]
        if (msg === "Name exists") {
            new_input_name.setCustomValidity("Profile name already exists");
            addValidityListenerOnce(new_input_name);
        } else if (msg === "Token exists") {
            new_input_token.setCustomValidity("Token is already taken");
            addValidityListenerOnce(new_input_token);
        }
    }
}

function clearModal() {
    document.querySelector("#new-input-name").value = "";
    document.querySelector("#new-input-ical").value = "";
    document.querySelector("#new-input-token").value = "";
}

async function deleteProfile(index) {
    const name_original = document.querySelector("#heading-button-" + index);
    const body = {
        "delete_profile_name": name_original.innerText,
    };
    const response = await sendRequest('/api/deleteProfile', body);
    if (response.ok) {
        location.reload();
    }
}

function copyTokenURL(element, index) {
    function returnToInitial() {
        element.innerHTML = "<i class='bi bi-clipboard'></i>";
        element.classList.remove("btn-success");
        element.classList.remove("btn-danger");
        element.classList.add("btn-outline-secondary");
    }

    const tokenInputElement = document.querySelector(`#input-token-${index}`);
    const textToCopy = location.href.split('?')[0].split('#')[0] + `filtered/${tokenInputElement.value}`;
    navigator.clipboard.writeText(textToCopy)
        .then(() => {
            element.innerHTML = "<i class='bi bi-clipboard-check'></i>";
            element.classList.remove("btn-outline-secondary");
            element.classList.add("btn-success");
            setTimeout(returnToInitial, 2000);
        })
        .catch(() => {
            element.classList.remove("btn-outline-secondary");
            element.classList.add("btn-danger");
            setTimeout(returnToInitial, 2000);
        });
}
