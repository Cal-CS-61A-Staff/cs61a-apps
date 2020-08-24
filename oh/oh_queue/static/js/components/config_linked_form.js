function ConfigLinked({ configKey, configKeys = [], config, render }) {
    const [value, setValue] = React.useState(config[configKey]);
    const [values, setValues] = React.useState(configKeys.map(key => config[key]));
    const submitButtonRef = React.useRef();

    React.useEffect(() => {
        setValue(config[configKey]);
        setValues(configKeys.map(key => config[key]));
    }, configKeys.map(key => config[key]).concat([config[configKey]]));

    const setters = configKeys.map((key, i) => val => console.log(val) || setValues(values => values.slice(0, i).concat([val]).concat(values.slice(i+1))));
    const handlers = setters.map(setter => e => setter(e.target.value));

    const handleSubmit = (e) => {
        if (e.preventDefault) {
            e.preventDefault();
        }
        if (submitButtonRef.current) {
            submitButtonRef.current.classList.add('is-loading');
            submitButtonRef.current.setAttribute('disabled', true);
        }
        const time = Date.now();

        const requestBody = configKey ?
            { key: configKey, value: (e.target ? value : e) } :
            { keys: configKeys, values };

        app.makeRequest(`update_config`, requestBody, (isSuccess) => {
            if (submitButtonRef.current && isSuccess) {
                setTimeout(() => {
                    submitButtonRef.current.classList.remove('is-loading');
                    submitButtonRef.current.removeAttribute('disabled');
                }, 250 - (Date.now() - time));
            }
        });

        return false;
    };

    const submitButton = <button className="btn btn-default" name="btn-submit" type="submit" ref={submitButtonRef}>Save</button>;

    const onChange = e => setValue(e.target.value);

    return render({ onSubmit: handleSubmit, onChange, value, setValue, submitButton, values, setters, handlers });
}
