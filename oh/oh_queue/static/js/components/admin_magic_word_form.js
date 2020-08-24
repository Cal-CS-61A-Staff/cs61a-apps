function AdminMagicWordForm({ config }) {
    const [key, setKey] = React.useState(0);

    React.useEffect(() => {
        if (!config["queue_magic_word_data"]) {
            app.makeRequest('refresh_magic_word', (res) => {
                if (res.magic_word) {
                    config["queue_magic_word_data"] = res.magic_word;
                    setKey(key + 1);
                }
            });
        }
    }, [config, config["queue_magic_word_data"]]);

    return (
        <ConfigLinked
            configKeys={['queue_magic_word_mode', 'queue_magic_word_data']}
            config={config}
            render={({
                         onSubmit,
                         values: [mode, data],
                         handlers: [onModeChange, onDataChange],
                         setters: [, setData],
                         submitButton
                     }) => (
                <InnerAdminMagicWordForm
                    mode={mode}
                    data={data}
                    onModeChange={onModeChange}
                    onDataChange={onDataChange}
                    setData={setData}
                    submitButton={submitButton}
                    onSubmit={onSubmit}
                />
            )}
        />
    )
}

function InnerAdminMagicWordForm({ mode, data, onModeChange, onDataChange, setData, submitButton, onSubmit }) {
    const handleModeChange = (e) => {
        onModeChange(e);
        if (e.target.value === "text") {
            setData("");
        }
    };
    const queueMagicWordOptions = [
        <div className="form-group">
            <select
                className="form-control"
                value={mode}
                onChange={handleModeChange}
            >
                <option value="none">None</option>
                <option value="text">Text</option>
                <option value="timed_numeric">Time-based Numeric</option>
            </select>
        </div>
    ];
    if (mode === 'text') {
        queueMagicWordOptions.push(
            <div className="form-group">
                <input type="text" className="form-control"
                       value={data}
                       onChange={onDataChange}
                       required="required"/>
            </div>
        );
    }
    return (
        <form onSubmit={onSubmit}>
            {queueMagicWordOptions}
            {submitButton}
        </form>
    )
}
