function ConfigLinkedText({ config, configKey }) {
  return (
    <ConfigLinked
      configKey={configKey}
      config={config}
      render={({ onSubmit, onChange, value, submitButton }) => (
        <form onSubmit={onSubmit}>
          <div className="form-group">
            <input
              type="text"
              className="form-control"
              required="required"
              value={value}
              onChange={onChange}
            />
          </div>
          {submitButton}
        </form>
      )}
    />
  );
}
