let OfflineIndicator = ({offline}) => {
  return (
    <div className={`offline offline-${offline ? 'down' : 'up'}`}>
      <div className="offline-content">
        {offline ?
          'Connection lost. Reconnecting...' :
          'Your computer is connected.'}
      </div>
    </div>
  );
}
