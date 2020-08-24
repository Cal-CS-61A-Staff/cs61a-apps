function AdminOptionsManager({ children }) {
    return (
        <div className="table-responsive">
            <table className="table table-hover">
                <thead>
                <tr>
                    <th>Option</th>
                    <th className="col-md-3">Value</th>
                </tr>
                </thead>
                <tbody>
                { children }
                </tbody>
            </table>
        </div>
    );
}
