export default async function post(url = "", data = {}) {
  const formData = new URLSearchParams();
  for (const [key, val] of Object.entries(data)) {
    formData.append(key, val);
  }
  const response = await fetch(url, {
    method: "POST",
    mode: "same-origin",
    cache: "no-cache",
    credentials: "same-origin", // include, *same-origin, omit
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    redirect: "manual",
    body: formData,
  });

  if (response.status !== 200) {
    throw new Error(`Error ${response.status}.`);
  }

  return response.json();
}
