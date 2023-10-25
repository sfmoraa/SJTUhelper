const sign_in_btn = document.querySelector("#sign-in-btn");
const sign_up_btn = document.querySelector("#sign-up-btn");
const container = document.querySelector(".container");

// 默认显示 sign-up-mode
container.classList.add("sign-up-mode");

// sign_up_btn.addEventListener("click", () => {
//   container.classList.add("sign-up-mode");
// });
//
// sign_in_btn.addEventListener("click", () => {
//   container.classList.remove("sign-up-mode");
// });


$(document).ready(function() {
  $('#send-verification-code').click(function() {
    var emailInput = document.querySelector('input[name="email"]');
    var emailValue = emailInput.value;
    var usernameInput = document.querySelector('input[name="signup_usr"]');
    var usernameValue = usernameInput.value;
    var btn = $('#send-verification-code');  // 获取按钮元素
    btn.prop('disabled', true);  // 禁用按钮
    var countdown = 60;  // 倒计时时间，单位为秒

    // 更新按钮内容为倒计时
    var originalText = btn.val();
    btn.val(countdown + ' 秒后可再次点击');


     // console.log(countdown + ' 秒后可再次点击')
    // 定时器，每秒更新倒计时时间
    var timer = setInterval(function() {
      countdown--;
      btn.val(countdown + ' 秒后可再次点击');

      if (countdown <= 0) {
        // 恢复按钮状态和内容
        clearInterval(timer);
        btn.prop('disabled', false);
        btn.val(originalText);
      }
    }, 1000);
    $.ajax({
      url: 'send_verification_code/',  // Django视图函数的URL
      type: 'POST',
      data: {
        'csrfmiddlewaretoken': csrf_token,  // 用于防止跨站请求伪造的CSRF令牌
        'email':emailValue,
        'username':usernameValue
      },
      success: function(response) {
        // 验证码发送成功后的处理逻辑
        alert(response.message);

      },
      error: function(xhr, status, error) {
        clearInterval(timer);
        btn.prop('disabled', false);
        btn.val(originalText);
        // 发生错误时的处理逻辑
        try {
          var response = JSON.parse(xhr.responseText);

          if (response && response.message) {
            var errorMessage = response.message;
            alert(errorMessage);
          } else {
            console.log(xhr.responseText);
            alert('An error occurred.');
          }
        } catch (e) {
          console.log(xhr.responseText);
          alert('An bad error occurred.');

        }
      }
    });
  });
});

$(document).ready(function() {
  $('#signup').click(function() {
    var emailInput = document.querySelector('input[name="email"]');
    var emailValue = emailInput.value;
    var usernameInput = document.querySelector('input[name="signup_usr"]');
    var usernameValue = usernameInput.value;
    var tokenInput = document.querySelector('input[name="token"]');
    var tokenvalue = tokenInput.value;
    var pwdInput = document.querySelector('input[name="password"]');
    var pwdValue = pwdInput.value;



    $.ajax({
      url: '',  // Django视图函数的URL
      type: 'POST',
      data: {
        'csrfmiddlewaretoken': csrf_token,  // 用于防止跨站请求伪造的CSRF令牌
        'email':emailValue,
        'username':usernameValue,
        'token':tokenvalue,
        'password':pwdValue
      },
      success: function(response) {
        // 验证码发送成功后的处理逻辑
        alert(response.message);
        window.location.href="http://127.0.0.1:8000/loginpage/";
      },
      error: function(xhr, status, error) {


        // 发生错误时的处理逻辑
        try {
          var response = JSON.parse(xhr.responseText);

          if (response && response.message) {
            var errorMessage = response.message;
            alert(errorMessage);
          } else {
            console.log(xhr.responseText);
            alert('An error occurred.');
          }
        } catch (e) {
          console.log(xhr.responseText);
          alert('An bad error occurred.');

        }
      }
    });
  });
});