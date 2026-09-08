export function ConfirmActionCard({ action, onConfirm }: { action: any; onConfirm: () => void }) { return <div className="action"><span>{action.payload?.title || action.action_type}</span><button onClick={onConfirm}>确认</button></div>; }

