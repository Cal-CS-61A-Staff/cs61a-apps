function AppointmentButtons({ ids }) {
  const action = (action) => () => {
    Swal.fire({
      title: "Are you sure?",
      text: "You won't be able to revert this action!",
      icon: "warning",
      showCancelButton: true,
      confirmButtonColor: "#3085d6",
      cancelButtonColor: "#d33",
      confirmButtonText: "Yes, do it!",
    }).then((result) => {
      if (result.value) {
        app.makeRequest("bulk_appointment_action", { action, ids }, () => {
          Swal.fire("Success!", "Your action has been performed.", "success");
        });
      }
    });
  };

  const { Link } = ReactRouterDOM;

  return (
    <div className="appointment-buttons">
      {ids == null && (
        <Link className="btn btn-success" to="/admin/appointments">
          Add Appointments
        </Link>
      )}
      <button className="btn btn-warning" onClick={action("open_all_assigned")}>
        Activate all assigned appointments
      </button>
      <button className="btn btn-primary" onClick={action("resolve_all_past")}>
        Resolve all past appointments
      </button>
      <button
        className="btn btn-danger"
        onClick={action("remove_all_unassigned")}
      >
        Delete all unassigned appointments
      </button>
      <button
        className="btn btn-info"
        onClick={action("resend_reminder_emails")}
      >
        Resend reminder emails
      </button>
    </div>
  );
}
