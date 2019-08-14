window.onload = function () {
	if (window.location.search) {
		Swal.fire({
			title: "Shiro is ready!",
			text: "Are you too? Type s.help in your guild to get started.",
			type: "success",
			confirmButtonText: "Okay",
			confirmButtonColor: "#777CD9"
		})
		
		var getUrl = window.location;
		var baseUrl = getUrl.protocol + "//" + getUrl.host + "/" + getUrl.pathname.split("/")[1];
		window.history.pushState({id: "homepage"}, "Shiro Discord Bot", baseUrl);
	}
} 