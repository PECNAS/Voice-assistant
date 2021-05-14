async function delete_command(e) {
	li = e.path[1]; // получаем родительский элемент
	type = li.children[0].innerHTML;
	phrase = li.children[1].innerHTML;
	action = li.children[2].innerHTML;

	await eel.delete_command(type, phrase, action);
	alert("Команда удалена!");

	li.remove();
}

function add_command_to_list(type, phrase, action) {
	var user_commands_list = document.querySelector(".user-commands-list");
	var li = document.createElement("li")
	li.classList = "user-commands-element";

	var type_element = document.createElement("label");
	type_element.classList = "user-command-type";
	type_element.innerHTML = type;

	var phrase_element = document.createElement("label");
	phrase_element.classList = "user-command-phrase";
	phrase_element.innerHTML = phrase;

	var action_element = document.createElement("label");
	action_element.classList = "user-command-action";
	action_element.innerHTML = action;

	var delete_button = document.createElement("button")
	delete_button.classList = "btn user-command-button-delete"
	delete_button.innerHTML = "Удалить команду"

	li.append(type_element);
	li.append(phrase_element);
	li.append(action_element);
	li.append(delete_button);

	user_commands_list.append(li);
}

window.onload = async function(e) {
	settings = await eel.get_settings()();
	
	if (settings['appeal'] == true) {
		var checkbox = document.querySelector(".appeal-radio-true");
		checkbox.checked = true;
	} else {
		var checkbox = document.querySelector(".appeal-radio-false");
		checkbox.checked = true;
	}

	var input = document.querySelector(".assistant-name-input");
	input.value = settings['assistant_name'];

	var select = document.querySelector(".devices");
	settings['devices'].forEach((element) => {
		var option = document.createElement("option");
		option.value = element['index']
		option.innerHTML = element['name'];
		if (element['index'] == settings['device_index']) {
			option.selected = true;
		}
		select.append(option)
	});

	var select = document.querySelector(".voices")
	settings['voices'].forEach((element) => {
		var option = document.createElement("option");
		option.value = element['voice_id']
		option.innerHTML = element['name'];
		if (element['voice_id'] == settings['voice_id']) {
			option.selected = true;
		}
		select.append(option)
	})

	settings['user_commands'].forEach((element) => {
		add_command_to_list(element['type'], element['phrase'], element['action']);
	})

	var buttons = document.getElementsByClassName("btn user-command-button-delete");
	for (i = 0; i < buttons.length; i += 1) {
		buttons[i].onclick = delete_command;
	}

}
document.querySelector("#accept-button").onclick = async function(e) {
	var true_checkbox = document.querySelector(".appeal-radio-true").checked;
	var false_checkbox = document.querySelector(".appeal-radio-false").checked;
	if (true_checkbox == true && false_checkbox == false) {
		var appeal = true;
	} else if (true_checkbox == false && false_checkbox == true) {
		var appeal = false;
	} else {
		var appeal = false;
	}
	var assistant_name_input = document.querySelector(".assistant-name-input").value;
	var devices_select = document.querySelector(".devices").value;
	var voices_select = document.querySelector(".voices").value;

	await eel.update_config(appeal, assistant_name_input, devices_select, voices_select);
	location.href = "main.html";
}
document.querySelector("#cancel-button").onclick = async function(e) {
	location.href = "main.html";
}

document.querySelector(".command-type-select").onchange = function(e) {
	var command_type = document.querySelector(".command-type-select").value

	if (command_type == "Запуск программы") {
		document.querySelector(".command-action-input").placeholder = "Введите путь до программы";
	} else {
		document.querySelector(".command-action-input").placeholder = "Введите действие";
	}
}

document.querySelector("#add-command-button").onclick = async function(e) {
	var command_type = document.querySelector(".command-type-select").value
	var command_phrase = document.querySelector(".command-phrase-input").value
	var command_action = document.querySelector(".command-action-input").value

	if (command_type != "" && command_phrase != "" && command_action != "") {
		result = await eel.add_user_command(command_type, command_phrase, command_action)();
		if (result == true) {
			alert("Команда успешно добавлена");
			document.querySelector(".command-type-select").value = "";
			document.querySelector(".command-phrase-input").value = "";
			document.querySelector(".command-action-input").value = "";

			add_command_to_list(command_type, command_phrase, command_action);
		} else {
			alert("Данная команда уже существует");
		}
	} else {
		alert("Все поля должны быть заполнены");
	}
}
