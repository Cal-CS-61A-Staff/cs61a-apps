function AdminItemsManager({ children, columns, itemType, items }) {
    const [input, setInput] = React.useState("");
    const [isLoading, setIsLoading] = React.useState(false);

    const isValidInput = input ? !items.map(item => item.name).includes(input) : null;

    const onChange = (input) => {
        setInput(input);
    };

    const addItemInput = () => {
        if (!isValidInput) {
            return;
        }

        setIsLoading(true);

        app.makeRequest(`add_${itemType}`, { name: input }, success => {
            setIsLoading(false);
            if (success) {
                setInput("");
            }
        })
    }

    const formGroupClassNames = classNames({
        'form-group': true,
        'has-error': isValidInput === false,
        'has-success': isValidInput === true
    });


    return (
        <div className="table-responsive">
            <table className="table table-hover">
                <thead>
                <tr>
                    {columns.map(column => <th key={column}><span>{column}</span></th>)}
                </tr>
                </thead>
                <tbody>
                {items.map((item) =>
                    <tr key={item.id}>
                        {children(item).map((child, i) => <td key={i}>{child}</td>)}
                    </tr>
                )}
                </tbody>
            </table>
            <table className="table table-hover">
                <tbody>
                    <tr key="new">
                        <td>
                            <div className={formGroupClassNames}>
                                <input className={`form-control`} type="text"
                                       minLength="1" placeholder="Add new entry" disabled={isLoading}
                                       value={input}
                                       onChange={e => onChange(e.target.value)}
                                />
                            </div>
                        </td>
                        <td className="col-md-1">
                            <button type="button" className="btn btn-default"
                                    disabled={!isValidInput || isLoading}
                                    onClick={addItemInput}>
                                {isLoading ? <div className="spinner-loading"/> : "Add"}
                            </button>
                        </td>
                    </tr>
                </tbody>
            </table>
        </div>
    );
}
