function ConfigLinkedText({
  config,
  configKey,
  lines = 1,
  placeholder,
  title,
  optional,
}) {
  const Input = lines > 1 ? "textarea" : "input";
  return (
    <ConfigLinked
      configKey={configKey}
      config={config}
      render={({ onSubmit, onChange, value, submitButton }) => (
        <form onSubmit={onSubmit}>
          <div className="form-group">
            {title && <label>{title}</label>}
            <Input
              type="text"
              className="form-control"
              required={optional ? undefined : "required"}
              value={value}
              onChange={onChange}
              placeholder={placeholder}
              rows={lines}
            />
          </div>
          {submitButton}
        </form>
      )}
    />
  );
}
