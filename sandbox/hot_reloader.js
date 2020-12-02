let version = VERSION;

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

async function poller() {
  const latestVersion = await fetch("/latest_revision", {
    method: "POST",
    cache: "no-cache",
  });

  if (!latestVersion.ok) {
    // todo
  } else {
    const data = await latestVersion.json();
    if (data.version !== version) {
      window.location.reload();
    } else if (data.isLoading) {
      document.body.appendChild(elem);
    }
  }
}

setInterval(poller, 700);
