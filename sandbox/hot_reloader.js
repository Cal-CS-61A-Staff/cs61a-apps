let version = VERSION;

console.info("Hot reloader enabled...");

async function poller() {
  const latestVersion = await fetch("/latest_revision", {
    method: "POST",
    cache: "no-cache",
  });

  if (!latestVersion.ok) {
    // todo
  } else if ((await latestVersion.json()) !== version) {
    window.location.reload();
  }
}

setInterval(poller, 1500);
