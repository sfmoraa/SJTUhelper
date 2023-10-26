var noSleep = new NoSleep();
      var wakeLockEnabled = false;
      var toggleEl = document.querySelector("#open");
      var toggleE2 = document.querySelector("#close");
      toggleEl.addEventListener('click', function() {
        if (!wakeLockEnabled) {
          noSleep.enable(); // keep the screen on!
          wakeLockEnabled = true;
          toggleEl.value = "开启常亮";
          window.alert("常亮模式已开启");
        } 
      }, false);
      toggleE2.addEventListener('click', function() {
          if (wakeLockEnabled) {
            noSleep.disable(); // let the screen turn off.
            wakeLockEnabled = false;
            toggleE2.value = "关闭常亮";
            window.alert("已关闭常亮模式");
          }
        }, false);