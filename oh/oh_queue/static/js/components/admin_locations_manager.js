function AdminLocationsManager({ state }) {
    const { locations } = state;

    return (
        <AdminItemsManager
            itemType="location"
            columns={["ID", "Name", "Zoom Link (optional)", "Online", "Visibility"]}
            items={Object.values(locations).filter(({ name }) => name !== "Online")}
        >
            {item => [
                item.id,
                <AdminItemsTextField itemType="location" placeholder="New Name" propType="name" item={item} />,
                <AdminItemsTextField itemType="location" placeholder="Zoom Link (optional)" propType="link" item={item} />,
                <AdminItemsBooleanField itemType="location" propType="online" item={item} />,
                <AdminItemsBooleanField itemType="location" propType="visible" item={item} onText="Visible" offText="Hidden" />,
            ]}
        </AdminItemsManager>
    );
}
