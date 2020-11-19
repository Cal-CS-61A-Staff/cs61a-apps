// @flow
export default async function post(url: string = "", data: {} = {}) {
  const response = await fetch(url, {
    method: "POST",
    mode: "same-origin",
    cache: "no-cache",
    credentials: "same-origin",
    headers: { "Content-Type": "application/json" },
    redirect: "manual",
    body: JSON.stringify(data),
  });

  if (response.status !== 200) {
    throw new Error(`Error ${response.status}.`);
  }

  return response.json();
}
