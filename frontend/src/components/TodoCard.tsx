export function TodoCard({ todo }: { todo: any }) { return <div className="row"><span>{todo.title}</span><small>{todo.remind_at ? new Date(todo.remind_at).toLocaleString() : "未设提醒"}</small></div>; }

