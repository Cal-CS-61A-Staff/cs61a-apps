function AdminItemsTextField({ itemType, placeholder, propType, item }) {
    const editItem = (e) => {
        e.preventDefault();
        const value = e.target.elements[0].value;
        const button = e.target.elements[1];
        $(button).addClass("is-loading");
        app.makeRequest(
            `update_${itemType}`,
            { id: item.id, [propType]: value },
            () => $(button).removeClass("is-loading")
        );
    };

    return (
        <form className="form-inline" onSubmit={editItem}>
            <div className="form-group form-group-sm">
                <div className="input-group">
                    <input className="form-control" type="text"
                           placeholder={placeholder} data-item-id={item.id}
                           defaultValue={item[propType]}/>
                    <span className="input-group-btn">
                        <button className="btn btn-default btn-sm" type="submit">Edit</button>
                    </span>
                </div>
            </div>
            </form>
    )
}
