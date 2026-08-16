import "./ToolStatus.css";

function ToolStatus({ status }) {
  if (!status) return null;

  return (
    <div className="tool-status">
      {status}
    </div>
  );
}

export default ToolStatus;