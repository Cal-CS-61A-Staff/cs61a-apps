function ConfigLinkedMarkdownInput({ title, placeholder, config, configKey }) {
    return (
        <ConfigLinked
            configKey={configKey}
            config={config}
            render={({ onSubmit, onChange, value, submitButton }) => (
                <form onSubmit={onSubmit}>
                    <div className="form-group">
                        <label htmlFor="welcome-input">{title} (supports Markdown)</label>
                        <textarea className="form-control" name="ticket-input"
                                  placeholder={placeholder}
                                  value={value}
                                  onChange={onChange}/>
                    </div>
                    <label>{title} Preview:</label>
                    <div className="alert alert-info alert-dismissable fade in"
                         role="alert">
                        <button type="button" className="close" aria-label="Close"
                                data-dismiss="alert">
                            <span aria-hidden="true">&times;</span>
                        </button>
                        <ReactMarkdown source={value}/>
                    </div>
                    <div className="form-group">
                        <div>
                            {submitButton}
                        </div>
                    </div>
                </form>
            )}
        />
    )
}
