var words = document.getElementById("top");

function signup(event) {
	var user_elem = document.getElementById("signup_user")
	var user = user_elem.value;
	if(user==""){
		alert('请输入！');
		return;
	}
	$.ajax({
		type: "POST",
		url: "signup",
		data: {
			username: user
		},
		dataType: "json",
		success: function (data) {
			
			if(data['success'] == 0) {
				alert('用户已存在');
			}
			else {
				alert('注册成功');
				user_elem.value = "";
			}
		},
		error: function (htp, s, e) {
			alert('注册失败');
		}
	});
}

function login(event) {
	var user_elem = document.getElementById("login_user");
	var user = user_elem.value;
	if(user==""){
		alert('请输入！');
		return;
	}
	$.ajax({
		type: "POST",
		url: "login",
		data: {
			username: user
		},
		dataType: "json",
		success: function (data) {
			if(data['success'] == 0) {
				alert('用户不存在，请注册');
			}
			else {
				alert('登录成功！')
				words.innerHTML = "你好，" + user + "!";
				user_elem.value = "";
			}
			
		},
		error: function (htp, s, e) {
			alert('登录失败');
		}
	});
}
