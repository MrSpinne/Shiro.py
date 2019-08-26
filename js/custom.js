window.onload = function () {
	params = new URLSearchParams(window.location.search);
	if (params.get("code")) {
		clearUrl();
		Swal.fire({
			title: "Shiro is ready!",
			text: "Are you too? Type s.help in your guild to get started.",
			type: "success",
			confirmButtonText: "Okay",
			confirmButtonColor: "#777CD9"
		});
	} else if (params.get("error")) {
		clearUrl();
		description = "";
		if (params.get("error_description")) {
			description = params.get("error_description") + ". ";
		}
		Swal.fire({
			title: "Invitation failed!",
			text: description + "If you need help, check out our support server.",
			type: "error",
			confirmButtonText: "Get Help",
			confirmButtonColor: "#777CD9",
			showCancelButton: true,
			cancelButtonText: "Close",
			cancelButtonColor: "#777CD9"
		}).then((result) => {
			if (result.dismiss === Swal.DismissReason.confirm) {
				var win = window.open("https://support.shiro.pro", "_blank");
				win.focus();
				Swal.fire({
					title: "You have been invited!",
					text: "Start talking to others. Ask your questions if you have any.",
					type: "success",
					confirmButtonText: "Okay",
					confirmButtonColor: "#777CD9"
		});
			}
		})
	}
}

function clearUrl() {
	var getUrl = window.location;
	var baseUrl = getUrl.protocol + "//" + getUrl.host + "/" + getUrl.pathname.split("/")[1];
	window.history.pushState({id: "homepage"}, "Shiro Discord Bot", baseUrl);
}