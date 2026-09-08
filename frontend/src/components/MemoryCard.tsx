export function MemoryCard({ memory }: { memory: any }) { return <div className="row"><span>{memory.content}</span><small>{memory.enabled ? "已启用" : "已停用"}</small></div>; }

