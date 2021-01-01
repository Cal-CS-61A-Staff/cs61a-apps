console.info("Hot reloader enabled...");

const elem = document.createElement("div");
elem.innerText = "Rebuilding...";
elem.style.position = "fixed";
elem.style.width = "250px";
elem.style.height = "65px";
elem.style.background = "blue";
elem.style.color = "white";
elem.style.top = "0";
elem.style.left = "calc(50% - 125px)";
elem.style.zIndex = "99999";
elem.style.lineHeight = "65px";
elem.style.textAlign = "center";
elem.style.fontFamily = '"Inconsolata", monospace';
elem.style.fontSize = "18pt";
elem.style.borderRadius = "0 0 30px 30px";

let rebuilding = false;
let path = window.location.pathname.slice(1);
if (path.indexOf(".") === -1) {
  if (path.length > 0) {
    path += "/index.html";
  } else {
    path += "index.html";
  }
}

async function poller() {
  let latestVersion;
  try {
    latestVersion = await fetch("/get_revision", {
      method: "POST",
      cache: "no-cache",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ path }),
    });
  } catch {
    latestVersion = { ok: false };
  }
  let data = null;
  if (latestVersion.ok) {
    data = await latestVersion.json();
  }
  if (data == null || data.manualVersion !== manualVersion) {
    // a manual make invocation has taken place
    // disable auto-reload
    document.body.appendChild(elem);
    elem.style.background = "red";
    elem.innerText = "Refresh to update";
    clearInterval(interval);
    return;
  }
  if (data.pubVersion !== data.srcVersion) {
    document.body.appendChild(elem);
    if (!rebuilding) {
      const resp = await fetch("/rebuild_path", {
        method: "POST",
        cache: "no-cache",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ path }),
      });
      if (resp.ok) {
        rebuilding = true;
      }
    }
  }
  if (data.pubVersion !== version) {
    window.location.reload();
  }
}

const interval = setInterval(poller, 700);
