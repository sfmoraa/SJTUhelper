
curWwwPath=window.document.location.href;
//获取地址最后一个“/”的下标
pathName = window.document.location.pathname;
pos = curWwwPath.indexOf(pathName);
label = curWwwPath.substring(pos+1, curWwwPath.length);

if (label=="zhihu" || label=="zhihu/"){
    element = window.document.getElementById("zhihu");
    element.className="active";
    window.document.getElementById("header-title-h1").innerText="知乎";
    window.document.getElementById("header-title-p").innerText="线上问答平台";
}
if (label=="github" || label=="github/"){
    element = window.document.getElementById("github");
    element.className="active";
    window.document.getElementById("header-title-h1").innerText="github";
    window.document.getElementById("header-title-p").innerText="代码仓库平台";
}
if (label=="bilibili" || label=="bilibili/"){
    element = window.document.getElementById("bilibili");
    element.className="active";
    window.document.getElementById("header-title-h1").innerText="bilibili";
    window.document.getElementById("header-title-p").innerText="线上视频平台";
}
if (label=="weibo" || label=="weibo/"){
    element = window.document.getElementById("weibo");
    element.className="active";
    window.document.getElementById("header-title-h1").innerText="微博";
    window.document.getElementById("header-title-p").innerText="线上博客平台";
}
if (label=="shuiyuan" || label=="shuiyuan/"){
    element = window.document.getElementById("shuiyuan");
    element.className="active";
    window.document.getElementById("header-title-h1").innerText="水源社区";
    window.document.getElementById("header-title-p").innerText="交大的线上聊天平台";
}
if (label=="canvas" || label=="canvas/"){
    element = window.document.getElementById("canvas");
    element.className="active";
    window.document.getElementById("header-title-h1").innerText="Canvas";
    window.document.getElementById("header-title-p").innerText="交大的线上作业平台";
}
if (label=="seiee" || label=="seiee/"){
    element = window.document.getElementById("seiee");
    element.className="active";
    window.document.getElementById("header-title-h1").innerText="电院通知";
    window.document.getElementById("header-title-p").innerText="上海交大电院的信息发布平台";
}
if (label=="dekt" || label=="dekt/"){
    element = window.document.getElementById("dekt");
    element.className="active";
    window.document.getElementById("header-title-h1").innerText="第二课堂";
    window.document.getElementById("header-title-p").innerText="交大第二课堂平台";
}

