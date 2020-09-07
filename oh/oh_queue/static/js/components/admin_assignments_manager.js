function AdminAssignmentsManager({ state }) {
    const {assignments} = state;

    return (
        <AdminItemsManager
            itemType="assignment"
            columns={["ID", "Name", "Visibility"]}
            items={Object.values(assignments)}
        >
            {item => [
                item.id,
                <AdminItemsTextField itemType="assignment" placeholder="New Name" propType="name" item={item} />,
                <AdminItemsBooleanField itemType="assignment" propType="visible" item={item} onText="Visible" offText="Hidden" />,
            ]}
        </AdminItemsManager>
    );
}
