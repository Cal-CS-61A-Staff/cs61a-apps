function FancyToggle({ checked, onChange, offText, onText }) {
    const [initialized, setInitialized] = React.useState(false);
    const toggleRef = React.useRef();

    const initializeToggle = (toggle) => {
        if (!toggle || initialized) return;
        $(toggle).bootstrapToggle();
        $(toggle).change(() => handleClick(toggle));
        setInitialized(true);
        toggleRef.current = toggle;
    };

    const handleClick = (toggle) => {
        onChange(toggle.checked);
    };

    React.useEffect(() => {
        if (toggleRef.current) {
            $(toggleRef.current).off("change");
            $(toggleRef.current).bootstrapToggle(checked ? "on" : "off");
            $(toggleRef.current).change(() => handleClick(toggleRef.current));
        }
    }, [toggleRef.current, checked]);

    return (
        <input
            ref={initializeToggle}
            type="checkbox"
            defaultChecked={checked}
            data-off={offText}
            data-on={onText}
            data-size="mini"
            data-toggle="toggle"
            onClick={handleClick}
        />
    )
}
