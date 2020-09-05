function AdminItemsBooleanField({ itemType, propType, item, onText="Yes", offText="No" }) {
    const handleChange = (value) => {
        app.makeRequest(`update_${itemType}`, { id: item.id, [propType]: value });
    }

    return <FancyToggle onText={onText} offText={offText} checked={item[propType]} onChange={handleChange} />;
}
