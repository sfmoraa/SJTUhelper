
curWwwPath=window.document.location.href;
//获取地址最后一个“/”的下标
pathName = window.document.location.pathname;
pos = curWwwPath.indexOf(pathName);
label = curWwwPath.substring(pos+1, curWwwPath.length);

if (label=="zhihu" || label=="zhihu/"){
    element = window.document.getElementById("zhihu");
    element.className="active";
    window.document.getElementById("header-title-h1").innerText="zhihu";
    window.document.getElementById("header-title-p").innerText="an online chat platform";
}
if (label=="github" || label=="github/"){
    element = window.document.getElementById("github");
    element.className="active";
    window.document.getElementById("header-title-h1").innerText="github";
    window.document.getElementById("header-title-p").innerText="an online code platform";
}
if (label=="bilibili" || label=="bilibili/"){
    element = window.document.getElementById("bilibili");
    element.className="active";
    window.document.getElementById("header-title-h1").innerText="bilibili";
    window.document.getElementById("header-title-p").innerText="an online video platform";
}
if (label=="weibo" || label=="weibo/"){
    element = window.document.getElementById("weibo");
    element.className="active";
    window.document.getElementById("header-title-h1").innerText="weibo";
    window.document.getElementById("header-title-p").innerText="an online blog platform";
}
if (label=="shuiyuan" || label=="shuiyuan/"){
    element = window.document.getElementById("shuiyuan");
    element.className="active";
    window.document.getElementById("header-title-h1").innerText="shuiyuan";
    window.document.getElementById("header-title-p").innerText="an online SJTU chat platform";
}
if (label=="canvas" || label=="canvas/"){
    element = window.document.getElementById("canvas");
    element.className="active";
    window.document.getElementById("header-title-h1").innerText="canvas";
    window.document.getElementById("header-title-p").innerText="an online SJTU homework platform";
}
if (label=="seiee" || label=="seiee/"){
    element = window.document.getElementById("seiee");
    element.className="active";
    window.document.getElementById("header-title-h1").innerText="seiee";
    window.document.getElementById("header-title-p").innerText="an online seiee information platform";
}
if (label=="dekt" || label=="dekt/"){
    element = window.document.getElementById("dekt");
    element.className="active";
    window.document.getElementById("header-title-h1").innerText="dekt";
    window.document.getElementById("header-title-p").innerText="an online dekt platform";
}

