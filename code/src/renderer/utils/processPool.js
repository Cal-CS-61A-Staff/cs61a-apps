class ProcessPool {
  constructor(factories, buffSize) {
    this.factories = factories;
    this.buffSize = buffSize;

    this.pool = new Map();

    for (const target of Object.keys(factories)) {
      this.refill(target);
    }
  }

  pop = (target) => {
    setInterval(() => this.refill(target));
    return this.pool.get(target).length
      ? this.pool.get(target).shift()
      : this.factories[target];
  };

  refill = (target) => {
    if (!this.pool.has(target)) {
      this.pool.set(target, []);
    }

    while (this.pool.get(target).length <= this.buffSize) {
      // eslint-disable-next-line no-use-before-define
      let handlers = Array(3)
        .fill()
        .map((_, i) => (x) => handlerBuffers[i].push(x));
      const handlerBuffers = handlers.map(() => []);
      const [interactCallback, killCallback, detachCallback] = this.factories[
        target
      ](null, ...handlers.map((_, i) => (x) => handlers[i](x)));
      this.pool.get(target).push((code, ...suppliedHandlers) => {
        interactCallback(code);
        handlers = suppliedHandlers;
        for (let i = 0; i !== handlers.length; ++i) {
          for (const line of handlerBuffers[i]) {
            handlers[i](line);
          }
        }
        return [interactCallback, killCallback, detachCallback];
      });
    }
  };
}

export default ProcessPool;
