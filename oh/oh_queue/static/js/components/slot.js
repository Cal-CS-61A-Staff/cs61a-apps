function Slot({ children, badgeText, onClick, className = "", link }) {
    if (link) {
        return (
            <a href="#" className={"list-group-item slot-add-button" + className}
               onClick={onClick}>
                {!!badgeText && <span className="badge">{badgeText}</span>}
                {children}
            </a>
        )
    } else {
        return (
            <li className={"list-group-item " + className}>
                {!!badgeText && <span className="badge">{badgeText}</span>}
                {children}
            </li>
        )
    }
}
