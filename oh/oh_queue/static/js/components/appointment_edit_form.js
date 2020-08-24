function AppointmentEditForm({ isOpen, appointment, onSubmit }) {
    const root = React.useRef();

    const [description, setDescription] = React.useState("");

    React.useEffect(() => {
        setDescription(appointment.description);
    }, [isOpen, appointment]);

    React.useEffect(() => {
        if (isOpen) {
            $(root.current).modal("show");
        } else {
            $(root.current).modal("hide");
        }
    }, [isOpen]);

    const handleSubmit = () => {
        app.makeRequest("update_appointment", {
            id: appointment.id,
            description,
        });
        onSubmit();
    };

    return ReactDOM.createPortal(
        <div className="modal fade" ref={root} tabIndex="-1" role="dialog">
            <div className="modal-dialog" role="document">
                <div className="modal-content">
                    <div className="modal-header">
                        <button type="button" className="close" data-dismiss="modal"
                                aria-label="Close"><span aria-hidden="true">&times;</span></button>
                        <h4 className="modal-title">
                            Edit Appointment
                        </h4>
                    </div>
                    <div className="modal-body">
                        <input className="form-control form-right" type="text"
                               name="question" title="Question" placeholder="Description (keep it short!)"
                               value={description} onChange={e => setDescription(e.target.value)}
                               required/>
                    </div>
                    <div className="modal-footer">
                        <button type="button" className="btn btn-default"
                                data-dismiss="modal">Close
                        </button>
                        <button
                            type="button"
                            className="btn btn-primary"
                            onClick={handleSubmit}
                        >Update
                        </button>
                    </div>
                </div>
            </div>
        </div>,
        document.body,
    );
}
