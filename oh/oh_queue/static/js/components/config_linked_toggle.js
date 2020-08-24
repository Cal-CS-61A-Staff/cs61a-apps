function ConfigLinkedToggle({ config, configKey, offText = "No", onText = "Yes" }) {
    if (!app || Object.keys(config).length === 0) {
        return null;
    }
    return (
        <ConfigLinked configKey={configKey} config={config} render={({ onSubmit, value }) => (
            <FancyToggle
                checked={value === "true" || value === true}
                offText={offText}
                onText={onText}
                onChange={x => onSubmit(x ? "true" : "false")}
            />
        )}/>
    );
}
