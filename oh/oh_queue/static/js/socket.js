function timeoutPromise(ms, promise) {
  return new Promise((resolve, reject) => {
    const timeoutId = setTimeout(() => {
      reject(new Error("promise timeout"));
    }, ms);
    promise.then(
      (res) => {
        clearTimeout(timeoutId);
        resolve(res);
      },
      (err) => {
        clearTimeout(timeoutId);
        reject(err);
      }
    );
  });
}

async function post(endpoint, data, skipTimeout) {
  const promise = fetch(endpoint, {
    method: "POST",
    cache: "no-cache",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(data),
  });
  if (skipTimeout) {
    return promise;
  }
  return timeoutPromise(10000, promise).then((resp) => resp.json());
}

class Socket {
  constructor() {
    setInterval(() => this.emit("connect"), 10000);
    this.handlers = new Map();
    this.emit("connect");
  }

  on(event, handler) {
    if (!this.handlers.has(event)) {
      this.handlers.set(event, []);
    }
    this.handlers.get(event).push(handler);
  }

  trigger(event, args) {
    for (const handler of this.handlers.get(event) || []) {
      handler(args);
    }
  }

  removeAllListeners(eventType) {
    this.handlers.delete(eventType);
  }

  emit(event, params = {}, callback = null) {
    if (callback == null && typeof params === "function") {
      callback = params;
      params = {};
    }
    post(`/api/${event}`, params)
      .then(({ action, updates }) => {
        this.trigger("connect");
        for (const [event, payload] of updates) {
          this.trigger(event, payload);
        }
        if (callback != null) {
          callback(action);
        }
      })
      .catch((e) => {
        console.error(e);
        this.trigger("disconnect");
      });
  }
}
