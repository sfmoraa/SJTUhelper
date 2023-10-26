//提取到函数外面作为全局变量
		var rm = document.getElementById("rightMenu");

		//自定义一个浏览器右键菜单，单击右键是显示它
		//oncontextmenu上下文菜单事件，右键菜单
		document.documentElement.oncontextmenu = function(e) {
			//显示我们自己定义的右键菜单
			//1.找到菜单
			//提取到函数外面作为全局变量

			//兼容Event对象
			e = e || window.event;

			//2.设置菜单的位置等于鼠标的坐标
			//判断：如果鼠标的位置+菜单的宽度>网页的宽度，那么就改为右边定位
			//鼠标坐标
			var mx = e.clientX;
			var my = e.clientY;
			//菜单宽度
			var rmWidth = parseInt(rm.style.width);
			//网页的宽度(高度用同样的方法解决)
			var pageWidth = document.documentElement.clientWidth;
			//console.log(pageWidth);
			if ((mx + rmWidth) < pageWidth) {
				rm.style.left = mx + "px";
				rm.style.top = my + "px";
			} else {
				rm.style.right = mx + "px";
				rm.style.top = my + "px";
			}

			//3.显示右键菜单
			rm.style.display = "block";

			//阻止默认的右键菜单显示
			return false;
		};

		//不需要积隐藏右键菜单
		document.documentElement.onclick = function() {
			rm.style.display = "none";
		}